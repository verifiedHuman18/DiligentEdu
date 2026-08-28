"""Student Analytics Dashboard Screen with Material Icons (No Emojis, No SWAT Acronym)."""

from typing import Optional

import streamlit as st

from frontend.components.cards import render_metric_card, render_swat_columns
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.repository import quiz_repository


def render_swat_screen(student_id: str, selected_class: Optional[str] = None) -> None:
    """Renders the Student Analytics and SWAT dashboard strictly bound to master profile class and subject."""
    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("swat")

    from frontend.state import get_student_subject
    class_level = get_student_class_level()
    subject = get_student_subject()

    st.write("")
    st.markdown(f"### Performance & Topic Mastery — Class {class_level} · {subject}")
    st.caption(
        f"Comprehensive SWAT analysis and chapter-wise mastery based on your Class {class_level} {subject} profile."
    )

    swat = get_student_swat(student_id, class_level=class_level, subject=subject)
    history = quiz_repository.get_student_history(
        student_id, class_level=class_level, subject=subject, include_questions=True
    )

    if not swat.get("has_data"):
        st.info(
            f"No quiz attempts recorded yet for Class {class_level} {subject}. Take a quiz in the Practice Quiz module to view your mastery data."
        )
        return

    # SECTION 1: Top Metrics Grid & Trajectory
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Lifetime Aggregate Metrics</h4>
                <div class="section-subtitle-text">Average scores, overall question accuracy, and syllabus coverage.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
            st.success(f"Top Strength: {top_s['chapter']} ({top_s['score']}%)")
        elif swat["weak"]:
            top_w = swat["weak"][0]
            st.warning(f"Needs Focus: {top_w['chapter']} ({top_w['score']}%)")
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
    st.write("")

    # SECTION 2: 4-Column Mastery Breakdown
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Chapter Mastery Breakdown</h4>
                <div class="section-subtitle-text">4-category matrix categorizing chapters by performance score and attempt frequency.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_swat_columns(swat)

    st.write("")
    st.write("")

    # SECTION 3: Quiz History
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Chronological Quiz History</h4>
                <div class="section-subtitle-text">Detailed breakdown of questions, student answers, and correct answers.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if history:
        for q in reversed(history[-5:]):
            score_pct = (
                round((q["score"] / q["total_questions"]) * 100, 1) if q["total_questions"] else 0
            )
            with st.expander(
                f"Ch {q['chapter']} | Score: {q['score']}/{q['total_questions']} ({score_pct}%) | {q['timestamp'][:16]}",
                icon=":material/history_edu:",
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
