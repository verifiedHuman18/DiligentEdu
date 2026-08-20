"""Student SWAT Dashboard Screen (No Emojis)."""

import streamlit as st
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.repository import quiz_repository
from frontend.components.cards import render_metric_card


def render_swat_screen(student_id: str) -> None:
    """Renders the Student SWAT Analysis dashboard."""
    st.markdown(f"### Student SWAT Analysis ({student_id})")
    st.caption("Descriptive chapter-wise mastery analysis to help you target your study focus.")

    swat = get_student_swat(student_id)
    history = quiz_repository.get_student_history(student_id, include_questions=True)

    if not swat.get("has_data"):
        st.info("No quiz attempts recorded yet. Take a quiz in the Practice Quiz tab to view your mastery data.")
        return

    # Top Metrics Grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Overall Average", f"{swat['overall']['average']}%")
    with m2:
        render_metric_card("Questions Attempted", swat["overall"]["total_questions"])
    with m3:
        render_metric_card("Questions Correct", swat["overall"]["total_correct"])
    with m4:
        render_metric_card("Quizzes Taken", swat["overall"]["quizzes_attempted"])

    st.write("")

    # Trend & Highlights
    h1, h2 = st.columns([1.5, 2])
    with h1:
        if swat["strengths"]:
            st.success(f"Top Strength: {swat['strengths'][0]['chapter']} ({swat['strengths'][0]['score']}%)")
        elif swat["weak_topics"]:
            st.warning(f"Needs Focus: {swat['weak_topics'][0]['chapter']} ({swat['weak_topics'][0]['score']}%)")
    with h2:
        trend = swat.get("trend", {})
        st.info(f"Recent Trend ({trend.get('direction', '—').upper()}): {trend.get('summary', 'Steady')}")

    st.divider()

    # SWAT 3-Column Breakdown
    st.markdown("#### Chapter-Wise Mastery Breakdown")
    st.caption("STRONG (>= 70%) | AVERAGE (50%–69%) | WEAK (< 50%)")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("##### STRONG")
        strong_items = swat.get("strengths", [])
        if strong_items:
            for item in strong_items:
                st.success(
                    f"**{item['chapter']}**  \nScore: {item['score']}% "
                    f"({item.get('correct', 0)}/{item.get('questions', 0)} Qs across "
                    f"{item['attempts']} quiz{'zes' if item['attempts'] > 1 else ''})"
                )
        else:
            st.caption("No chapters currently in Strong.")

    with c2:
        st.markdown("##### AVERAGE")
        avg_items = swat.get("average_topics", [])
        if avg_items:
            for item in avg_items:
                st.info(
                    f"**{item['chapter']}**  \nScore: {item['score']}% "
                    f"({item.get('correct', 0)}/{item.get('questions', 0)} Qs across "
                    f"{item['attempts']} quiz{'zes' if item['attempts'] > 1 else ''})"
                )
        else:
            st.caption("No chapters currently in Average.")

    with c3:
        st.markdown("##### WEAK")
        weak_items = swat.get("weak_topics", [])
        if weak_items:
            for item in weak_items:
                st.error(
                    f"**{item['chapter']}**  \nScore: {item['score']}% "
                    f"({item.get('correct', 0)}/{item.get('questions', 0)} Qs across "
                    f"{item['attempts']} quiz{'zes' if item['attempts'] > 1 else ''})"
                )
        else:
            st.caption("No weak chapters identified.")

    st.divider()

    # Timeline History
    st.markdown("#### Detailed Quiz History")
    for att in reversed(history):
        with st.expander(
            f"{att['timestamp'][:19].replace('T', ' ')} | Class {att['class_level']} — {att['chapter']} | "
            f"{att['percentage']:.0f}% ({att['score']}/{att['total_questions']})",
            expanded=False,
        ):
            st.markdown(f"Quiz ID: `{att['quiz_id']}` | Difficulty: `{att['difficulty'].upper()}`")
            if "questions" in att and att["questions"]:
                for q_idx, q_rec in enumerate(att["questions"], 1):
                    q_status = "[Correct]" if q_rec["is_correct"] else "[Incorrect]"
                    st.markdown(f"{q_status} **Q{q_idx}:** {q_rec['question_text']}")
                    st.caption(f"Your answer: {q_rec['user_answer']} | Correct: {q_rec['correct_answer']}")

    if st.button("Clear Quiz History", type="secondary"):
        quiz_repository.clear_student_data(student_id)
        st.rerun()
