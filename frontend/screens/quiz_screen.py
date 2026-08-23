"""Practice Quiz Screen with instant grading, Material icons, and SWAT integration."""

import logging

import streamlit as st

from frontend.components.cards import render_citation_box
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level
from src.academic_rag.analytics.swat import get_available_chapters
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.quiz.generator import create_student_quiz

logger = logging.getLogger(__name__)


def render_quiz_screen(student_id: str, user_api_key: str, selected_model: str) -> None:
    """Renders the Practice Quiz screen with single master profile standard."""
    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("quiz")

    class_level = get_student_class_level()

    st.write("")
    st.markdown(f"### NCERT Practice Quiz — Class {class_level}")
    st.caption(
        f"Generate curriculum-aligned practice quizzes for **Class {class_level} Science** *(based on your student profile)*."
    )
    st.write("")

    # Controls Grid (Phase 6: Chapter, Difficulty, Question Count)
    c1, c2, c3 = st.columns([3.0, 1.2, 1.2])

    with c1:
        available_chs = get_available_chapters(class_level, student_id=student_id)
        ch_display_map = {}
        ch_labels = []
        for ch in available_chs:
            status_tag = f"[{ch['status'].upper()}]" if ch["status"] != "unattempted" else "[NEW]"
            badge = f" ({ch['score']}%)" if ch["score"] is not None else ""
            label = f"{status_tag} Ch {ch['chapter_number']}: {ch['chapter']}{badge}"
            ch_display_map[label] = ch["chapter"]
            ch_labels.append(label)

        # Pre-selection if student clicked an action plan recommendation
        default_ch = st.session_state.get("selected_chapter")
        default_idx = 0
        if default_ch:
            for idx, lbl in enumerate(ch_labels):
                if default_ch in lbl:
                    default_idx = idx
                    break

        selected_ch_label = st.selectbox(
            "Select Chapter", ch_labels, index=default_idx, key="screen_quiz_ch"
        )
        selected_ch_title = ch_display_map.get(
            selected_ch_label,
            available_chs[0]["chapter"] if available_chs else "Chemical Reactions and Equations",
        )

    with c2:
        default_diff = st.session_state.get("quiz_difficulty", "medium").lower()
        diff_opts = ["medium", "easy", "hard"]
        diff_idx = diff_opts.index(default_diff) if default_diff in diff_opts else 0
        quiz_diff = st.selectbox("Difficulty", diff_opts, index=diff_idx, key="screen_quiz_diff")

    with c3:
        quiz_count = st.selectbox("Questions", [5, 3, 7, 10], index=0, key="screen_quiz_count")

    if st.button(
        "Generate NCERT Quiz",
        icon=":material/auto_awesome:",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner(
            f"Generating {quiz_count}-question {quiz_diff} quiz for {selected_ch_title} (Class {class_level})..."
        ):
            try:
                from src.academic_rag.exceptions import (
                    GeminiAuthError,
                    GeminiConfigurationError,
                    GeminiQuotaExhaustedError,
                )

                generated = create_student_quiz(
                    student_id=student_id,
                    chapter=selected_ch_title,
                    class_level=class_level,
                    num_questions=quiz_count,
                    difficulty=quiz_diff,
                    api_key=user_api_key,
                    model=selected_model,
                )
                st.session_state.current_quiz = generated
                st.session_state.quiz_submitted = False
                st.session_state.quiz_user_answers = {}
                st.session_state.last_submission_result = None
                st.rerun()
            except GeminiQuotaExhaustedError:
                st.warning(
                    "**AI service temporarily unavailable**\n\n"
                    "The configured AI service has reached its current usage limit. "
                    "You can add your own Gemini API key in Settings to continue."
                )
                from frontend.state import navigate_to

                if st.button("Open Settings", icon=":material/settings:", key="quiz_quota_open_settings_btn"):
                    navigate_to("settings")
                    st.rerun()
            except (GeminiAuthError, GeminiConfigurationError) as auth_err:
                st.error(f"**Authentication Error:** {auth_err}")
                from frontend.state import navigate_to

                if st.button("Configure API Key in Settings", icon=":material/key:", key="quiz_auth_open_settings_btn"):
                    navigate_to("settings")
                    st.rerun()
            except Exception as e:
                logger.error(f"Quiz generation failed: {e}")
                st.error(f"Quiz generation failed: {e}")

    # Active Quiz Display
    curr_quiz = st.session_state.get("current_quiz")
    if curr_quiz and curr_quiz.get("questions"):
        st.write("")
        st.markdown(
            f"#### {curr_quiz.get('chapter', 'Chapter')} Quiz — Class {curr_quiz.get('class_level', 10)}"
        )
        st.caption(
            f"Difficulty: {curr_quiz.get('difficulty', 'medium').capitalize()} | Questions: {len(curr_quiz['questions'])}"
        )

        is_submitted = st.session_state.get("quiz_submitted", False)
        user_answers = {}

        for idx, q_data in enumerate(curr_quiz["questions"], start=1):
            st.markdown(f"**Question {idx}:** {q_data['question']}")

            raw_options = q_data.get("options", [])
            opt_labels = []
            opt_map = {}
            letters = ["A", "B", "C", "D"]

            if isinstance(raw_options, dict):
                for k, v in raw_options.items():
                    k_clean = str(k).strip().upper()
                    label = f"{k_clean}) {v}" if not str(v).startswith(f"{k_clean}") else str(v)
                    opt_labels.append(label)
                    opt_map[label] = k_clean
            elif isinstance(raw_options, list):
                for i, opt in enumerate(raw_options):
                    def_letter = letters[i] if i < len(letters) else str(i + 1)
                    opt_str = str(opt).strip()
                    if (
                        len(opt_str) >= 2
                        and opt_str[0].upper() in letters
                        and opt_str[1] in [")", ".", ":", " "]
                    ):
                        detected_letter = opt_str[0].upper()
                        label = opt_str
                        opt_labels.append(label)
                        opt_map[label] = detected_letter
                    else:
                        label = f"{def_letter}) {opt_str}"
                        opt_labels.append(label)
                        opt_map[label] = def_letter

            saved_ans = st.session_state.get("quiz_user_answers", {}).get(str(idx))
            saved_idx = None
            if saved_ans:
                for o_i, lbl in enumerate(opt_labels):
                    if opt_map.get(lbl) == saved_ans or lbl == saved_ans:
                        saved_idx = o_i
                        break

            chosen = st.radio(
                f"Select answer for Q{idx}",
                opt_labels,
                index=saved_idx,
                key=f"q_radio_{idx}",
                disabled=is_submitted,
                label_visibility="collapsed",
            )

            if chosen:
                chosen_letter = opt_map.get(
                    chosen, chosen.split(")")[0].split(".")[0].strip().upper()
                )
                user_answers[str(idx)] = chosen_letter

            if is_submitted:
                correct_letter = str(q_data.get("correct_answer", "")).strip().upper()
                if len(correct_letter) > 1 and correct_letter.startswith(("A", "B", "C", "D")):
                    correct_letter = correct_letter[0]
                student_choice = user_answers.get(str(idx), "")

                if student_choice == correct_letter:
                    st.success(f"Correct! Option {correct_letter}")
                else:
                    st.error(
                        f"Incorrect. Your answer: Option {student_choice or 'None'} | Correct answer: Option {correct_letter}"
                    )

                with st.expander(f"Explanation & NCERT Citations (Q{idx})", expanded=True):
                    exp_text = q_data.get("explanation", "Refer to NCERT textbook.")
                    st.markdown(f"**Explanation:** {exp_text}")

                    sp = (
                        q_data.get("source_pages")
                        or q_data.get("source_page")
                        or q_data.get("pages")
                    )
                    if not sp:
                        import re

                        exp_pages = re.findall(
                            r"(?:\[PAGE:\s*|page\s+|pages\s+|p\.\s*)(\d+)",
                            str(exp_text),
                            re.IGNORECASE,
                        )
                        if exp_pages:
                            sp = [int(p) for p in exp_pages]

                    render_citation_box(
                        chapter=curr_quiz.get("chapter", ""),
                        class_level=curr_quiz.get("class_level", 10),
                        pages=sp,
                    )

            st.write("")

        st.session_state.quiz_user_answers = user_answers

        if not is_submitted:
            if st.button(
                "Submit Quiz",
                icon=":material/check_circle:",
                type="primary",
                use_container_width=True,
            ):
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

            st.write("")
            res_col1, res_col2 = st.columns([2.5, 1])
            with res_col1:
                if pct >= 70:
                    st.success(f"Score: {correct_count}/{total_q} ({pct}%) — Mastery standard met.")
                elif pct >= 50:
                    st.info(
                        f"Score: {correct_count}/{total_q} ({pct}%) — Satisfactory performance."
                    )
                else:
                    st.warning(
                        f"Score: {correct_count}/{total_q} ({pct}%) — Review recommended. Check textbook references above."
                    )

                if sub_res:
                    status_name = sub_res.get("new_status", "").upper()
                    if sub_res.get("status_changed"):
                        st.success(
                            f"SWAT Status Updated: {sub_res.get('status_change_summary')} [{status_name}]"
                        )
                    else:
                        st.info(
                            f"SWAT Chapter Score: {sub_res.get('chapter')} average is "
                            f"{sub_res.get('new_chapter_score')}% [{status_name}]"
                        )

            with res_col2:
                if st.button(
                    "Take Another Quiz",
                    icon=":material/replay:",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answers = {}
                    st.session_state.last_submission_result = None
                    st.rerun()
