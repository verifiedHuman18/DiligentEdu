"""Student Analytics Dashboard Screen with Material Icons (No Emojis, No SWAT Acronym)."""

import streamlit as st
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.repository import quiz_repository
from frontend.components.cards import render_metric_card
from frontend.state import navigate_to


def render_swat_screen(student_id: str) -> None:
    """Renders the Student Analytics dashboard."""
    if st.button("Back to Home", icon=":material/arrow_back:", type="secondary", key="swat_top_back_btn"):
        navigate_to("home")
        st.rerun()

    st.write("")
    st.markdown(f"### Student Analytics ({student_id})")
    st.caption("Chapter-wise mastery analysis to help you target your study focus.")

    swat = get_student_swat(student_id)
    history = quiz_repository.get_student_history(student_id, include_questions=True)

    if not swat.get("has_data"):
        st.info("No quiz attempts recorded yet. Take a quiz in the Practice Quiz module to view your mastery data.")
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
        if trend.get("has_trend"):
            dir_str = "Improving" if trend["direction"] == "improving" else ("Declining" if trend["direction"] == "declining" else "Stable")
            st.info(f"Performance Trend: {dir_str} (Last 5: {trend['recent_average']}%)")

    st.write("")

    # 3-Column Mastery Breakdown
    st.markdown("#### Mastery by Chapter")
    col_str, col_avg, col_weak = st.columns(3)

    with col_str:
        st.markdown("**Mastered Topics (>= 75%)**")
        if swat["strengths"]:
            for item in swat["strengths"]:
                st.success(f"Ch {item.get('chapter_number', '')} {item['chapter']} — {item['score']}%")
        else:
            st.caption("No mastered chapters yet.")

    with col_avg:
        st.markdown("**In Progress (50% - 74%)**")
        if swat["average_topics"]:
            for item in swat["average_topics"]:
                st.info(f"Ch {item.get('chapter_number', '')} {item['chapter']} — {item['score']}%")
        else:
            st.caption("No topics currently in progress.")

    with col_weak:
        st.markdown("**Needs Review (< 50%)**")
        if swat["weak_topics"]:
            for item in swat["weak_topics"]:
                st.error(f"Ch {item.get('chapter_number', '')} {item['chapter']} — {item['score']}%")
        else:
            st.caption("No weak topics identified.")

    st.write("")

    # Quiz History
    st.markdown("#### Quiz History")
    if history:
        for q in reversed(history[-5:]):
            score_pct = round((q["score"] / q["total_questions"]) * 100, 1) if q["total_questions"] else 0
            with st.expander(f"Ch {q['chapter']} | Score: {q['score']}/{q['total_questions']} ({score_pct}%) | {q['timestamp'][:16]}"):
                for idx, item in enumerate(q.get("questions_data", []), 1):
                    user_ans = item.get("user_answer", "None")
                    correct_ans = item.get("correct_answer", "")
                    status = "Correct" if item.get("is_correct") else "Incorrect"
                    st.markdown(f"**Q{idx}: {item.get('question', '')}**")
                    st.markdown(f"Your answer: `{user_ans}` | Correct: `{correct_ans}` — *{status}*")
                    if item.get("explanation"):
                        st.caption(f"Explanation: {item['explanation']}")
                    st.write("")
    else:
        st.caption("No quiz history available.")
