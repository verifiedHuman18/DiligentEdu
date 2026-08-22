"""Student Analytics Dashboard Screen with Material Icons (No Emojis, No SWAT Acronym)."""

from typing import Optional

import streamlit as st

from frontend.components.cards import render_metric_card
from frontend.state import get_student_class_level, navigate_to
from src.academic_rag.analytics.action_plan import generate_action_plan
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.repository import quiz_repository


def render_swat_screen(student_id: str, selected_class: Optional[str] = None) -> None:
    """Renders the Student Analytics and SWAT dashboard strictly bound to master profile class."""
    if st.button(
        "Back to Home", icon=":material/arrow_back:", type="secondary", key="swat_top_back_btn"
    ):
        navigate_to("home")
        st.rerun()

    class_level = get_student_class_level()

    st.write("")
    st.markdown(f"### Your Performance — Class {class_level} · Science")
    st.caption("Comprehensive SWAT analysis and chapter-wise mastery based on your student profile.")

    # Informational Standard Badge
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="background: var(--md-primary); color: var(--on-primary); font-weight: 700; font-size: 0.82rem; padding: 4px 10px; border-radius: 6px;">
                Class {class_level} · Science
            </span>
            <span style="font-size: 0.8rem; color: var(--on-surface-variant);">
                (Active Standard — Modify in Profile Settings)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    swat = get_student_swat(student_id, class_level=class_level)
    history = quiz_repository.get_student_history(
        student_id, class_level=class_level, include_questions=True
    )

    if not swat.get("has_data"):
        st.info(
            f"No quiz attempts recorded yet for Class {class_level}. Take a quiz in the Practice Quiz module to view your mastery data."
        )
        return

    # Top Metrics Grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Overall Average", f"{swat['overall']['average']}%")
    with m2:
        render_metric_card("Overall Accuracy", f"{swat['overall']['accuracy']}%")
    with m3:
        attempted_chs = swat["overall"].get("attempted_chapters", 0)
        total_chs = swat["overall"].get("total_chapters", 13)
        render_metric_card("Chapters Covered", f"{attempted_chs}/{total_chs}")
    with m4:
        render_metric_card("Quizzes Taken", swat["overall"]["quizzes_attempted"])

    st.write("")

    # Trend & Highlights
    h1, h2 = st.columns([1.5, 2])
    with h1:
        if swat["strong"]:
            top_s = swat["strong"][0]
            st.success(
                f"Top Strength: {top_s['chapter']} ({top_s['score']}%)"
            )
        elif swat["weak"]:
            top_w = swat["weak"][0]
            st.warning(
                f"Needs Focus: {top_w['chapter']} ({top_w['score']}%)"
            )
    with h2:
        trend = swat.get("trend", {})
        dir_str = (
            "Improving"
            if trend.get("direction") == "improving"
            else ("Declining" if trend.get("direction") == "declining" else "Stable")
        )
        recent_avg = trend.get("recent_average", swat["overall"]["average"])
        st.info(f"Performance Trend: {dir_str} (Recent: {recent_avg}%)")

    st.write("")

    # Recommended Action Plan (Phases 15, 16, 17, 18, 19)
    plan = generate_action_plan(student_id, class_level=class_level)
    if plan.get("actions"):
        st.markdown(f"#### 📋 YOUR ACTION PLAN — Class {class_level} · Science")
        st.caption(
            "Targeted recommendations based on your performance. "
            "*(These are recommendations, not forced sequencing — you can practice any chapter anytime.)*"
        )

        top_actions = plan["actions"][:3]
        act_cols = st.columns(len(top_actions))
        for idx, (col, act) in enumerate(zip(act_cols, top_actions)):
            with col:
                p_badge = act.get("priority_icon", "⚪")
                p_label = act.get("priority_label", "RECOMMENDATION")
                score_str = f"Score: {act['score']}%" if act["score"] is not None else "Not attempted yet"
                ch_title = (
                    f"Ch {act['chapter_number']}: {act['chapter']}"
                    if act.get("chapter_number")
                    else act["chapter"]
                )

                st.markdown(
                    f"""
                    <div style="background: var(--surface-container); border-radius: 10px; padding: 14px; margin-bottom: 12px; border-top: 3px solid var(--md-primary);">
                        <div style="font-size: 0.8rem; font-weight: 700; color: var(--md-primary); margin-bottom: 4px;">{p_badge} {p_label}</div>
                        <div style="font-size: 1.0rem; font-weight: 700; color: var(--on-surface); margin-bottom: 2px;">{ch_title}</div>
                        <div style="font-size: 0.88rem; color: var(--md-secondary); font-weight: 600; margin-bottom: 6px;">{score_str}</div>
                        <div style="font-size: 0.82rem; color: var(--on-surface-variant); min-height: 42px; margin-bottom: 8px;">{act['reason']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                btn_key = f"action_plan_btn_{idx}_{act['chapter']}"
                btn_type = "primary" if act["priority_rank"] == 1 else "secondary"
                if st.button(
                    f"👉 {act['button_text']}",
                    key=btn_key,
                    type=btn_type,
                    use_container_width=True,
                ):
                    st.session_state.selected_chapter = act["chapter"]
                    st.session_state.quiz_difficulty = act["difficulty"]
                    navigate_to("quiz")
                    st.rerun()

        st.write("")

    # 4-Column Mastery Breakdown
    st.markdown("#### Mastery by Chapter")
    col_str, col_avg, col_weak, col_unatt = st.columns(4)

    with col_str:
        st.markdown("🟢 **Strong (≥ 70%)**")
        if swat["strong"]:
            for item in swat["strong"]:
                ch_num = f"Ch {item.get('chapter_number', '')}: " if item.get("chapter_number") else ""
                perf = f" ({item['recent_performance']})" if item.get("attempts", 1) > 1 else ""
                st.success(f"{ch_num}{item['chapter']} — {item['score']}%{perf}")
        else:
            st.caption("No strong chapters yet.")

    with col_avg:
        st.markdown("🟡 **Average (50%–69%)**")
        if swat["average"]:
            for item in swat["average"]:
                ch_num = f"Ch {item.get('chapter_number', '')}: " if item.get("chapter_number") else ""
                perf = f" ({item['recent_performance']})" if item.get("attempts", 1) > 1 else ""
                st.info(f"{ch_num}{item['chapter']} — {item['score']}%{perf}")
        else:
            st.caption("No average topics.")

    with col_weak:
        st.markdown("🔴 **Weak (< 50%)**")
        if swat["weak"]:
            for item in swat["weak"]:
                ch_num = f"Ch {item.get('chapter_number', '')}: " if item.get("chapter_number") else ""
                perf = f" ({item['recent_performance']})" if item.get("attempts", 1) > 1 else ""
                st.error(f"{ch_num}{item['chapter']} — {item['score']}%{perf}")
        else:
            st.caption("No weak topics.")

    with col_unatt:
        st.markdown("⚪ **Not Attempted**")
        unatt = swat.get("unattempted", [])
        if unatt:
            for item in unatt:
                ch_num = f"Ch {item.get('chapter_number', '')}: " if item.get("chapter_number") else ""
                st.markdown(f"- {ch_num}{item['chapter']}")
        else:
            st.caption("All curriculum chapters attempted!")

    st.write("")

    # Quiz History
    st.markdown("#### Quiz History")
    if history:
        for q in reversed(history[-5:]):
            score_pct = (
                round((q["score"] / q["total_questions"]) * 100, 1) if q["total_questions"] else 0
            )
            with st.expander(
                f"Ch {q['chapter']} | Score: {q['score']}/{q['total_questions']} ({score_pct}%) | {q['timestamp'][:16]}"
            ):
                for idx, item in enumerate(q.get("questions_data", []), 1):
                    user_ans = item.get("user_answer", "None")
                    correct_ans = item.get("correct_answer", "")
                    status = "Correct" if item.get("is_correct") else "Incorrect"
                    st.markdown(f"**Q{idx}: {item.get('question', '')}**")
                    st.markdown(
                        f"Your answer: `{user_ans}` | Correct: `{correct_ans}` — *{status}*"
                    )
                    if item.get("explanation"):
                        st.caption(f"Explanation: {item['explanation']}")
                    st.write("")
    else:
        st.caption("No quiz history available.")
