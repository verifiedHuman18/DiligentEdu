"""Practice Quiz Screen with instant grading and SWAT integration (No Emojis)."""

import logging
import streamlit as st

from src.academic_rag.analytics.swat import get_available_chapters
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.quiz.generator import create_student_quiz
from frontend.components.cards import render_citation_box

logger = logging.getLogger(__name__)


def render_quiz_screen(student_id: str, user_api_key: str, selected_model: str) -> None:
    """Renders the Practice Quiz screen."""
    st.markdown("### NCERT Practice Quiz")
    st.caption("Generate grounded multiple-choice quizzes with instant grading, textbook explanations, and exact page citations.")

    # Controls Grid
    c1, c2, c3, c4 = st.columns([1.2, 2.4, 1.1, 1.1])

    with c1:
        quiz_grade = st.selectbox("Grade", ["Class 10", "Class 9"], key="screen_quiz_grade")
        quiz_cls_int = 10 if quiz_grade == "Class 10" else 9

    with c2:
        available_chs = get_available_chapters(quiz_cls_int, student_id=student_id)
        ch_display_map = {}
        ch_labels = []
        for ch in available_chs:
            status_tag = f"[{ch['status'].upper()}]" if ch["status"] != "unattempted" else "[NEW]"
            badge = f" ({ch['score']}%)" if ch["score"] is not None else ""
            label = f"{status_tag} Ch {ch['chapter_number']}: {ch['chapter']}{badge}"
            ch_display_map[label] = ch["chapter"]
            ch_labels.append(label)

        selected_ch_label = st.selectbox("Chapter", ch_labels, key="screen_quiz_ch")
        selected_ch_title = ch_display_map.get(selected_ch_label, available_chs[0]["chapter"] if available_chs else "Electricity")

    with c3:
        quiz_diff = st.selectbox("Difficulty", ["medium", "easy", "hard"], key="screen_quiz_diff")

    with c4:
        quiz_count = st.selectbox("Questions", [5, 3, 7, 10], index=0, key="screen_quiz_count")

    if st.button("Generate NCERT Quiz", type="primary", use_container_width=True):
        if not user_api_key:
            st.warning("Please enter your Google Gemini API key in the sidebar.")
        else:
            with st.spinner(f"Generating {quiz_count}-question {quiz_diff} quiz for {selected_ch_title}..."):
                try:
                    generated = create_student_quiz(
                        student_id=student_id,
                        class_level=quiz_cls_int,
                        chapter=selected_ch_title,
                        difficulty=quiz_diff,
                        num_questions=quiz_count,
                        api_key=user_api_key,
                        model=selected_model,
                    )
                    st.session_state.current_quiz = generated
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answers = {}
                    st.session_state.last_submission_result = None
                    st.rerun()
                except Exception as e:
                    logger.error(f"Quiz generation error: {e}")
                    st.error(f"Quiz generation error: {e}")

    # Active Quiz Display
    curr_quiz = st.session_state.get("current_quiz")
    if curr_quiz and "questions" in curr_quiz:
        st.divider()
        st.markdown(f"#### Quiz: Class {curr_quiz.get('class_level')} Science — {curr_quiz.get('chapter')}")
        st.caption(
            f"Difficulty: {curr_quiz.get('difficulty', '').upper()} | "
            f"Total Questions: {curr_quiz.get('total_questions', len(curr_quiz['questions']))} | "
            f"Student: {student_id}"
        )

        user_answers = st.session_state.get("quiz_user_answers", {})
        is_submitted = st.session_state.get("quiz_submitted", False)

        for idx, q_data in enumerate(curr_quiz["questions"], 1):
            st.markdown(f"**Q{idx}. {q_data['question']}**")
            options = q_data.get("options", [])
            choice_key = f"q_choice_{idx}"
            current_val = user_answers.get(choice_key, None)

            if not is_submitted:
                selected_opt = st.radio(
                    f"Options for Q{idx}:",
                    options,
                    key=choice_key,
                    index=options.index(current_val) if current_val in options else None,
                    label_visibility="collapsed",
                )
                user_answers[choice_key] = selected_opt
            else:
                user_ans_text = user_answers.get(choice_key)
                correct_key = q_data.get("correct_answer", "A").upper()
                correct_opt_text = next(
                    (o for o in options if o.startswith(f"{correct_key})") or o.startswith(f"{correct_key}.")),
                    options[0] if options else "",
                )

                is_correct = user_ans_text and user_ans_text.startswith(f"{correct_key}")
                if is_correct:
                    st.success(f"Correct. Your Answer: {user_ans_text}")
                else:
                    st.error(f"Incorrect. Your Answer: {user_ans_text or 'No answer selected'}  \nCorrect Answer: {correct_opt_text}")

                with st.expander(f"Explanation and NCERT Citations (Q{idx})", expanded=True):
                    st.markdown(f"**Explanation:** {q_data.get('explanation', 'Refer to NCERT textbook.')}")
                    sp = q_data.get("source_pages", [])
                    render_citation_box(
                        chapter=curr_quiz.get('chapter', ''),
                        class_level=curr_quiz.get('class_level', 10),
                        pages=sp,
                    )

            st.write("")

        st.session_state.quiz_user_answers = user_answers

        if not is_submitted:
            if st.button("Submit Quiz", type="primary", use_container_width=True):
                try:
                    sub_result = submit_and_grade_quiz(
                        student_id=student_id,
                        quiz_id=curr_quiz.get("quiz_id"),
                        user_answers=user_answers,
                        quiz_data=curr_quiz,
                    )
                    st.session_state.last_submission_result = sub_result
                except Exception as e:
                    logger.error(f"Failed to submit quiz: {e}")
                    st.error(f"Submission error: {e}")

                st.session_state.quiz_submitted = True
                st.rerun()
        else:
            sub_res = st.session_state.get("last_submission_result", {})
            correct_count = sub_res.get("score", 0)
            total_q = sub_res.get("total", len(curr_quiz["questions"]))
            pct = sub_res.get("percentage", 0)

            st.divider()
            res_col1, res_col2 = st.columns([2.5, 1])
            with res_col1:
                if pct >= 70:
                    st.success(f"Score: {correct_count}/{total_q} ({pct}%) — Mastery standard met.")
                elif pct >= 50:
                    st.info(f"Score: {correct_count}/{total_q} ({pct}%) — Satisfactory performance.")
                else:
                    st.warning(f"Score: {correct_count}/{total_q} ({pct}%) — Review recommended. Check textbook references above.")

                if sub_res:
                    status_name = sub_res.get("new_status", "").upper()
                    if sub_res.get("status_changed"):
                        st.success(f"SWAT Status Updated: {sub_res.get('status_change_summary')} [{status_name}]")
                    else:
                        st.info(
                            f"SWAT Chapter Score: {sub_res.get('chapter')} average is "
                            f"{sub_res.get('new_chapter_score')}% [{status_name}]"
                        )

            with res_col2:
                if st.button("Take Another Quiz", type="primary", use_container_width=True):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answers = {}
                    st.session_state.last_submission_result = None
                    st.rerun()
