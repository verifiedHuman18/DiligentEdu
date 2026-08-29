"""Teacher Diagnostics and Master Analytics Screen with Material Icons (No Emojis)."""

import textwrap
from typing import Optional

import streamlit as st

from backend.analytics.action_plan import (
    reset_teacher_action_plan,
    save_teacher_action_plan,
)
from backend.analytics.teacher import (
    get_all_students_from_db,
    get_teacher_student_profile,
)
from backend.curriculum.service import curriculum_service
from frontend.components.cards import render_metric_card, render_swat_columns
from frontend.components.navigation import render_back_to_home
from frontend.components.performance_trend_chart import render_performance_trend_section
from frontend.state import get_user_role


def render_teacher_screen(
    student_id: Optional[str] = None, selected_class: str = "Class 10"
) -> None:
    """Renders the Teacher Master Analytics, 4-Category SWAT, and Action-Plan Diagnostics with distinct visual sections."""
    # If a student navigated here in legacy/test mode, provide Back to Home
    if get_user_role() == "student":
        render_back_to_home("teacher")

    # Fetch available student IDs from DB
    all_students_data = get_all_students_from_db()
    if not all_students_data:
        all_students_data = [
            {
                "id": student_id or st.session_state.get("student_id", "student_001"),
                "name": "Test Student",
                "class_level": 10,
            }
        ]

    student_map = {
        s["id"]: f"{s['name']} (Class {s['class_level'] or 10})" for s in all_students_data
    }
    student_class_map = {s["id"]: s["class_level"] or 10 for s in all_students_data}
    student_ids = list(student_map.keys())

    default_student = student_id or st.session_state.get("student_id", "student_001")
    if default_student not in student_ids:
        default_student = student_ids[0]

    from frontend.state import get_student_subject

    current_subject = get_student_subject()

    t_c1, t_c2 = st.columns([2.0, 2.0])
    with t_c1:
        st.markdown("### Teacher Diagnostics")
        st.caption("Pedagogical insights, 4-category SWAT breakdown, and action-plan statistics.")
    with t_c2:
        curr_inspect_student = st.selectbox(
            "Select Student to Inspect",
            options=student_ids,
            format_func=lambda x: student_map.get(x, x),
            index=student_ids.index(default_student) if default_student in student_ids else 0,
            key="teacher_inspect_student_select",
            help="Select a student from database records to inspect diagnostic telemetry.",
        )

    target_student_id = curr_inspect_student or default_student
    student_current_class = student_class_map.get(target_student_id, 10)
    target_student_name = student_map.get(target_student_id, target_student_id).split(" (Class")[0]

    cls_int = student_current_class
    teacher_class = f"Class {cls_int}"
    subject = current_subject

    prof = get_teacher_student_profile(target_student_id, class_level=cls_int, subject=subject)
    has_history = prof.get("has_data", False)

    st_overview = prof.get("overview", {})
    st_status = prof.get("status", {})
    st_chapters = prof.get("chapter_statistics", [])
    st_history = prof.get("quiz_history", [])
    st_swat = prof.get("swat_summary", {})
    st_plan = prof.get("action_plan", {})

    st.write("")

    if not has_history:
        st.info(
            f"No quiz data found for student `{target_student_name}`. "
            "You can assign a customized study action plan below to guide their onboarding."
        )
    else:
        # SECTION 1: Diagnostic Status & Master Metrics
        st.markdown(
            """
            <div class="section-header-bar">
                <div>
                    <h4 class="section-title-text">Diagnostic Overview & Metrics</h4>
                    <div class="section-subtitle-text">Real-time performance trajectory and aggregate quiz telemetry.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        status_title = st_status.get("overall_status", "Active")
        status_code = st_status.get("status_code", "monitor")
        overall_avg = st_overview.get("overall_average", 0)
        trend_info = st_status.get("trend", {})
        trend_dir = trend_info.get("direction", "stable").capitalize()
        trend_reason = trend_info.get("reason", "")
        alerts = st_status.get("alerts", [])
        positive_notes = st_status.get("positive_notes", [])

        if status_code == "performing_well":
            badge_bg = "var(--md-tertiary-container)"
            badge_color = "var(--md-on-tertiary-container)"
            badge_border = "var(--md-tertiary)"
        elif status_code in ["improving", "improving_low_base"]:
            badge_bg = "var(--md-cyan-container)"
            badge_color = "var(--md-on-cyan-container)"
            badge_border = "var(--md-cyan)"
        elif status_code == "monitor":
            badge_bg = "var(--md-amber-container)"
            badge_color = "var(--md-on-amber-container)"
            badge_border = "var(--md-amber)"
        else:
            badge_bg = "var(--md-error-container)"
            badge_color = "var(--md-on-error-container)"
            badge_border = "var(--md-error)"

        items_html = []
        if trend_reason:
            items_html.append(
                f'<div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4;"><strong>Trajectory:</strong> {trend_reason}</div>'
            )
        if alerts:
            for a in alerts:
                msg = a.get("message") if isinstance(a, dict) else str(a)
                # Clean any legacy emoji from alert message
                clean_msg = msg.replace("", "").replace("", "").strip()
                items_html.append(
                    f'<div style="font-size: 0.85rem; color: var(--danger-text); line-height: 1.4;"><strong>Attention:</strong> {clean_msg}</div>'
                )
        if positive_notes:
            for p in positive_notes:
                clean_p = p.replace("", "").replace("", "").strip()
                items_html.append(
                    f'<div style="font-size: 0.85rem; color: var(--md-tertiary); line-height: 1.4;"><strong>Strength:</strong> {clean_p}</div>'
                )

        details_block = (
            '<div style="display: flex; flex-direction: column; gap: 4px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border-outline-variant);">'
            + "".join(items_html)
            + "</div>"
            if items_html
            else ""
        )

        st.markdown(
            f"""
            <div style="background: var(--surface-container-low); border: 1px solid var(--border-outline-variant); border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 0.76rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; text-transform: uppercase;">
                            {status_title}
                        </span>
                        <span style="font-size: 0.88rem; font-weight: 600; color: var(--text-primary);">
                            Student Diagnostic Status
                        </span>
                    </div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary);">
                        Average: <strong style="color: var(--text-primary);">{overall_avg}%</strong> &nbsp;•&nbsp; Trend: <strong style="color: var(--text-primary);">{trend_dir}</strong>
                    </div>
                </div>
                {details_block}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Master Metrics Grid
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            render_metric_card("Overall Average", f"{st_overview.get('overall_average', 0)}%")
        with m2:
            render_metric_card("Overall Accuracy", f"{st_overview.get('accuracy', 0)}%")
        with m3:
            render_metric_card("Quizzes Taken", st_overview.get("total_quizzes", 0))
        with m4:
            att_chs = st_overview.get("attempted_chapters", len(st_chapters))
            tot_chs = st_overview.get("total_chapters", 13)
            render_metric_card("Chapters Covered", f"{att_chs}/{tot_chs}")
        with m5:
            dir_str = st_status.get("trend", {}).get("direction", "stable").capitalize()
            render_metric_card("Trend", dir_str)

        st.write("")
        st.write("")

        # SECTION: Performance Over Time & Trend Analytics
        render_performance_trend_section(
            student_id=target_student_id,
            class_level=cls_int,
            subject=subject,
        )

        st.write("")
        st.write("")

    # SECTION 2: Recommended Action Plan & Teacher Customization
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Study Action Plan & Guidance</h4>
                <div class="section-subtitle-text">Pedagogical recommendations with attempt counts, score trajectories, and underlying rationale.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    is_customized = st_plan.get("is_customized", False)
    teacher_notes = st_plan.get("teacher_notes")

    # Plan Status Banner
    if is_customized:
        notes_html = (
            f"<div style='font-size: 0.85rem; color: var(--on-surface); margin-top: 4px;'><strong>Teacher's Guidance:</strong> {teacher_notes}</div>"
            if teacher_notes
            else ""
        )
        st.markdown(
            f"""
            <div style="background: var(--surface-container); border-left: 4px solid var(--md-primary); border-radius: 8px; padding: 10px 14px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: var(--md-primary); color: var(--on-primary); font-weight: 700; font-size: 0.76rem; padding: 2px 8px; border-radius: 4px;">CUSTOM TEACHER PLAN ACTIVE</span>
                    <span style="font-size: 0.82rem; color: var(--on-surface-variant);">Assigned specifically for {target_student_name} ({teacher_class})</span>
                </div>
                {notes_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: var(--surface-container-low); border: 1px solid var(--outline-variant); border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                <span style="background: var(--surface-container-high); color: var(--on-surface); font-weight: 700; font-size: 0.76rem; padding: 2px 8px; border-radius: 4px;">AUTOMATED SWAT PLAN ACTIVE</span>
                <span style="font-size: 0.82rem; color: var(--on-surface-variant);">Generated dynamically from quiz telemetry and weak topic analysis.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Top Action Cards Display
    actions = st_plan.get("actions", [])
    if actions:
        for act in actions[:4]:
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

            is_t_assigned = act.get("is_teacher_assigned", False)
            border_color = "var(--md-primary)" if is_t_assigned else "var(--outline-variant)"
            priority_tag = (
                f"Priority {act['priority_rank']} · Teacher Assigned"
                if is_t_assigned
                else f"Priority {act['priority_rank']} · SWAT Recommended"
            )

            action_card_html = textwrap.dedent(f"""\
<div style="background: var(--surface-container); border-left: 4px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
<div style="font-weight: 700; font-size: 0.8rem; color: var(--md-primary); text-transform: uppercase; letter-spacing: 0.5px;">{priority_tag}</div>
<div style="font-size: 1.05rem; font-weight: 700; color: var(--on-surface); margin: 4px 0;">{ch_name}</div>
<div style="font-size: 0.86rem; color: var(--on-surface-variant); margin-bottom: 4px;">
<strong>Score:</strong> {score_str} &nbsp;|&nbsp; <strong>Attempts:</strong> {attempts_str} {("&nbsp;|&nbsp; <strong>" + recent_str + "</strong>") if recent_str else ""} &nbsp;|&nbsp; <strong>Target Difficulty:</strong> `{act.get("difficulty", "medium")}`
</div>
<div style="font-size: 0.85rem; color: var(--on-surface);"><strong>Reason:</strong> {act["reason"]}</div>
</div>\
""")
            st.markdown(action_card_html, unsafe_allow_html=True)
    else:
        st.caption("No specific action items identified.")

    # Teacher Action Plan Customization Editor
    with st.expander(
        "Customize / Override Action Plan for this Student",
        icon=":material/tune:",
        expanded=is_customized,
    ):
        st.markdown(f"##### Edit Study Plan for `{target_student_name}`")
        st.caption(
            "Select specific NCERT chapters, set difficulty levels, and provide tailored guidance. "
            "These priorities will immediately take top precedence in the student's Home Screen."
        )

        all_grade_chapters = curriculum_service.get_chapters_for_grade(cls_int, subject=subject)
        ch_titles = [c.chapter_title for c in all_grade_chapters]

        num_assigned = st.slider(
            "Number of Priority Chapters to Assign",
            min_value=1,
            max_value=min(5, len(ch_titles)),
            value=min(3, len(ch_titles)),
            key=f"t_edit_num_ch_{cls_int}_{subject}_{target_student_id}",
        )

        custom_actions_inputs = []

        for i in range(num_assigned):
            st.markdown(f"**Priority {i + 1} Target**")
            col_ch, col_diff, col_act = st.columns([2.5, 1.2, 1.5])

            # Pre-populate defaults from existing plan or curriculum
            default_ch_idx = i if i < len(ch_titles) else 0
            if i < len(actions) and actions[i]["chapter"] in ch_titles:
                default_ch_idx = ch_titles.index(actions[i]["chapter"])

            with col_ch:
                chosen_ch = st.selectbox(
                    f"Chapter {i + 1}",
                    options=ch_titles,
                    index=default_ch_idx,
                    key=f"t_edit_ch_{cls_int}_{subject}_{target_student_id}_{i}",
                )

            with col_diff:
                default_diff = (
                    actions[i].get("difficulty", "medium") if i < len(actions) else "medium"
                )
                diff_opts = ["medium", "easy", "hard"]
                chosen_diff = st.selectbox(
                    f"Difficulty {i + 1}",
                    options=diff_opts,
                    index=diff_opts.index(default_diff) if default_diff in diff_opts else 0,
                    key=f"t_edit_diff_{cls_int}_{subject}_{target_student_id}_{i}",
                )

            with col_act:
                default_act_type = (
                    actions[i].get("action", "practice") if i < len(actions) else "practice"
                )
                act_opts = ["practice", "diagnostic", "mastery"]
                chosen_act = st.selectbox(
                    f"Goal {i + 1}",
                    options=act_opts,
                    index=act_opts.index(default_act_type) if default_act_type in act_opts else 0,
                    key=f"t_edit_act_{cls_int}_{subject}_{target_student_id}_{i}",
                )

            default_note = (
                actions[i].get("teacher_note") or actions[i].get("reason", "")
                if i < len(actions) and actions[i].get("is_teacher_assigned")
                else ""
            )
            ch_note = st.text_input(
                f"Guidance / Focus Note for Priority {i + 1} (optional)",
                value=default_note,
                placeholder="e.g. Focus on this chapter before Friday's assessment",
                key=f"t_edit_note_{cls_int}_{subject}_{target_student_id}_{i}",
            )

            custom_actions_inputs.append(
                {
                    "chapter": chosen_ch,
                    "difficulty": chosen_diff,
                    "action": chosen_act,
                    "reason": ch_note
                    or f"Teacher prioritized {chosen_ch} for focused {chosen_diff} practice.",
                    "teacher_note": ch_note,
                    "priority_label": f"TEACHER ASSIGNED #{i + 1}",
                }
            )
            st.divider()

        global_teacher_note = st.text_area(
            "Overall Teacher Instructions / Message for Student (optional)",
            value=teacher_notes or "",
            placeholder="e.g., Please complete these practice quizzes before Monday's revision class.",
            key=f"t_edit_global_note_{cls_int}_{subject}_{target_student_id}",
        )

        b_c1, b_c2, b_c3 = st.columns([1.6, 1.6, 1.8])

        with b_c1:
            if st.button(
                "Save & Assign Plan",
                type="primary",
                icon=":material/save:",
                key=f"btn_save_plan_{cls_int}_{subject}_{target_student_id}",
                use_container_width=True,
            ):
                save_teacher_action_plan(
                    student_id=target_student_id,
                    class_level=cls_int,
                    actions=custom_actions_inputs,
                    teacher_notes=global_teacher_note,
                    subject=subject,
                )
                st.success(f"Custom action plan successfully assigned to `{target_student_name}`!")
                st.rerun()

        with b_c2:
            if st.button(
                "Reset to AI / SWAT Plan",
                type="secondary",
                icon=":material/restart_alt:",
                key=f"btn_reset_plan_{cls_int}_{subject}_{target_student_id}",
                use_container_width=True,
                help="Clears teacher customizations and restores algorithmic SWAT recommendations based on quiz scores.",
            ):
                reset_teacher_action_plan(
                    student_id=target_student_id, class_level=cls_int, subject=subject
                )
                st.info(f"Restored automated SWAT action plan for `{target_student_name}`.")
                st.rerun()

    st.write("")
    st.write("")

    if has_history:
        # SECTION 3: 4-Category SWAT Summary
        st.markdown(
            """
            <div class="section-header-bar">
                <div>
                    <h4 class="section-title-text">Chapter Mastery Breakdown</h4>
                    <div class="section-subtitle-text">4-category SWAT matrix of subject strengths, average topics, weak areas, and unattempted chapters.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_swat_columns(st_swat)

        st.write("")
        st.write("")

        # SECTION 4: Chronological Quiz Activity Log
        st.markdown(
            """
            <div class="section-header-bar">
                <div>
                    <h4 class="section-title-text">Chronological Quiz History</h4>
                    <div class="section-subtitle-text">Recent assessment attempts, scores, and difficulty progression.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st_history:
            for q in reversed(st_history[-6:]):
                st.markdown(
                    f"- **{q['date']}** | Ch: **{q['chapter']}** | "
                    f"Score: **{q['score']}/{q['total_questions']}** ({q['score_display']}) | "
                    f"Difficulty: `{q['difficulty']}`"
                )
        else:
            st.caption("No recent quiz activity.")
