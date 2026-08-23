"""Teacher Analytics & Early-Warning Diagnostic Dashboard UI component."""

from typing import Optional

import streamlit as st

from src.academic_rag.analytics.teacher import get_teacher_student_profile


def render_teacher_tab(student_id: str, class_level: Optional[int] = None):
    """Renders Teacher Master Analytics and Early-Warning Diagnostics Dashboard with class isolation."""
    class_label = f" [Class {class_level}]" if class_level else ""
    st.markdown("### Teacher Analytics & Early-Warning Dashboard")
    st.caption(
        f"Detailed pedagogical analysis and transparent early-warning diagnostic indicators for **`{student_id}`**{class_label}."
    )

    prof = get_teacher_student_profile(student_id, class_level=class_level)

    if not prof.get("has_data"):
        st.info(
            f"No quiz data found for student `{student_id}`. Quizzes taken by the student will populate this dashboard."
        )
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
        st.success(
            f"### Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )
    elif status_code in ["improving", "improving_low_base"]:
        st.info(
            f"### Overall Standing: **{status_title}** "
            f"(Upward Trajectory: {st_status['trend']['earlier_average']}% -> {st_status['trend']['recent_average']}%)"
        )
    elif status_code == "monitor":
        st.warning(
            f"### Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )
    else:
        st.error(
            f"### Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
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
    st.markdown("#### Student Lifetime Metrics")
    t_m1, t_m2, t_m3, t_m4, t_m5 = st.columns(5)
    t_m1.metric("Class Level", f"Class {st_overview['class']}")
    t_m2.metric("Overall Average", f"{st_overview['overall_average']}%")
    t_m3.metric("Quizzes Completed", st_overview["total_quizzes"])
    t_m4.metric(
        "Questions Attempted",
        f"{st_overview['questions_attempted']} (Correct: {st_overview['questions_correct']})",
    )
    t_m5.metric("Accuracy", f"{st_overview['accuracy']}%")

    st.divider()

    # 3. Chapter Performance Breakdown
    st.markdown("#### Chapter-Wise Performance Statistics")
    if st_chapters:
        ch_table_rows = []
        for c in st_chapters:
            ch_table_rows.append(
                {
                    "Chapter": f"{c['chapter']}",
                    "Average Score": f"{c['average']}%",
                    "Accuracy": f"{c['accuracy']}%",
                    "Attempts": c["attempts"],
                    "Questions (Corr/Att)": f"{c['questions_correct']}/{c['questions_attempted']}",
                    "SWAT Category": c["status"].upper(),
                }
            )
        st.table(ch_table_rows)

    st.divider()

    # 4. Strength / Weakness Summary (4-Category SWAT)
    st.markdown("#### Chapter Mastery (4-Category SWAT)")
    ts_col1, ts_col2, ts_col3, ts_col4 = st.columns(4)
    with ts_col1:
        st.markdown("##### Strengths (≥ 70%)")
        if st_swat.get("strengths"):
            for s in st_swat["strengths"]:
                st.success(f"**{s['chapter']}** ({s['score']}%)")
        else:
            st.caption("None yet.")

    with ts_col2:
        st.markdown("##### Average (50%–69%)")
        if st_swat.get("average_topics"):
            for a in st_swat["average_topics"]:
                st.info(f"**{a['chapter']}** ({a['score']}%)")
        else:
            st.caption("None.")

    with ts_col3:
        st.markdown("##### Weak (< 50%)")
        if st_swat.get("weak_topics"):
            for w in st_swat["weak_topics"]:
                st.warning(f"**{w['chapter']}** ({w['score']}%)")
        else:
            st.caption("None.")

    with ts_col4:
        st.markdown("##### Unattempted")
        if st_swat.get("unattempted_topics"):
            for u in st_swat["unattempted_topics"]:
                st.markdown(f"- {u['chapter']}")
        else:
            st.caption("None.")

    st.divider()

    # 5. Recommended Focus & Action-Plan Statistics
    st.markdown("#### Recommended Focus & Action-Plan Statistics")
    st_plan = prof.get("action_plan", {})
    if st_plan.get("actions"):
        for act in st_plan["actions"][:4]:
            p_label = act.get("priority_label", "RECOMMENDATION")
            score_str = f"{act['score']}%" if act["score"] is not None else "Not attempted"
            attempts_str = (
                f"{act.get('attempts', 0)} attempt{'s' if act.get('attempts', 0) != 1 else ''}"
            )
            recent_str = (
                f" | Trajectory: {act.get('recent_performance')}"
                if act.get("attempts", 0) > 1
                else ""
            )
            st.info(
                f"**{p_label} (Priority {act['priority_rank']}): {act['chapter']}**  \n"
                f"Score: **{score_str}** | Attempts: **{attempts_str}**{recent_str}  \n"
                f"*{act['reason']}*"
            )

    st.divider()

    # 6. Chronological Quiz Log
    st.markdown("#### Chronological Quiz Log")
    if st_history:
        for q in reversed(st_history):
            st.markdown(
                f"- **{q['date']}** | Chapter: **{q['chapter']}** | "
                f"Score: **{q['score']}/{q['total_questions']}** ({q['score_display']}) | "
                f"Difficulty: `{q['difficulty']}`"
            )
    else:
        st.caption("No quiz attempts recorded.")
