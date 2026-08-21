"""Student SWAT Dashboard UI component."""

import streamlit as st

from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.repository import quiz_repository


def render_swat_tab(student_id: str):
    """Renders the descriptive Student SWAT Analysis dashboard and attempt history."""
    st.markdown(f"### 📊 Student SWAT Analysis (`{student_id}`)")
    st.caption(
        "Descriptive chapter-wise performance analysis. Identifies your strengths, average areas, "
        "and weaknesses so you can decide your own study focus."
    )

    swat = get_student_swat(student_id)
    history = quiz_repository.get_student_history(student_id, include_questions=True)

    if not swat.get("has_data"):
        st.info(
            "ℹ️ No quiz attempts recorded yet for this student ID. Complete a quiz in the "
            "**📝 Practice Quiz** tab to view your performance data."
        )
        return

    # Top metrics
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Overall Average", f"{swat['overall']['average']}%")
    m_col2.metric("Questions Attempted", swat["overall"]["total_questions"])
    m_col3.metric("Questions Correct", swat["overall"]["total_correct"])
    m_col4.metric("Quizzes Completed", swat["overall"]["quizzes_attempted"])

    st.divider()

    # Key Highlights: Trend
    h_col1, h_col2 = st.columns([1.5, 2])
    with h_col1:
        if swat["strengths"]:
            st.success(
                f"🏆 **Top Strength:** {swat['strengths'][0]['chapter']} (**{swat['strengths'][0]['score']}%**)"
            )
        elif swat["weak_topics"]:
            st.warning(
                f"🔍 **Needs Focus:** {swat['weak_topics'][0]['chapter']} (**{swat['weak_topics'][0]['score']}%**)"
            )
    with h_col2:
        trend = swat.get("trend", {})
        st.info(
            f"📈 **Recent Trend ({trend.get('direction', '—').upper()}):** {trend.get('summary', 'Steady')}"
        )

    st.divider()

    # SWAT Categorization
    st.markdown("#### 🎯 Chapter-Wise SWAT Breakdown")
    st.caption("🟢 **STRONG** (≥ 70%) | 🟡 **AVERAGE** (50%–69%) | 🔴 **WEAK** (< 50%)")

    c_col1, c_col2, c_col3 = st.columns(3)

    with c_col1:
        st.markdown("##### 🟢 STRONG")
        strong_items = swat["strengths"]
        if strong_items:
            for item in strong_items:
                st.success(
                    f"**{item['chapter']}**  \nScore: **{item['score']}%** "
                    f"({item.get('correct', 0)}/{item.get('questions', 0)} Qs in "
                    f"{item['attempts']} quiz{'zes' if item['attempts'] > 1 else ''})"
                )
        else:
            st.caption("No chapters currently in Strong.")

    with c_col2:
        st.markdown("##### 🟡 AVERAGE")
        avg_items = swat["average_topics"]
        if avg_items:
            for item in avg_items:
                st.info(
                    f"**{item['chapter']}**  \nScore: **{item['score']}%** "
                    f"({item.get('correct', 0)}/{item.get('questions', 0)} Qs in "
                    f"{item['attempts']} quiz{'zes' if item['attempts'] > 1 else ''})"
                )
        else:
            st.caption("No chapters currently in Average.")

    with c_col3:
        st.markdown("##### 🔴 WEAK")
        weak_items = swat["weak_topics"]
        if weak_items:
            for item in weak_items:
                st.warning(
                    f"**{item['chapter']}**  \nScore: **{item['score']}%** "
                    f"({item.get('correct', 0)}/{item.get('questions', 0)} Qs in "
                    f"{item['attempts']} quiz{'zes' if item['attempts'] > 1 else ''})"
                )
        else:
            st.caption("No weak chapters identified!")

    st.divider()

    # Full Detailed Timeline
    st.markdown("#### 🕒 Detailed Quiz History Timeline")
    for att in reversed(history):
        with st.expander(
            f"🗓️ {att['timestamp'][:19].replace('T', ' ')} | Class {att['class_level']} — {att['chapter']} | "
            f"{att['percentage']:.0f}% ({att['score']}/{att['total_questions']})",
            expanded=False,
        ):
            st.markdown(
                f"**Quiz ID:** `{att['quiz_id']}` | **Difficulty:** `{att['difficulty'].upper()}`"
            )
            if "questions" in att and att["questions"]:
                for q_idx, q_rec in enumerate(att["questions"], 1):
                    q_icon = "✅" if q_rec["is_correct"] else "❌"
                    st.markdown(f"{q_icon} **Q{q_idx}:** {q_rec['question_text']}")
                    st.caption(
                        f"Your answer: `{q_rec['user_answer']}` | Correct: `{q_rec['correct_answer']}`"
                    )

    if st.button("🗑️ Clear My Quiz History", type="secondary"):
        quiz_repository.clear_student_data(student_id)
        st.rerun()
