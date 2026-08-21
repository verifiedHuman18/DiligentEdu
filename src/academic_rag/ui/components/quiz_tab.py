"""Practice Quiz Tab UI component with instant grading and SWAT delta display."""

import logging

import streamlit as st

from src.academic_rag.analytics.swat import get_available_chapters
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.quiz.generator import create_student_quiz

logger = logging.getLogger(__name__)


def render_quiz_tab(student_id: str, user_api_key: str, selected_model: str):
    """Renders the Practice Quiz configuration, taking, and submission interface."""
    st.markdown("### 📝 NCERT Science Practice Quiz")
    st.caption(
        "Generate grounded, multiple-choice quizzes with instant grading, textbook explanations, "
        "and exact page citations in **1 single Gemini request**."
    )

    q_col1, q_col2, q_col3, q_col4 = st.columns([1.2, 2.4, 1.1, 1.1])

    with q_col1:
        quiz_grade = st.selectbox("Grade", ["Class 10", "Class 9"], key="quiz_grade_sel")
        quiz_cls_int = 10 if quiz_grade == "Class 10" else 9

    with q_col2:
        available_chs = get_available_chapters(quiz_cls_int, student_id=student_id)
        ch_display_map = {}
        ch_labels = []
        for ch in available_chs:
            icon = (
                "🟢"
                if ch["status"] == "strong"
                else (
                    "🟡"
                    if ch["status"] == "average"
                    else ("🔴" if ch["status"] == "weak" else "⚪")
                )
            )
            badge = f" ({ch['score']}%)" if ch["score"] is not None else " (New)"
            label = f"{icon} Ch {ch['chapter_number']}: {ch['chapter']}{badge}"
            ch_display_map[label] = ch["chapter"]
            ch_labels.append(label)

        selected_ch_label = st.selectbox(
            "Chapter (Freely Choose Any)", ch_labels, key="quiz_ch_sel"
        )
        selected_ch_title = ch_display_map.get(
            selected_ch_label, available_chs[0]["chapter"] if available_chs else "Electricity"
        )

    with q_col3:
        quiz_diff = st.selectbox("Difficulty", ["medium", "easy", "hard"], key="quiz_diff_sel")

    with q_col4:
        quiz_count = st.selectbox("Questions", [5, 3, 7, 10], index=0, key="quiz_count_sel")

    if st.button("⚡ Generate NCERT Quiz", type="primary", use_container_width=True):
        if not user_api_key:
            st.warning("👈 Please enter your Google Gemini API key in the sidebar.")
        else:
            with st.spinner(
                f"Generating {quiz_count}-question {quiz_diff} quiz for {selected_ch_title} from NCERT in 1 request..."
            ):
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
                    st.rerun()
                except Exception as e:
                    st.error(f"Quiz generation error: {e}")

    # Render active quiz
    curr_quiz = st.session_state.get("current_quiz")
    if curr_quiz and "questions" in curr_quiz:
        st.divider()
        st.markdown(
            f"#### 📖 Quiz: Class {curr_quiz.get('class_level')} Science — {curr_quiz.get('chapter')}"
        )
        st.caption(
            f"Difficulty: **{curr_quiz.get('difficulty', '').upper()}** | "
            f"Total Questions: **{curr_quiz.get('total_questions', len(curr_quiz['questions']))}** | "
            f"Student: `{student_id}`"
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
                    (
                        o
                        for o in options
                        if o.startswith(f"{correct_key})") or o.startswith(f"{correct_key}.")
                    ),
                    options[0] if options else "",
                )

                is_correct = user_ans_text and user_ans_text.startswith(f"{correct_key}")
                if is_correct:
                    st.success(f"✅ **Your Answer:** {user_ans_text}")
                else:
                    st.error(
                        f"❌ **Your Answer:** {user_ans_text or 'No answer selected'}  \n**Correct Answer:** {correct_opt_text}"
                    )

                with st.expander(f"💡 Explanation & NCERT Citations (Q{idx})", expanded=True):
                    st.markdown(
                        f"**Explanation:** {q_data.get('explanation', 'Refer to NCERT textbook.')}"
                    )
                    sp = q_data.get("source_pages", [])
                    sp_str = ", ".join(str(p) for p in sp) if sp else "Referenced in Chapter"
                    st.markdown(
                        f"📚 **NCERT Citation:** Class {curr_quiz.get('class_level')} Science | "
                        f"*{curr_quiz.get('chapter')}* | **Page(s): {sp_str}**"
                    )

            st.write("")

        st.session_state.quiz_user_answers = user_answers

        if not is_submitted:
            if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                try:
                    sub_result = submit_and_grade_quiz(
                        student_id=student_id,
                        quiz_id=curr_quiz.get("quiz_id"),
                        user_answers=user_answers,
                        quiz_data=curr_quiz,
                    )
                    st.session_state.last_submission_result = sub_result
                except Exception as e:
                    logger.error(f"Failed to submit and grade quiz: {e}")
                    st.error(f"Submission error: {e}")

                st.session_state.quiz_submitted = True
                st.rerun()
        else:
            sub_res = st.session_state.get("last_submission_result", {})
            correct_count = sub_res.get("score", 0)
            total_q = sub_res.get("total", len(curr_quiz["questions"]))
            pct = sub_res.get("percentage", 0)

            st.divider()

            score_col1, score_col2 = st.columns([2.5, 1])
            with score_col1:
                if pct >= 70:
                    st.success(
                        f"🎉 **Outstanding Job!** Score: **{correct_count}/{total_q}** ({pct}%)"
                    )
                elif pct >= 50:
                    st.info(f"👍 **Good Effort!** Score: **{correct_count}/{total_q}** ({pct}%)")
                else:
                    st.warning(
                        f"📖 **Needs Review:** Score: **{correct_count}/{total_q}** ({pct}%) — Review the cited pages above!"
                    )

                # Render Automatic SWAT Update Banner
                if sub_res:
                    stat_icon = (
                        "🟢"
                        if sub_res.get("new_status") == "strong"
                        else ("🟡" if sub_res.get("new_status") == "average" else "🔴")
                    )
                    if sub_res.get("status_changed"):
                        st.success(
                            f"🔄 **SWAT Updated!** {sub_res.get('status_change_summary')} {stat_icon}"
                        )
                    else:
                        st.info(
                            f"📊 **SWAT Chapter Score:** {sub_res.get('chapter')} average is "
                            f"**{sub_res.get('new_chapter_score')}%** ({sub_res.get('new_status', '').upper()} {stat_icon})"
                        )

            with score_col2:
                if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answers = {}
                    st.session_state.last_submission_result = None
                    st.rerun()
