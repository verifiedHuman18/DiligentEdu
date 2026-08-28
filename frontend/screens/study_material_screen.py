"""My Study Material Screen (Phases 1-3, 8-9, 20-23).

Allows students to upload, manage, and inspect their personal reference books and notes
with student and class isolation, local vector embeddings, and real-time status tracking.
"""

import logging
import textwrap
from typing import Optional

import streamlit as st

from backend.curriculum.service import get_ncert_curriculum
from backend.storage.repository import (
    get_student_study_materials,
)
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level

logger = logging.getLogger(__name__)


def _format_file_size(size_bytes: int) -> str:
    """Formats raw bytes into a readable string (KB / MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def render_study_material_screen(
    student_id: str = "student_001",
    user_api_key: Optional[str] = None,
) -> None:
    """Renders the My Study Material screen with upload and management capabilities."""
    render_back_to_home("study_material")

    from frontend.state import get_student_subject

    class_level = get_student_class_level()
    subject = get_student_subject()

    st.write("")
    header_html = textwrap.dedent(f"""\
<div class="section-header-bar">
    <div>
        <h3 style="margin:0; font-size: 1.45rem; font-weight: 700; color: var(--on-surface);">
            📚 My Study Material — Class {class_level} · {subject}
        </h3>
        <div class="section-subtitle-text">
            Upload and manage reference books, notes, and study material. Automatically indexed with local embeddings for your Tutor and Practice Quizzes.
        </div>
    </div>
</div>
""")
    st.markdown(header_html, unsafe_allow_html=True)
    st.write("")

    # Two column layout: Upload Form (Left) | Guidelines (Right)
    col_upload, col_guide = st.columns([3, 2])

    with col_upload:
        st.markdown("#### Upload New Material")
        uploaded_file = st.file_uploader(
            "Choose a PDF file (.pdf only, max 25 MB)",
            type=["pdf"],
            key="study_mat_file_uploader",
            help="Upload textbooks, reference guides, or classroom notes in standard PDF format.",
        )

        mat_name_default = ""
        if uploaded_file is not None:
            clean_default = uploaded_file.name.replace(".pdf", "").replace("_", " ").title()
            mat_name_default = clean_default

        c_name, c_subj = st.columns([2, 1])
        with c_name:
            material_title = st.text_input(
                "Material Title / Name",
                value=mat_name_default,
                placeholder=f"e.g. {subject} Reference Book, Important Notes",
                key="study_mat_title_input",
            )
        with c_subj:
            st.text_input(
                "Subject",
                value=subject,
                disabled=True,
                key="study_mat_subject_display",
            )

        # Chapter mapping (Optional)
        curriculum_chapters = get_ncert_curriculum(class_level, subject=subject)
        ch_options = ["All Chapters / General Reference"] + [
            f"Ch {ch['chapter_number']}: {ch['chapter']}" for ch in curriculum_chapters
        ]
        selected_ch_opt = st.selectbox(
            "Curriculum Chapter (Optional)",
            options=ch_options,
            index=0,
            key="study_mat_chapter_select",
            help="Tag this material to a specific chapter, or leave as General Reference to make it available across all topics.",
        )

        selected_chapter = None
        if selected_ch_opt != "All Chapters / General Reference":
            # Extract chapter title
            if ":" in selected_ch_opt:
                selected_chapter = selected_ch_opt.split(":", 1)[1].strip()

        st.caption(
            f"🔒 Bound automatically to your active profile: **Class {class_level} ({subject})**."
        )

        if st.button(
            "Upload & Index Material",
            type="primary",
            icon=":material/upload:",
            disabled=(uploaded_file is None),
            key="btn_start_material_upload",
            use_container_width=True,
        ):
            if uploaded_file is None:
                st.error("Please select a PDF file to upload.")
            else:
                with st.spinner(
                    "Validating, extracting pages, and generating local vector embeddings (0 Gemini tokens consumed)..."
                ):
                    try:
                        from backend import upload_study_material

                        file_bytes = uploaded_file.getvalue()
                        res = upload_study_material(
                            student_id=student_id,
                            file_data=file_bytes,
                            filename=uploaded_file.name,
                            material_name=material_title.strip() or mat_name_default,
                            class_level=class_level,
                            subject=subject,
                            chapter=selected_chapter,
                        )
                        st.success(
                            f"Successfully uploaded and indexed **{res['material_name']}** ({res['page_count']} pages, {res['chunk_count']} chunks)!"
                        )
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Material upload failed: {e}")
                        st.error(f"Upload failed: {e}")

    with col_guide:
        guide_html = textwrap.dedent(f"""\
<div style="background: var(--surface-container); border-radius: 12px; padding: 18px; border-left: 4px solid var(--md-primary); margin-top: 10px;">
    <div style="font-weight: 700; font-size: 0.95rem; color: var(--on-surface); margin-bottom: 8px;">
        🛡️ Privacy & Ingestion Architecture
    </div>
    <div style="font-size: 0.83rem; color: var(--on-surface-variant); line-height: 1.6;">
        <ul style="padding-left: 18px; margin: 0;">
            <li><strong>Strict Multi-Tenant Isolation:</strong> Your uploads are visible only to you (<code>{student_id}</code>) and strictly filtered to <strong>Class {class_level}</strong>.</li>
            <li><strong>Authoritative Hierarchy:</strong> NCERT remains the official curriculum baseline. Your uploaded books provide supplementary examples and derivations.</li>
            <li><strong>Zero AI Cost:</strong> Ingestion and embedding are processed locally (0 Gemini tokens).</li>
            <li><strong>Readable Text PDFs:</strong> Scanned image-only PDFs without a text layer are rejected to prevent blank indexing.</li>
        </ul>
    </div>
</div>
""")
        st.markdown(guide_html, unsafe_allow_html=True)

    st.write("")
    st.markdown("---")
    st.write("")

    # Section 2: Uploaded Material Inventory
    st.markdown("#### My Uploaded Material Inventory")
    materials = get_student_study_materials(
        student_id=student_id, class_level=class_level, subject=subject
    )

    if not materials:
        empty_html = textwrap.dedent("""\
<div style="background: var(--surface-container-low); border: 1px dashed var(--outline-variant); border-radius: 12px; padding: 32px; text-align: center; margin: 12px 0;">
    <div style="font-size: 1.1rem; font-weight: 700; color: var(--on-surface); margin-bottom: 6px;">No Material Uploaded Yet</div>
    <div style="font-size: 0.88rem; color: var(--on-surface-variant); max-width: 480px; margin: 0 auto 16px auto;">
        Upload reference books or revision notes above. Once uploaded, your NCERT Tutor and Practice Quizzes will automatically reference your personal materials.
    </div>
</div>
""")
        st.markdown(empty_html, unsafe_allow_html=True)
    else:
        for idx, doc in enumerate(materials):
            doc_id = doc["document_id"]
            status = doc.get("status", "PROCESSING")
            title = doc.get("material_name") or doc.get("filename")
            filename = doc.get("filename")
            pages = doc.get("page_count", 0)
            chunks = doc.get("chunk_count", 0)
            size_str = _format_file_size(doc.get("file_size_bytes", 0))
            uploaded_at = doc.get("uploaded_at", "")[:10]
            ch_tag = doc.get("chapter") or "All Chapters"
            doc_subj = doc.get("subject") or subject

            # Status Badge Styling
            if status == "READY":
                status_chip = '<span style="background: #1b5e20; color: #e8f5e9; font-size: 0.76rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">✓ READY</span>'
            elif status == "PROCESSING":
                status_chip = '<span style="background: #0d47a1; color: #e3f2fd; font-size: 0.76rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">⏳ PROCESSING</span>'
            else:
                status_chip = '<span style="background: #b71c1c; color: #ffebee; font-size: 0.76rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">✗ FAILED</span>'

            card_col, action_col = st.columns([4.2, 1.0])

            with card_col:
                card_html = textwrap.dedent(f"""\
<div style="background: var(--surface-container); border-radius: 10px; padding: 14px 16px; margin-bottom: 8px; border: 1px solid var(--outline-variant);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <div style="font-size: 1.02rem; font-weight: 700; color: var(--on-surface);">{title}</div>
        <div>{status_chip}</div>
    </div>
    <div style="font-size: 0.82rem; color: var(--on-surface-variant); margin-bottom: 6px;">
        <code>{filename}</code> &nbsp;·&nbsp; {size_str} &nbsp;·&nbsp; Uploaded: {uploaded_at}
    </div>
    <div style="font-size: 0.82rem; color: var(--md-primary); font-weight: 600;">
        Class {class_level} {doc_subj} &nbsp;·&nbsp; Scope: {ch_tag} &nbsp;·&nbsp; {pages} Pages ({chunks} Chunks)
    </div>
</div>
""")
                st.markdown(card_html, unsafe_allow_html=True)

            with action_col:
                st.write("")
                btn_del_key = f"btn_del_doc_{doc_id}_{idx}"
                if st.button(
                    "Delete",
                    key=btn_del_key,
                    icon=":material/delete:",
                    type="secondary",
                    help=f"Permanently delete {title} and its vector embeddings",
                    use_container_width=True,
                ):
                    from backend import delete_study_material

                    try:
                        delete_study_material(document_id=doc_id, student_id=student_id)
                        st.toast(f"Deleted {title}")
                        st.rerun()
                    except Exception as del_err:
                        st.error(f"Failed to delete: {del_err}")
