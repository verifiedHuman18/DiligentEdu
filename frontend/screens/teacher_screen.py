"""Teacher Diagnostics and Master Analytics Screen with Material Icons (No Emojis)."""

import textwrap
from typing import Optional

import streamlit as st

from frontend.components.cards import render_metric_card, render_swat_columns
from frontend.components.navigation import render_back_to_home
from frontend.state import get_user_role
from src.academic_rag.analytics.teacher import get_teacher_student_profile
from src.academic_rag.storage.repository import quiz_repository


def render_teacher_screen(
    student_id: Optional[str] = None, selected_class: str = "Class 10"
) -> None:
    """Renders the Teacher Master Analytics, 4-Category SWAT, and Action-Plan Diagnostics with dedicated Class & Student selectors."""
    # If a student navigated here in legacy/test mode, provide Back to Home
    if get_user_role() == "student":
        render_back_to_home("teacher")

    # Fetch available student IDs from quiz database
    all_students = quiz_repository.get_all_student_ids()
    default_student = student_id or st.session_state.get("student_id", "student_001")
    if default_student not in all_students:
        all_students = [default_student] + [s for s in all_students if s != default_student]

    t_c1, t_c2, t_c3 = st.columns([2.2, 1.4, 1.4])
    with t_c1:
        st.markdown("### Teacher Diagnostics & Analytics")
        st.caption(
            "Pedagogical insights, 4-category SWAT breakdown, and action-plan supporting statistics."
        )
    with t_c2:
        curr_inspect_student = st.selectbox(
            "Select Student to Inspect",
            options=all_students,
            index=0,
            key="teacher_inspect_student_select",
            help="Select a student from database records to inspect diagnostic telemetry.",
        )
    with t_c3:
        teacher_class = st.radio(
            "Class to Inspect",
            options=["Class 10", "Class 9"],
            horizontal=True,
            key="teacher_screen_class_toggle",
            help="Inspect student performance strictly for Class 10 or Class 9.",
        )

    target_student_id = curr_inspect_student or default_student
    cls_int = 10 if teacher_class == "Class 10" else 9

    prof = get_teacher_student_profile(target_student_id, class_level=cls_int)

    if not prof.get("has_data"):
        st.info(f"No quiz data found for student `{target_student_id}` in {teacher_class}.")
        return

    st_overview = prof["overview"]
    st_status = prof["status"]
    st_chapters = prof["chapter_statistics"]
    st_history = prof["quiz_history"]
    st_swat = prof.get("swat_summary", {})
    st_plan = prof.get("action_plan", {})

    # 1. Early-Warning Status Alert Banner
    status_title = st_status["overall_status"]
    status_code = st_status["status_code"]

    if status_code == "performing_well":
        st.success(
            f"Overall Status: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )
    elif status_code in ["improving", "improving_low_base"]:
        st.info(
            f"Overall Status: **{status_title}** "
            f"(Upward Trajectory: {st_status['trend']['earlier_average']}% -> {st_status['trend']['recent_average']}%)"
        )
    elif status_code == "monitor":
        st.warning(
            f"Overall Status: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )
    else:
        st.error(
            f"Overall Status: **{status_title}** (Overall Average: {st_overview['overall_average']}%)"
        )

    # Alerts & Positive Notes
    if st_status.get("alerts"):
        for alert in st_status["alerts"]:
            msg = alert.get("message") if isinstance(alert, dict) else str(alert)
            st.warning(f"{msg}")
    if st_status.get("positive_notes"):
        for note in st_status["positive_notes"]:
            st.success(f"{note}")

    st.write("")

    # 2. Master Metrics Grid
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card("Overall Average", f"{st_overview['overall_average']}%")
    with m2:
        render_metric_card("Overall Accuracy", f"{st_overview.get('accuracy', 0)}%")
    with m3:
        render_metric_card("Quizzes Taken", st_overview["total_quizzes"])
    with m4:
        att_chs = st_overview.get("attempted_chapters", len(st_chapters))
        tot_chs = st_overview.get("total_chapters", 13)
        render_metric_card("Chapters Covered", f"{att_chs}/{tot_chs}")
    with m5:
        dir_str = st_status.get("trend", {}).get("direction", "stable").capitalize()
        render_metric_card("Trend", dir_str)

    st.write("")

    # 3. Phase 19: Recommended Focus & Action-Plan Statistics (with Reasoning)
    st.markdown("#### Recommended Action Plan & Diagnostic Statistics")
    st.caption(
        "Pedagogical recommendations with attempt counts, score trajectories, and underlying rationale."
    )

    actions = st_plan.get("actions", [])
    if actions:
        # Display top priorities in clean cards
        for act in actions[:4]:
            p_label = act.get("priority_label", "RECOMMENDATION")
            ch_name = act["chapter"]
            score_str = f"{act['score']}%" if act["score"] is not None else "Not attempted"
            attempts_str = (
                f"{act.get('attempts', 0)} attempt{'s' if act.get('attempts', 0) != 1 else ''}"
            )
            recent_str = (
                f"Trajectory: {act.get('recent_performance', '—')}"
                if act.get("attempts", 0) > 1
                else ""
            )

            action_card_html = textwrap.dedent(f"""\
<div style="background: var(--surface-container); border-left: 4px solid var(--md-primary); border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
<div style="font-weight: 700; font-size: 0.85rem; color: var(--md-primary);">{p_label} — Priority {act["priority_rank"]}</div>
<div style="font-size: 1.05rem; font-weight: 700; color: var(--on-surface); margin: 4px 0;">{ch_name}</div>
<div style="font-size: 0.88rem; color: var(--on-surface-variant); margin-bottom: 4px;">
<strong>Score:</strong> {score_str} &nbsp;|&nbsp; <strong>Attempts:</strong> {attempts_str} {("&nbsp;|&nbsp; <strong>" + recent_str + "</strong>") if recent_str else ""}
</div>
<div style="font-size: 0.85rem; color: var(--on-surface);"><strong>Reason:</strong> {act["reason"]}</div>
</div>\
""")
            st.markdown(action_card_html, unsafe_allow_html=True)
    else:
        st.caption("No specific action items identified.")

    st.write("")

    # 4. Phase 19: 4-Category SWAT Summary
    st.markdown("#### Chapter Mastery (4-Category SWAT)")
    render_swat_columns(st_swat)

    st.write("")

    # 5. Recent Student Activity Log
    st.markdown("#### Chronological Quiz History")
    if st_history:
        for q in reversed(st_history[-6:]):
            st.markdown(
                f"- **{q['date']}** | Ch: **{q['chapter']}** | "
                f"Score: **{q['score']}/{q['total_questions']}** ({q['score_display']}) | "
                f"Difficulty: `{q['difficulty']}`"
            )
    else:
        st.caption("No recent quiz activity.")
