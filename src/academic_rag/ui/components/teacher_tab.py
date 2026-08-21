"""Teacher Analytics & Early-Warning Diagnostic Dashboard UI component."""

import streamlit as st

from src.academic_rag.analytics.teacher import get_teacher_student_profile


def render_teacher_tab(student_id: str):
    """Renders Teacher Master Analytics and Early-Warning Diagnostics Dashboard."""
    st.markdown("### 👨‍🏫 Teacher Analytics & Early-Warning Dashboard")
    st.caption(
        f"Detailed pedagogical analysis and transparent early-warning diagnostic indicators for **`{student_id}`**."
    )

    prof = get_teacher_student_profile(student_id)

    if not prof.get("has_data"):
        st.info(
            f"ℹ️ No quiz data found for student `{student_id}`. Quizzes taken by the student will populate this dashboard."
        )
        return

    st_overview = prof["overview"]
    st_status = prof["status"]
    st_chapters = prof["chapter_statistics"]
    st_history = prof["quiz_history"]
    st_swat = prof["swat_summary"]

    # 1. Early-Warning Status Alert Banner
    status_icon = st_status["status_icon"]
    status_title = st_status["overall_status"]
    status_code = st_status["status_code"]

    if status_code == "performing_well":
        st.success(
            f"### {status_icon} Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )
    elif status_code in ["improving", "improving_low_base"]:
        st.info(
            f"### {status_icon} Overall Standing: **{status_title}** "
            f"(Upward Trajectory: {st_status['trend']['earlier_average']}% ➔ {st_status['trend']['recent_average']}%)"
        )
    elif status_code == "monitor":
        st.warning(
            f"### {status_icon} Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )
    else:
        st.error(
            f"### {status_icon} Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )

    # Display Active Alerts / Positive Notes
    if st_status.get("alerts"):
        for alert in st_status["alerts"]:
            st.warning(alert["message"])

    if st_status.get("positive_notes"):
        for note in st_status["positive_notes"]:
            st.success(note)

    st.divider()

    # 2. Key Student Overview Metrics
    st.markdown("#### 📈 Student Lifetime Metrics")
    t_m1, t_m2, t_m3, t_m4, t_m5 = st.columns(5)
    t_m1.metric("Class Level", f"Class {st_overview['class']}")
    t_m2.metric("Overall Average", f"{st_overview['overall_average']}%")
    t_m3.metric("Quizzes Completed", st_overview["total_quizzes"])
    t_m4.metric(
        "Questions Attempted",
        f"{st_overview['questions_attempted']} (✓ {st_overview['questions_correct']})",
    )
    t_m5.metric("Accuracy", f"{st_overview['accuracy']}%")

    st.divider()

    # 3. Chapter Performance Breakdown
    st.markdown("#### 📚 Chapter-Wise Performance Statistics")
    if st_chapters:
        ch_table_rows = []
        for c in st_chapters:
            icon = "🟢" if c["status"] == "strong" else ("🟡" if c["status"] == "average" else "🔴")
            ch_table_rows.append(
                {
                    "Chapter": f"{icon} {c['chapter']}",
                    "Average Score": f"{c['average']}%",
                    "Accuracy": f"{c['accuracy']}%",
                    "Attempts": c["attempts"],
                    "Questions (Corr/Att)": f"{c['questions_correct']}/{c['questions_attempted']}",
                    "SWAT Category": c["status"].upper(),
                }
            )
        st.table(ch_table_rows)

    st.divider()

    # 4. Strength / Weakness Summary
    st.markdown("#### 🎯 Teacher SWAT Diagnostic")
    ts_col1, ts_col2, ts_col3 = st.columns(3)
    with ts_col1:
        st.markdown("##### 🟢 Strengths (≥ 70%)")
        if st_swat.get("strengths"):
            for s in st_swat["strengths"]:
                st.success(f"**{s['chapter']}** ({s['score']}%)")
        else:
            st.caption("None yet.")

    with ts_col2:
        st.markdown("##### 🟡 Average Topics (50%–69%)")
        if st_swat.get("average_topics"):
            for a in st_swat["average_topics"]:
                st.info(f"**{a['chapter']}** ({a['score']}%)")
        else:
            st.caption("None.")

    with ts_col3:
        st.markdown("##### 🔴 Weak Topics (< 50%)")
        if st_swat.get("weak_topics"):
            for w in st_swat["weak_topics"]:
                st.error(f"**{w['chapter']}** ({w['score']}%)")
        else:
            st.caption("None.")

    st.divider()

    # 5. Chronological Quiz Log
    st.markdown("#### 🕒 Chronological Quiz History Log")
    if st_history:
        hist_display = []
        for row in reversed(st_history):
            hist_display.append(
                {
                    "Date": row["date"],
                    "Chapter": row["chapter"],
                    "Difficulty": row["difficulty"],
                    "Score": row["score_display"],
                    "Questions": f"{row['score']}/{row['total_questions']}",
                    "Timestamp (UTC)": row["timestamp"][:19].replace("T", " "),
                }
            )
        st.dataframe(hist_display, use_container_width=True)
