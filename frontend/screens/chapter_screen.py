"""Dedicated NCERT Chapter Detail Hub with New-Tab PDF Viewer, Download, Mastery Analytics, and Quiz History (Phases 1-4)."""

import logging
import os

import streamlit as st

from frontend.components.cards import render_metric_card
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level, navigate_to
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.curriculum.service import get_chapter_pdf
from src.academic_rag.storage.repository import quiz_repository

logger = logging.getLogger(__name__)


def render_chapter_screen(
    student_id: str = "student_001",
    user_api_key: str = "",
    selected_model: str = "gemini-3.5-flash-lite",
) -> None:
    """Renders the comprehensive Chapter Detail Hub for a selected NCERT chapter."""
    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("chapter")

    class_level = get_student_class_level()

    # 1. Retrieve & Resolve Chapter Metadata (Phase 1)
    active_info = st.session_state.get("active_chapter_detail")
    target_ident = (
        active_info.get("chapter") if isinstance(active_info, dict) else (active_info or 1)
    )

    pdf_info = get_chapter_pdf(class_level, target_ident)
    ch_num = pdf_info["chapter_number"]
    ch_title = pdf_info["chapter_name"]
    filename = pdf_info["filename"]
    pdf_path = pdf_info["pdf_path"]
    file_exists = pdf_info["exists"]

    st.write("")
    st.markdown(f"### Chapter {ch_num}: {ch_title}")

    # 2. Action Buttons (Phases 2, 3, 4)
    st.markdown("#### Actions")
    col1, col2, col3, col4 = st.columns(4)

    # Prepare PDF Data for New Tab Link & Download
    pdf_bytes = b""
    if file_exists and os.path.isfile(pdf_path):
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
        except Exception as e:
            logger.error(f"Failed to read PDF file {pdf_path}: {e}")

    static_url = pdf_info.get("static_url", f"app/static/class{class_level}/{filename}")

    with col1:
        # Phase 2 & 4: Genuine browser hyperlink opening PDF in new tab via Streamlit static serving
        if file_exists:
            st.link_button(
                "Open in New Tab",
                url=static_url,
                type="primary",
                icon=":material/open_in_new:",
                use_container_width=True,
                help=f"Open {filename} in a new browser tab",
            )
        else:
            st.button(
                "PDF Unavailable",
                disabled=True,
                use_container_width=True,
                key="ch_newtab_btn_disabled",
            )

    with col2:
        # Phase 3: Download PDF Secondary Action
        if pdf_bytes:
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                icon=":material/download:",
                use_container_width=True,
                key=f"ch_screen_download_btn_{ch_num}",
            )
        else:
            st.button(
                "Download", disabled=True, use_container_width=True, key="ch_down_btn_disabled"
            )

    with col3:
        if st.button(
            "Ask a Doubt",
            icon=":material/chat:",
            key=f"ch_screen_doubt_btn_{ch_num}",
            use_container_width=True,
            help="Ask questions about this chapter in NCERT Tutor",
        ):
            st.session_state.active_prompt = f"Explain the key concepts, laws, and important formulas of Chapter {ch_num}: {ch_title} in NCERT Class {class_level} Science."
            navigate_to("tutor")
            st.rerun()

    with col4:
        if st.button(
            "Practice Quiz",
            type="primary",
            icon=":material/quiz:",
            key=f"ch_screen_practice_btn_{ch_num}",
            use_container_width=True,
            help="Take a practice quiz on this chapter",
        ):
            st.session_state.selected_chapter = ch_title
            navigate_to("quiz")
            st.rerun()

    st.write("")
    st.write("")

    # 3. Chapter Performance & Mastery Analytics (Phase 4)
    st.markdown("#### Performance Mastery")

    swat = get_student_swat(student_id, class_level=class_level)
    breakdown = swat.get("chapter_breakdown", {})
    ch_stats = breakdown.get(ch_title)

    if ch_stats and ch_stats.get("status") != "unattempted":
        score = ch_stats.get("score", 0)
        attempts = ch_stats.get("attempts", 1)
        accuracy = ch_stats.get("accuracy", score)
        status = ch_stats.get("status", "average")
        recent = ch_stats.get("recent_performance") or f"{score}%"

        if status == "strong":
            badge_color = "var(--md-primary)"
            badge_label = "STRONG TOPIC"
            badge_desc = (
                "Excellent mastery demonstrated! Keep up the performance with periodic review."
            )
        elif status == "weak":
            badge_color = "var(--md-error)"
            badge_label = "HIGH PRIORITY / WEAK"
            badge_desc = "Performance is below target. Recommended to review NCERT notes and take a practice quiz."
        else:
            badge_color = "var(--md-amber)"
            badge_label = "AVERAGE / IN PROGRESS"
            badge_desc = (
                "Moderate mastery demonstrated. Continue practicing to reach strong classification."
            )

        st.markdown(
            f"""
            <div style="background: var(--surface-container); border-radius: 10px; padding: 14px 18px; margin-bottom: 16px; border-left: 5px solid {badge_color};">
                <div style="font-weight: 700; font-size: 0.9rem; color: {badge_color}; margin-bottom: 4px;">{badge_label}</div>
                <div style="font-size: 0.86rem; color: var(--on-surface);">{badge_desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card("Average Score", f"{score}%")
        with m2:
            render_metric_card("Accuracy", f"{accuracy}%")
        with m3:
            render_metric_card("Quiz Attempts", attempts)
        with m4:
            render_metric_card("Progression", recent)

    else:
        st.markdown(
            """
            <div style="background: var(--surface-container-low); border: 1px solid var(--outline-variant); border-radius: 10px; padding: 18px; text-align: center; margin-bottom: 16px;">
                <div style="font-size: 1.05rem; font-weight: 600; color: var(--on-surface); margin-bottom: 4px;">Not Attempted Yet</div>
                <div style="font-size: 0.86rem; color: var(--on-surface-variant); max-width: 500px; margin: 0 auto;">
                    You haven't taken a practice quiz for this chapter yet. Click <strong>Practice Quiz</strong> above to establish your baseline score.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # 4. Quiz History for this Chapter (Phase 4)
    st.markdown("#### Quiz History")
    all_history = quiz_repository.get_student_class_history(student_id, class_level)
    ch_history = [h for h in all_history if h.get("chapter") == ch_title]

    if ch_history:
        # Show chronological quiz attempts
        for idx, attempt in enumerate(ch_history, 1):
            ts = attempt.get("timestamp", "")
            if ts and len(ts) >= 16:
                ts_display = ts[:10] + " " + ts[11:16]
            else:
                ts_display = ts or "Recent"

            diff = str(attempt.get("difficulty", "medium")).capitalize()
            score_val = attempt.get("score", 0)
            total_val = attempt.get("total_questions", 0)
            pct = attempt.get("percentage", 0)

            pct_color = (
                "var(--md-primary)"
                if pct >= 70
                else ("var(--md-amber)" if pct >= 50 else "var(--md-error)")
            )

            st.markdown(
                f"""
                <div style="background: var(--surface-container-low); border: 1px solid var(--outline-variant); border-radius: 8px; padding: 10px 16px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-weight: 700; font-size: 0.88rem; color: var(--on-surface);">Quiz {idx}</span>
                        <span style="font-size: 0.82rem; color: var(--on-surface-variant);">{ts_display}</span>
                        <span style="font-size: 0.78rem; background: var(--surface-container-high); padding: 2px 8px; border-radius: 4px; color: var(--on-surface-variant); font-weight: 600;">{diff}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 0.86rem; color: var(--on-surface); font-weight: 600;">{score_val} / {total_val} correct</span>
                        <span style="font-weight: 700; font-size: 0.92rem; color: {pct_color}; min-width: 45px; text-align: right;">{pct:.0f}%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No quiz attempts recorded yet for this chapter.")
