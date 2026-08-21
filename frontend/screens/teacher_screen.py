"""Teacher Diagnostics and Master Analytics Screen with Material Icons (No Emojis)."""

import streamlit as st
from src.academic_rag.analytics.teacher import get_teacher_student_profile
from frontend.components.cards import render_metric_card
from frontend.state import navigate_to


def render_teacher_screen(student_id: str) -> None:
    """Renders the Teacher Master Analytics and Early-Warning Diagnostic Dashboard."""
    if st.button("Back to Home", icon=":material/arrow_back:", type="secondary", key="teacher_top_back_btn"):
        navigate_to("home")
        st.rerun()

    st.write("")
    st.markdown("### Teacher Analytics and Diagnostics")
    st.caption(f"Pedagogical insights and early-warning mastery indicators for student **`{student_id}`**.")

    prof = get_teacher_student_profile(student_id)

    if not prof.get("has_data"):
        st.info(f"No quiz data found for student `{student_id}`.")
        return

    st_overview = prof["overview"]
    st_status = prof["status"]
    st_chapters = prof["chapter_statistics"]
    st_history = prof["quiz_history"]
    st_swat = prof["swat_summary"]

    # 1. Early-Warning Status Alert Banner
    status_title = st_status["overall_status"]
    status_code = st_status["status_code"]

    if status_code == "performing_well":
        st.success(f"Status: **{status_title}** (Overall Average: {st_overview['overall_average']}%)")
    elif status_code in ["improving", "improving_low_base"]:
        st.info(
            f"Status: **{status_title}** "
            f"(Upward Trajectory: {st_status['trend']['earlier_average']}% -> {st_status['trend']['recent_average']}%)"
        )
    elif status_code == "monitor":
        st.warning(f"Status: **{status_title}** (Overall Average: {st_overview['overall_average']}%)")
    else:
        st.error(f"Status: **{status_title}** (Overall Average: {st_overview['overall_average']}%)")

    # Alerts & Positive Notes
    if st_status.get("alerts"):
        for alert in st_status["alerts"]:
            st.warning(f"Notice: {alert}")
    if st_status.get("positive_notes"):
        for note in st_status["positive_notes"]:
            st.success(f"Commendation: {note}")

    st.write("")

    # 2. Master Metrics Grid
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card("Overall Average", f"{st_overview['overall_average']}%")
    with m2:
        render_metric_card("Quizzes Taken", st_overview["total_quizzes"])
    with m3:
        render_metric_card("Questions Answered", st_overview["total_questions"])
    with m4:
        render_metric_card("Accuracy", f"{st_overview['overall_accuracy_rate']}%")
    with m5:
        render_metric_card("Chapters Covered", f"{len(st_chapters)}/26")

    st.write("")

    # 3. Chapter-Wise Performance Breakdown
    st.markdown("#### Chapter-Wise Performance")
    if st_chapters:
        for ch in st_chapters:
            sc = ch["average_score"]
            attempts = ch["attempts"]
            tot_q = ch["total_questions"]
            tot_c = ch["total_correct"]
            st_text = ch["status_text"].upper()

            with st.expander(f"Ch {ch['chapter_number']} — {ch['chapter']} | Average: {sc}% [{st_text}] | Attempts: {attempts}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Chapter Average", f"{sc}%")
                with c2:
                    st.metric("Total Questions", f"{tot_c}/{tot_q}")
                with c3:
                    st.metric("Quizzes Attempted", attempts)
                if ch.get("last_attempt"):
                    st.caption(f"Last Attempt: {ch['last_attempt'][:16]}")
    else:
        st.caption("No chapter records available.")

    st.write("")

    # 4. Recent Student Activity Log
    st.markdown("#### Recent Activity Log")
    if st_history:
        for q in reversed(st_history[-5:]):
            st.markdown(
                f"- **{q['timestamp'][:16]}** | Ch: **{q['chapter']}** | "
                f"Score: **{q['score']}/{q['total_questions']}** "
                f"({round((q['score']/q['total_questions'])*100, 1) if q['total_questions'] else 0}%) | "
                f"Difficulty: `{q.get('difficulty', 'medium')}`"
            )
    else:
        st.caption("No recent activity.")
