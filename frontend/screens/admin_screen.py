"""Class Admin Dashboard for DiligentEdu (Phases 1-21 Scoped Architecture)."""

import streamlit as st

from backend.admin.service import admin_service
from backend.analytics.admin import (
    get_class_chapter_performance,
    get_class_overview,
)
from backend.exceptions import (
    PermissionDeniedError,
    StudentValidationError,
)
from frontend.components.cards import render_metric_card
from frontend.state import get_student_class_level


def render_admin_screen(selected_class: str = "Class 10") -> None:
    """Renders the Class Admin dashboard with strictly scoped student management, creation, deletion, and analytics."""
    cls_int = get_student_class_level()
    admin_id = st.session_state.get("admin_id")

    # If admin_id is not yet in session state, resolve fallback for testing/dev
    if not admin_id:
        try:
            from backend.storage.repository import get_prisma_client

            db = get_prisma_client()
            admin_user = db.user.find_first(where={"role": "admin", "class_level": cls_int})
            if admin_user:
                admin_id = admin_user.id
                st.session_state.admin_id = admin_id
        except Exception:
            pass

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
            <span class="material-symbols-outlined" style="font-size: 2.2rem; color: var(--md-amber);">admin_panel_settings</span>
            <h2 style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.9rem; margin: 0; color: var(--text-primary);">
                Class {cls_int} Administrator Dashboard
            </h2>
        </div>
        <div style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 1.5rem;">
            Class-wide academic diagnostics, curriculum health telemetry, and scoped student management.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Class Overview Metrics
    overview = get_class_overview(cls_int)

    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Aggregate Class Health</h4>
                <div class="section-subtitle-text">Real-time performance averages across all students in Class.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(
            "Enrolled Students",
            f"{overview['active_students']} / {overview['total_students']}",
            delta=f"{overview['active_students']} active with quiz data",
        )
    with m2:
        render_metric_card(
            "Class Average",
            f"{overview['class_average']}%",
            delta="Across all completed quizzes",
        )
    with m3:
        render_metric_card(
            "Class Accuracy",
            f"{overview['class_accuracy']}%",
            delta=f"{overview['total_questions_correct']} / {overview['total_questions_attempted']} correct answers",
        )
    with m4:
        render_metric_card(
            "Total Quizzes Taken",
            str(overview["total_quizzes"]),
            delta="Class-wide submission count",
        )

    st.write("")
    st.write("")

    # 2. Student Management & Roster (Phases 8-16)
    st.markdown(
        f"""
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Student Management (Class {cls_int})</h4>
                <div class="section-subtitle-text">Manage enrolled Class {cls_int} students, add new students, and perform promotion.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add Student Form (Phase 9 & 10: NO class dropdown - strictly inherited from admin)
    with st.expander(
        f"➕ Add New Class {cls_int} Student",
        expanded=st.session_state.get("show_add_student", False),
    ):
        with st.form("create_student_form", border=False):
            st.markdown(f"**Register Student into Class {cls_int}**")
            f_col1, f_col2, f_col3 = st.columns([1.2, 1.4, 1.4])
            with f_col1:
                new_name = st.text_input(
                    "Full Name *", placeholder="e.g. Aarav Sharma", key="new_st_name"
                )
            with f_col2:
                new_email = st.text_input(
                    "Roll No. / Email *",
                    placeholder="e.g. IIT2025001 or aarav@school.edu",
                    key="new_st_email",
                )
            with f_col3:
                new_password = st.text_input(
                    "Password (Optional)",
                    placeholder="Default: Student@123",
                    key="new_st_password",
                    type="password",
                    help="Leave blank to use default Student@123",
                )

            submit_create = st.form_submit_button(
                f"Create Class {cls_int} Student", type="primary", use_container_width=True
            )

        if submit_create:
            if not admin_id:
                st.error("Admin identity could not be verified. Please re-authenticate.")
            else:
                try:
                    res = admin_service.create_student(
                        admin_id=admin_id,
                        student_data={
                            "name": new_name,
                            "email": new_email,
                            "password": new_password,
                        },
                    )
                    st.success(
                        f"Successfully registered {res['name']} in Class {cls_int} ({res['email']})!"
                    )
                    st.session_state.show_add_student = False
                    st.rerun()
                except (PermissionDeniedError, StudentValidationError) as e:
                    st.error(str(e))
                except Exception:
                    st.error("An unexpected error occurred while creating student.")

    # Scoped Student Listing (Phase 14: Server-side scoped)
    if admin_id:
        try:
            students = admin_service.get_students_for_admin(admin_id)
        except Exception:
            from backend.analytics.admin import get_class_students

            students = get_class_students(cls_int)
    else:
        from backend.analytics.admin import get_class_students

        students = get_class_students(cls_int)

    if not students:
        st.info(
            f"No students currently registered in Class {cls_int}. Use the form above to add a student."
        )
    else:
        # Section Subtitle
        st.markdown(
            """
            <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); font-family: 'Outfit', sans-serif; margin-bottom: 12px;">
                Student Details
            </div>
            """,
            unsafe_allow_html=True,
        )

        for idx, s in enumerate(students):
            st_name = s.get("name") or "Student"
            st_email = s.get("email") or "N/A"
            s_class = s.get("class_level", cls_int)
            s_id = s.get("id")

            with st.container():
                c1, c2, c3 = st.columns([3.5, 1.5, 3.2], vertical_alignment="center")
                with c1:
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
                            <div style="width: 34px; height: 34px; border-radius: 50%; background: var(--surface-container-highest); display: flex; align-items: center; justify-content: center; font-weight: 700; color: var(--md-amber); font-size: 0.85rem;">
                                {st_name[0].upper() if st_name else "S"}
                            </div>
                            <div>
                                <div style="font-weight: 600; color: var(--text-primary);">{st_name}</div>
                                <div style="color: var(--text-muted); font-size: 0.8rem;">{st_email}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"""
                        <div>
                            <span style="background: var(--surface-container-highest); color: var(--text-primary); padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; border: 1px solid var(--border-outline-variant);">
                                Class {s_class}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c3:
                    # Action buttons: Promote (if Class 9) + Delete with confirmation (Phases 6, 11, 16)
                    col_act1, col_act2 = st.columns([1.2, 1.8], vertical_alignment="center")

                    # 1. Promote Button (Class 9 only)
                    with col_act1:
                        if s_class == 9:
                            if st.button(
                                "Promote to 10", key=f"promote_{s_id}_{idx}", type="primary"
                            ):
                                try:
                                    admin_service.promote_student(
                                        admin_id=admin_id, student_id=s_id
                                    )
                                    st.success(f"Promoted {st_name} to Class 10!")
                                    st.rerun()
                                except PermissionDeniedError as pe:
                                    st.error(str(pe))
                                except Exception:
                                    st.error("Failed to promote student.")
                        else:
                            st.markdown(
                                """
                                <div style="color: var(--md-tertiary); font-size: 0.8rem; font-weight: 600;">
                                    Senior
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    # 2. Delete Button with Confirmation (Phase 11)
                    with col_act2:
                        pending_delete_key = f"pending_delete_{s_id}"
                        is_pending = st.session_state.get(pending_delete_key, False)

                        if not is_pending:
                            if st.button("Delete", key=f"btn_del_{s_id}_{idx}", type="secondary"):
                                st.session_state[pending_delete_key] = True
                                st.rerun()
                        else:
                            c_cancel, c_confirm = st.columns([1, 1], vertical_alignment="center")
                            with c_cancel:
                                if st.button("Cancel", key=f"btn_cancel_del_{s_id}_{idx}"):
                                    st.session_state[pending_delete_key] = False
                                    st.rerun()
                            with c_confirm:
                                if st.button(
                                    "Confirm", key=f"btn_confirm_del_{s_id}_{idx}", type="primary"
                                ):
                                    try:
                                        admin_service.delete_student(
                                            admin_id=admin_id, student_id=s_id
                                        )
                                        st.session_state[pending_delete_key] = False
                                        st.success(f"Deleted {st_name}.")
                                        st.rerun()
                                    except PermissionDeniedError as pe:
                                        st.error(str(pe))
                                    except Exception:
                                        st.error("Failed to delete student.")

                st.markdown(
                    "<div style='border-bottom: 1px solid var(--border-outline-variant); margin: 4px 0;'></div>",
                    unsafe_allow_html=True,
                )

    st.write("")
    st.write("")

    # 3. Chapter Performance
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Curriculum Health (Class-Wide)</h4>
                <div class="section-subtitle-text">Average scores, diagnostic accuracy, and quiz engagement per curriculum chapter.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chapter_stats = get_class_chapter_performance(cls_int)
    if chapter_stats:
        for ch in chapter_stats:
            avg = ch["average"]
            acc = ch["accuracy"]
            taken = ch["quizzes_taken"]

            if avg >= 70:
                color_theme = "var(--md-tertiary)"
                badge_bg = "var(--md-tertiary-container)"
                status_txt = "STRONG"
            elif avg >= 50:
                color_theme = "var(--md-amber)"
                badge_bg = "var(--md-amber-container)"
                status_txt = "AVERAGE"
            else:
                color_theme = "var(--md-error)"
                badge_bg = "var(--md-error-container)"
                status_txt = "NEEDS ATTENTION"

            st.markdown(
                f"""
                <div style="background: var(--surface-container); border: 1px solid var(--border-outline-variant); border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 700; font-size: 1.05rem; color: var(--text-primary); font-family: 'Outfit', sans-serif;">
                            {ch["chapter"]}
                        </div>
                        <span style="background: {badge_bg}; color: {color_theme}; font-weight: 700; font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; letter-spacing: 0.05em;">
                            {status_txt}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 12px;">
                        <div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Average Score</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: {color_theme};">{avg}%</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Accuracy</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary);">{acc}%</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Quizzes Attempted</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary);">{taken}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No quiz telemetry available for this class yet.")
