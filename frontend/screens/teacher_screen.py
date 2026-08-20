"""Teacher Diagnostics and Master Analytics Screen (No Emojis)."""

import streamlit as st
from src.academic_rag.analytics.teacher import get_teacher_student_profile
from frontend.components.cards import render_metric_card


def render_teacher_screen(student_id: str) -> None:
    """Renders the Teacher Master Analytics and Early-Warning Diagnostic Dashboard."""
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
            st.warning(alert["message"])

    if st_status.get("positive_notes"):
        for note in st_status["positive_notes"]:
            st.success(note)

    st.write("")

    # 2. Lifetime Metrics Grid
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card("Class Level", f"Class {st_overview['class']}")
    with m2:
        render_metric_card("Overall Average", f"{st_overview['overall_average']}%")
    with m3:
        render_metric_card("Quizzes Taken", st_overview["total_quizzes"])
    with m4:
        render_metric_card("Questions Attempted", f"{st_overview['questions_attempted']}")
    with m5:
        render_metric_card("Accuracy", f"{st_overview['accuracy']}%")

    st.divider()

    # 3. Chapter Performance Table
    st.markdown("#### Chapter-Wise Performance")
    if st_chapters:
        ch_table_rows = []
        for c in st_chapters:
            ch_table_rows.append({
                "Chapter": c["chapter"],
                "Average Score": f"{c['average']}%",
                "Accuracy": f"{c['accuracy']}%",
                "Attempts": c["attempts"],
                "Questions (Corr/Att)": f"{c['questions_correct']}/{c['questions_attempted']}",
                "SWAT Status": c["status"].upper(),
            })
        st.dataframe(ch_table_rows, use_container_width=True)

    st.divider()

    # 4. Strength / Weakness Diagnostic
    st.markdown("#### Teacher Diagnostic Matrix")
    ts1, ts2, ts3 = st.columns(3)
    with ts1:
        st.markdown("##### STRONG (>= 70%)")
        if st_swat.get("strengths"):
            for s in st_swat["strengths"]:
                st.success(f"**{s['chapter']}** ({s['score']}%)")
        else:
            st.caption("None yet.")

    with ts2:
        st.markdown("##### AVERAGE (50%–69%)")
        if st_swat.get("average_topics"):
            for a in st_swat["average_topics"]:
                st.info(f"**{a['chapter']}** ({a['score']}%)")
        else:
            st.caption("None.")

    with ts3:
        st.markdown("##### WEAK (< 50%)")
        if st_swat.get("weak_topics"):
            for w in st_swat["weak_topics"]:
                st.error(f"**{w['chapter']}** ({w['score']}%)")
        else:
            st.caption("None.")

    st.divider()

    # 5. Chronological Quiz Log
    st.markdown("#### Chronological Quiz History Log")
    if st_history:
        hist_display = []
        for row in reversed(st_history):
            hist_display.append({
                "Date": row["date"],
                "Chapter": row["chapter"],
                "Difficulty": row["difficulty"],
                "Score": row["score_display"],
                "Questions": f"{row['score']}/{row['total_questions']}",
                "Timestamp": row["timestamp"][:19].replace("T", " "),
            })
        st.dataframe(hist_display, use_container_width=True)
