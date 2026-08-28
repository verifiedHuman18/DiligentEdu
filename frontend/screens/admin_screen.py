"""Class Admin Dashboard."""

import streamlit as st

from backend.analytics.admin import (
    get_class_chapter_performance,
    get_class_overview,
    get_class_students,
)
from backend.analytics.teacher import promote_student_in_db
from frontend.components.cards import render_metric_card


def render_admin_screen(selected_class: str = "Class 10") -> None:
    """Renders the Class Admin dashboard."""
    from frontend.state import get_student_class_level

    cls_int = get_student_class_level()

    st.markdown(f"###  Class {cls_int} Administrator Dashboard")
    st.caption("Class-wide analytics, curriculum health, and student roster management.")
    st.write("")

    # 1. Class Overview Metrics
    overview = get_class_overview(cls_int)

    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Aggregate Class Health</h4>
                <div class="section-subtitle-text">Performance averages across all students in the class.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(
            "Active Students", f"{overview['active_students']} / {overview['total_students']}"
        )
    with m2:
        render_metric_card("Class Average", f"{overview['class_average']}%")
    with m3:
        render_metric_card("Class Accuracy", f"{overview['class_accuracy']}%")
    with m4:
        render_metric_card("Total Quizzes", overview["total_quizzes"])

    st.write("")
    st.write("")

    # 2. Student Roster & Promotion
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Student Management</h4>
                <div class="section-subtitle-text">Roster of enrolled students and promotion actions.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    students = get_class_students(cls_int)
    if not students:
        st.info(f"No students found in Class {cls_int}.")
    else:
        for s in students:
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(
                        f"**{s['name']}**  \n<span style='color: var(--text-secondary); font-size: 0.8rem;'>{s['email']}</span>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"<div style='padding-top: 8px;'>Class {s['class_level']}</div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    if s["class_level"] == 9:
                        if st.button("Promote to 10", key=f"promote_{s['id']}", type="primary"):
                            promote_student_in_db(s["id"], 10)
                            st.success(f"Promoted {s['name']} to Class 10!")
                            st.rerun()
                st.divider()

    st.write("")

    # 3. Chapter Performance
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Curriculum Health (Class-Wide)</h4>
                <div class="section-subtitle-text">Average scores and accuracy per chapter.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chapter_stats = get_class_chapter_performance(cls_int)
    if chapter_stats:
        for ch in chapter_stats:
            st.markdown(
                f"- **{ch['chapter']}**: Avg Score: {ch['average']}% | Accuracy: {ch['accuracy']}% | Quizzes Taken: {ch['quizzes_taken']}"
            )
    else:
        st.caption("No quiz data available for this class yet.")
