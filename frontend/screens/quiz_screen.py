"""Practice Quiz Screen with Socrates Learning System Mode, Instant Grading, and SWAT Integration."""

import asyncio
import logging
import re
from typing import Any, Dict, List

import streamlit as st

from backend.analytics.swat import get_available_chapters
from backend.quiz.evaluator import submit_and_grade_quiz
from backend.quiz.generator import create_student_quiz
from backend.quiz.socrates import (
    enrich_quiz_with_socrates,
    generate_socrates_hints,
    generate_socrates_misconception,
    stream_socrates_dialogue,
)
from frontend.components.cards import render_citation_box
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level

logger = logging.getLogger(__name__)


def _extract_options(raw_options: Any) -> tuple[List[str], Dict[str, str]]:
    """Normalizes question options into display labels and option letters map."""
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

    return opt_labels, opt_map


async def render_quiz_screen(student_id: str, user_api_key: str, selected_model: str) -> None:
    """Renders the Practice Quiz screen with unified controls and Socrates Learning System."""
    render_back_to_home("quiz")

    from frontend.state import get_student_subject

    class_level = get_student_class_level()
    subject = get_student_subject()

    st.write("")
    st.markdown(f"### NCERT Practice Quiz — Class {class_level} · {subject}")

    # Unified Mode Switcher (Sleek side-by-side buttons)
    current_mode = st.session_state.get("quiz_mode", "socrates")
    is_socrates_mode = current_mode == "socrates"

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if is_socrates_mode:
            st.button(
                "Socrates Learning Mode (Active)",
                icon=":material/psychology:",
                type="primary",
                use_container_width=True,
                key="mode_soc_btn_active",
            )
        else:
            if st.button(
                "Switch to Socrates Mode",
                icon=":material/psychology:",
                type="secondary",
                use_container_width=True,
                key="mode_soc_btn_inactive",
            ):
                st.session_state.quiz_mode = "socrates"
                st.rerun()

    with m_col2:
        if not is_socrates_mode:
            st.button(
                "Standard Exam Mode (Active)",
                icon=":material/assignment:",
                type="primary",
                use_container_width=True,
                key="mode_std_btn_active",
            )
        else:
            if st.button(
                "Switch to Standard Mode",
                icon=":material/assignment:",
                type="secondary",
                use_container_width=True,
                key="mode_std_btn_inactive",
            ):
                st.session_state.quiz_mode = "standard"
                st.rerun()

    st.write("")

    # Controls Grid: Chapter, Difficulty, Question Count
    c1, c2, c3 = st.columns([3.0, 1.2, 1.2])

    with c1:
        available_chs = get_available_chapters(class_level, subject=subject, student_id=student_id)
        ch_display_map = {}
        ch_labels = []
        for ch in available_chs:
            status_tag = f"[{ch['status'].upper()}]" if ch["status"] != "unattempted" else "[NEW]"
            badge = f" ({ch['score']}%)" if ch["score"] is not None else ""
            label = f"{status_tag} Ch {ch['chapter_number']}: {ch['chapter']}{badge}"
            ch_display_map[label] = ch["chapter"]
            ch_labels.append(label)

        default_idx = 0
        selected_ch_label = st.selectbox(
            f"Chapter ({subject})", ch_labels, index=default_idx, key=f"screen_quiz_ch_{subject}"
        )
        selected_ch_title = ch_display_map.get(
            selected_ch_label,
            available_chs[0]["chapter"] if available_chs else "Chapter 1",
        )

    with c2:
        default_diff = st.session_state.get("quiz_difficulty", "medium").lower()
        diff_opts = ["medium", "easy", "hard"]
        diff_idx = diff_opts.index(default_diff) if default_diff in diff_opts else 0
        quiz_diff = st.selectbox("Difficulty", diff_opts, index=diff_idx, key="screen_quiz_diff")

    with c3:
        quiz_count = st.selectbox("Questions", [5, 3, 7, 10], index=0, key="screen_quiz_count")

    btn_label = "Generate Socratic Quiz" if is_socrates_mode else "Generate Standard Quiz"
    if st.button(
        btn_label,
        icon=":material/auto_awesome:",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner(
            f"Generating {quiz_count}-question {quiz_diff} quiz for {selected_ch_title} (Class {class_level} {subject})..."
        ):
            try:
                from backend.exceptions import (
                    GeminiAuthError,
                    GeminiConfigurationError,
                    GeminiQuotaExhaustedError,
                )

                generated = create_student_quiz(
                    student_id=student_id,
                    chapter=selected_ch_title,
                    class_level=class_level,
                    subject=subject,
                    num_questions=quiz_count,
                    difficulty=quiz_diff,
                    api_key=user_api_key,
                    model=selected_model,
                )
                # Enrich with Socratic hints
                generated = enrich_quiz_with_socrates(
                    generated, api_key=user_api_key, model=selected_model
                )
                st.session_state.current_quiz = generated
                st.session_state.quiz_submitted = False
                st.session_state.quiz_user_answers = {}
                st.session_state.last_submission_result = None
                st.session_state.socrates_active_q = 1
                st.session_state.socrates_hints_revealed = {}
                st.session_state.socrates_chat_history = {}
                st.session_state.socrates_attempts = {}
                st.session_state.socrates_completed = False
                st.rerun()
            except GeminiQuotaExhaustedError:
                st.warning(
                    "**AI service temporarily unavailable**\n\n"
                    "The configured AI service has reached its current usage limit. "
                    "You can add your own Gemini API key in Settings to continue."
                )
                from frontend.state import navigate_to

                if st.button(
                    "Open Settings",
                    icon=":material/settings:",
                    key="quiz_quota_open_settings_btn",
                ):
                    navigate_to("settings")
                    st.rerun()
            except (GeminiAuthError, GeminiConfigurationError) as auth_err:
                st.error(f"**Authentication Error:** {auth_err}")
                from frontend.state import navigate_to

                if st.button(
                    "Configure API Key in Settings",
                    icon=":material/key:",
                    key="quiz_auth_open_settings_btn",
                ):
                    navigate_to("settings")
                    st.rerun()
            except Exception as e:
                logger.error(f"Quiz generation failed: {e}")
                st.error(f"Quiz generation failed: {e}")

    # Active Quiz Display
    curr_quiz = st.session_state.get("current_quiz")
    if curr_quiz and curr_quiz.get("questions"):
        st.write("")
        st.divider()

        if is_socrates_mode:
            await _render_socrates_quiz_mode(
                curr_quiz=curr_quiz,
                student_id=student_id,
                user_api_key=user_api_key,
                selected_model=selected_model,
                class_level=class_level,
            )
        else:
            _render_standard_quiz_mode(
                curr_quiz=curr_quiz,
                student_id=student_id,
                class_level=class_level,
            )


def _render_socrates_completed_screen(
    curr_quiz: Dict[str, Any],
    student_id: str,
    class_level: int,
) -> None:
    """Renders the clean completed session hub when a Socratic learning quest ends."""
    chapter_name = curr_quiz.get("chapter", "Science")
    questions = curr_quiz.get("questions", [])
    total_q = len(questions)
    sub_res = st.session_state.get("last_submission_result", {})
    attempts = st.session_state.get("socrates_attempts", {})
    chat_histories = st.session_state.get("socrates_chat_history", {})

    mastered_count = sum(1 for a in attempts.values() if a.get("is_correct"))
    correct_count = sub_res.get("score", mastered_count)
    pct = sub_res.get("percentage", int(round(correct_count / total_q * 100)) if total_q > 0 else 0)

    # 1. Completion Banner
    st.success(
        f"Socratic Session Completed — {chapter_name} (Score: {correct_count}/{total_q} · {pct}%)"
    )

    if sub_res:
        status_name = sub_res.get("new_status", "").upper()
        if sub_res.get("status_changed"):
            st.info(f"SWAT Status Updated: {sub_res.get('status_change_summary')} [{status_name}]")
        else:
            st.caption(
                f"SWAT Mastery: {sub_res.get('chapter')} average is {sub_res.get('new_chapter_score')}% [{status_name}]"
            )

    st.write("")
    st.divider()

    # 2. Detailed Question Review & Citations

    st.markdown("##### Question Review & NCERT Citations")
    for idx, q_data in enumerate(questions, start=1):
        q_attempt = attempts.get(str(idx), {})
        is_q_correct = q_attempt.get("is_correct", False)
        chosen_opt = q_attempt.get(
            "chosen", st.session_state.get("quiz_user_answers", {}).get(str(idx), "None")
        )
        correct_ans = str(q_data.get("correct_answer", "A")).strip().upper()
        if len(correct_ans) > 1 and correct_ans.startswith(("A", "B", "C", "D")):
            correct_ans = correct_ans[0]

        status_text = "Mastered" if is_q_correct else "Explored"

        with st.expander(
            f"Question {idx}: {q_data.get('question', '')[:65]}... — [{status_text}]",
            expanded=(idx == 1),
        ):
            st.markdown(f"**Question {idx}:** {q_data.get('question', '')}")

            opt_labels, _ = _extract_options(q_data.get("options", []))
            for opt_lbl in opt_labels:
                is_this_correct = opt_lbl.strip().startswith(correct_ans)
                is_this_chosen = opt_lbl.strip().startswith(str(chosen_opt))
                if is_this_correct:
                    st.markdown(f"- **{opt_lbl}** *(Correct Answer)*")
                elif is_this_chosen:
                    st.markdown(f"- {opt_lbl} *(Your Choice)*")
                else:
                    st.markdown(f"- {opt_lbl}")

            st.write("")
            st.markdown(f"**Explanation:** {q_data.get('explanation', '')}")

            sp = q_data.get("source_pages") or q_data.get("source_page") or q_data.get("pages")
            if not sp:
                exp_pages = re.findall(
                    r"(?:\[PAGE:\s*|page\s+|pages\s+|p\.\s*)(\d+)",
                    str(q_data.get("explanation", "")),
                    re.IGNORECASE,
                )
                if exp_pages:
                    sp = [int(p) for p in exp_pages]

            render_citation_box(
                chapter=chapter_name,
                class_level=class_level,
                pages=sp,
            )

            q_dialogue = chat_histories.get(str(idx), [])
            if q_dialogue:
                st.write("")
                st.markdown("**Socratic Dialogue:**")
                for msg in q_dialogue:
                    if msg["role"] == "user":
                        st.markdown(
                            f'<div class="socrates-chat-msg-user"><strong>You:</strong> {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div class="socrates-chat-msg-bot"><strong>Socrates:</strong> {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )


async def _render_socrates_quiz_mode(
    curr_quiz: Dict[str, Any],
    student_id: str,
    user_api_key: str,
    selected_model: str,
    class_level: int,
) -> None:
    """Renders the interactive Socratic learning flow with streamlined UI."""
    if st.session_state.get("socrates_completed") or st.session_state.get("quiz_submitted"):
        _render_socrates_completed_screen(
            curr_quiz=curr_quiz,
            student_id=student_id,
            class_level=class_level,
        )
        return

    questions = curr_quiz.get("questions", [])
    total_q = len(questions)
    chapter_name = curr_quiz.get("chapter", "Science")

    active_q = st.session_state.get("socrates_active_q", 1)
    if active_q < 1 or active_q > total_q:
        active_q = 1
        st.session_state.socrates_active_q = 1

    attempts = st.session_state.get("socrates_attempts", {})

    # Streamlined Step Navigator Strip
    nav_cols = st.columns(total_q)
    for q_i in range(1, total_q + 1):
        q_attempt = attempts.get(str(q_i))
        if q_attempt and q_attempt.get("is_correct"):
            btn_status = f"Q{q_i}: Done"
            icon_str = ":material/check_circle:"
        elif q_attempt:
            btn_status = f"Q{q_i}: Try"
            icon_str = ":material/pending:"
        else:
            btn_status = f"Q{q_i}"
            icon_str = ":material/radio_button_unchecked:"

        is_current = q_i == active_q
        if nav_cols[q_i - 1].button(
            btn_status,
            key=f"soc_nav_btn_{q_i}",
            icon=icon_str,
            type="primary" if is_current else "secondary",
            use_container_width=True,
        ):
            st.session_state.socrates_active_q = q_i
            st.rerun()

    st.write("")

    # Active Question
    q_data = questions[active_q - 1]
    st.markdown(f"#### Question {active_q} of {total_q} · {chapter_name}")
    st.markdown(f"**{q_data.get('question', '')}**")

    opt_labels, opt_map = _extract_options(q_data.get("options", []))

    current_attempt = attempts.get(str(active_q), {})
    saved_choice = current_attempt.get(
        "chosen", st.session_state.get("quiz_user_answers", {}).get(str(active_q))
    )

    saved_idx = None
    if saved_choice:
        for o_i, lbl in enumerate(opt_labels):
            if opt_map.get(lbl) == saved_choice or lbl == saved_choice:
                saved_idx = o_i
                break

    is_solved = current_attempt.get("is_correct", False)

    chosen = st.radio(
        f"Options for Question {active_q}:",
        opt_labels,
        index=saved_idx,
        key=f"soc_radio_q_{active_q}",
        disabled=is_solved,
        label_visibility="collapsed",
    )

    chosen_letter = None
    if chosen:
        chosen_letter = opt_map.get(chosen, chosen.split(")")[0].split(".")[0].strip().upper())
        if "quiz_user_answers" not in st.session_state:
            st.session_state.quiz_user_answers = {}
        st.session_state.quiz_user_answers[str(active_q)] = chosen_letter

    correct_letter = str(q_data.get("correct_answer", "A")).strip().upper()
    if len(correct_letter) > 1 and correct_letter.startswith(("A", "B", "C", "D")):
        correct_letter = correct_letter[0]

    # Hypothesis Testing Button
    if not is_solved:
        if st.button(
            "Test Hypothesis with Socrates",
            type="primary",
            icon=":material/psychology:",
            use_container_width=True,
            key=f"soc_test_btn_{active_q}",
        ):
            if not chosen_letter:
                st.warning("Please choose one of the options above.")
            else:
                is_correct = chosen_letter == correct_letter
                if is_correct:
                    st.session_state.socrates_attempts[str(active_q)] = {
                        "chosen": chosen_letter,
                        "is_correct": True,
                    }
                    st.rerun()
                else:
                    with st.spinner("Analyzing hypothesis..."):
                        reflection = generate_socrates_misconception(
                            question_text=q_data.get("question", ""),
                            options=q_data.get("options", []),
                            chosen_option=chosen_letter,
                            correct_option=correct_letter,
                            chapter=chapter_name,
                            class_level=class_level,
                            explanation=q_data.get("explanation", ""),
                            api_key=user_api_key,
                            model=selected_model,
                        )
                        st.session_state.socrates_attempts[str(active_q)] = {
                            "chosen": chosen_letter,
                            "is_correct": False,
                            "reflection": reflection,
                        }
                        st.rerun()

    # Feedback Box (Instant)
    if current_attempt:
        if current_attempt.get("is_correct"):
            st.success(f"Concept Mastered! Option {correct_letter} is correct.")
            with st.expander("NCERT Explanation & Citations", expanded=False):
                exp_text = q_data.get("explanation", "Refer to NCERT textbook.")
                st.markdown(f"**Explanation:** {exp_text}")
                sp = q_data.get("source_pages") or q_data.get("source_page") or q_data.get("pages")
                if not sp:
                    exp_pages = re.findall(
                        r"(?:\[PAGE:\s*|page\s+|pages\s+|p\.\s*)(\d+)",
                        str(exp_text),
                        re.IGNORECASE,
                    )
                    if exp_pages:
                        sp = [int(p) for p in exp_pages]
                render_citation_box(chapter=chapter_name, class_level=class_level, pages=sp)
        else:
            st.warning(
                current_attempt.get(
                    "reflection", "Consider re-examining the options and test again."
                )
            )

    st.write("")

    # Unified Socratic Hints Expander (Compact)
    hints = q_data.get("socrates_hints") or generate_socrates_hints(
        question=q_data.get("question", ""),
        options=q_data.get("options", []),
        chapter=chapter_name,
        class_level=class_level,
        explanation=q_data.get("explanation", ""),
        api_key=user_api_key,
        model=selected_model,
    )
    revealed_level = st.session_state.socrates_hints_revealed.get(str(active_q), 0)

    with st.expander("Socratic Hints & Guidance", expanded=(revealed_level > 0)):
        h_col1, h_col2, h_col3 = st.columns(3)
        with h_col1:
            if revealed_level >= 1:
                st.button(
                    "Tier 1 (Unlocked)",
                    icon=":material/lock_open:",
                    disabled=True,
                    use_container_width=True,
                    key=f"h1_u_{active_q}",
                )
            else:
                if st.button(
                    "Unlock Hint 1",
                    icon=":material/lightbulb:",
                    use_container_width=True,
                    key=f"h1_r_{active_q}",
                ):
                    st.session_state.socrates_hints_revealed[str(active_q)] = 1
                    st.rerun()
        with h_col2:
            if revealed_level >= 2:
                st.button(
                    "Tier 2 (Unlocked)",
                    icon=":material/lock_open:",
                    disabled=True,
                    use_container_width=True,
                    key=f"h2_u_{active_q}",
                )
            elif revealed_level >= 1:
                if st.button(
                    "Unlock Hint 2",
                    icon=":material/science:",
                    use_container_width=True,
                    key=f"h2_r_{active_q}",
                ):
                    st.session_state.socrates_hints_revealed[str(active_q)] = 2
                    st.rerun()
            else:
                st.button(
                    "Tier 2 (Locked)",
                    icon=":material/lock:",
                    disabled=True,
                    use_container_width=True,
                    key=f"h2_l_{active_q}",
                )
        with h_col3:
            if revealed_level >= 3:
                st.button(
                    "Tier 3 (Unlocked)",
                    icon=":material/lock_open:",
                    disabled=True,
                    use_container_width=True,
                    key=f"h3_u_{active_q}",
                )
            elif revealed_level >= 2:
                if st.button(
                    "Unlock Hint 3",
                    icon=":material/troubleshoot:",
                    use_container_width=True,
                    key=f"h3_r_{active_q}",
                ):
                    st.session_state.socrates_hints_revealed[str(active_q)] = 3
                    st.rerun()
            else:
                st.button(
                    "Tier 3 (Locked)",
                    icon=":material/lock:",
                    disabled=True,
                    use_container_width=True,
                    key=f"h3_l_{active_q}",
                )

        if revealed_level >= 1:
            st.info(f"**Thought Starter:** {hints.get('thought_starter', '')}")
        if revealed_level >= 2:
            st.info(f"**Core Principle:** {hints.get('guiding_principle', '')}")
        if revealed_level >= 3:
            st.info(f"**Deduction Clue:** {hints.get('socratic_deduction', '')}")

    # Unified Live Dialogue Expander
    chat_hist = st.session_state.socrates_chat_history.get(str(active_q), [])
    with st.expander("Ask Socrates about this Question", expanded=bool(chat_hist)):
        sq_col1, sq_col2 = st.columns(2)
        user_query_to_send = None

        if sq_col1.button(
            "Why is this concept important?",
            icon=":material/lightbulb:",
            key=f"sq1_{active_q}",
            use_container_width=True,
        ):
            user_query_to_send = "Can you explain why this scientific law is fundamental in NCERT and give a real-world intuition?"

        if sq_col2.button(
            "Give me a thought experiment",
            icon=":material/science:",
            key=f"sq2_{active_q}",
            use_container_width=True,
        ):
            user_query_to_send = (
                "Can you give me a simple everyday thought experiment to visualize this concept?"
            )

        for msg in chat_hist:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="socrates-chat-msg-user"><strong>You:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="socrates-chat-msg-bot"><strong>Socrates:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

        with st.form(key=f"soc_dialogue_form_{active_q}", clear_on_submit=True):
            custom_input = st.text_input(
                "Your question for Socrates:",
                placeholder="Ask Socrates a doubt about this question...",
                key=f"soc_custom_text_{active_q}",
                label_visibility="collapsed",
            )
            form_submitted = st.form_submit_button(
                "Ask Socrates", icon=":material/send:", type="primary"
            )
            if form_submitted and custom_input.strip():
                user_query_to_send = custom_input.strip()

        if user_query_to_send:
            clean_q = user_query_to_send.strip()
            if str(active_q) not in st.session_state.socrates_chat_history:
                st.session_state.socrates_chat_history[str(active_q)] = []

            st.session_state.socrates_chat_history[str(active_q)].append(
                {"role": "user", "content": clean_q}
            )
            st.markdown(
                f'<div class="socrates-chat-msg-user"><strong>You:</strong> {clean_q}</div>',
                unsafe_allow_html=True,
            )

            bot_placeholder = st.empty()
            full_bot_reply = ""
            try:
                async for chunk in stream_socrates_dialogue(
                    question_text=q_data.get("question", ""),
                    options=q_data.get("options", []),
                    student_query=clean_q,
                    chat_history=st.session_state.socrates_chat_history[str(active_q)][:-1],
                    chapter=chapter_name,
                    class_level=class_level,
                    explanation=q_data.get("explanation", ""),
                    api_key=user_api_key,
                    model=selected_model,
                ):
                    full_bot_reply += chunk
                    bot_placeholder.markdown(
                        f'<div class="socrates-chat-msg-bot"><strong>Socrates:</strong> {full_bot_reply}▌</div>',
                        unsafe_allow_html=True,
                    )
                    await asyncio.sleep(0.015)

                bot_placeholder.markdown(
                    f'<div class="socrates-chat-msg-bot"><strong>Socrates:</strong> {full_bot_reply}</div>',
                    unsafe_allow_html=True,
                )
                st.session_state.socrates_chat_history[str(active_q)].append(
                    {"role": "assistant", "content": full_bot_reply}
                )
            except Exception as e:
                logger.error(f"Socratic dialogue failed: {e}")
                st.error(f"Dialogue error: {e}")

    st.write("")
    st.divider()

    # Bottom Step Navigation & End Session Button
    b_col1, b_col2, b_col3 = st.columns([1.2, 2.6, 1.2])
    with b_col1:
        if active_q > 1:
            if st.button(
                "Previous Question",
                icon=":material/arrow_back:",
                key="soc_prev_btn",
                use_container_width=True,
            ):
                st.session_state.socrates_active_q = active_q - 1
                st.rerun()

    with b_col3:
        if active_q < total_q:
            if st.button(
                "Next Question",
                icon=":material/arrow_forward:",
                key="soc_next_btn",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.socrates_active_q = active_q + 1
                st.rerun()

    mastered_count = sum(1 for a in attempts.values() if a.get("is_correct"))
    with b_col2:
        if st.button(
            f"End Session & Finalize ({mastered_count}/{total_q} Solved)",
            type="primary" if mastered_count == total_q else "secondary",
            icon=":material/verified:",
            use_container_width=True,
            key="soc_finalize_btn",
        ):
            user_answers = st.session_state.get("quiz_user_answers", {})
            try:
                sub_result = submit_and_grade_quiz(
                    student_id=student_id,
                    quiz_id=curr_quiz.get("quiz_id"),
                    user_answers=user_answers,
                    quiz_data=curr_quiz,
                )
                st.session_state.last_submission_result = sub_result
                st.session_state.socrates_completed = True
                st.session_state.quiz_submitted = True
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to submit Socratic quiz: {e}")
                st.error(f"Session submission error: {e}")


def _render_standard_quiz_mode(
    curr_quiz: Dict[str, Any],
    student_id: str,
    class_level: int,
) -> None:
    """Renders the standard all-at-once quiz examination interface."""
    chapter_name = curr_quiz.get("chapter", "Science")
    questions = curr_quiz.get("questions", [])
    total_q = len(questions)
    is_submitted = st.session_state.get("quiz_submitted", False)

    st.markdown(f"#### {chapter_name} Quiz — Class {curr_quiz.get('class_level', class_level)}")
    st.caption(
        f"Difficulty: {curr_quiz.get('difficulty', 'medium').capitalize()} | Questions: {total_q}"
    )

    if is_submitted:
        sub_res = st.session_state.get("last_submission_result", {})
        correct_count = sub_res.get("score", 0)
        pct = sub_res.get("percentage", 0)

        st.success(f"Quiz Completed — Score: {correct_count}/{total_q} ({pct}%)")

        if sub_res:
            status_name = sub_res.get("new_status", "").upper()
            if sub_res.get("status_changed"):
                st.info(
                    f"SWAT Status Updated: {sub_res.get('status_change_summary')} [{status_name}]"
                )
            else:
                st.caption(
                    f"SWAT Chapter Score: {sub_res.get('chapter')} average is {sub_res.get('new_chapter_score')}% [{status_name}]"
                )

        st.write("")
        st.divider()
        st.markdown("##### Examination Review & Citations")

    user_answers = st.session_state.get("quiz_user_answers", {})

    for idx, q_data in enumerate(questions, start=1):
        st.markdown(f"**Question {idx}:** {q_data['question']}")

        opt_labels, opt_map = _extract_options(q_data.get("options", []))

        saved_ans = user_answers.get(str(idx))
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
            chosen_letter = opt_map.get(chosen, chosen.split(")")[0].split(".")[0].strip().upper())
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

            with st.expander("Explanation & NCERT Citations", expanded=True):
                exp_text = q_data.get("explanation", "Refer to NCERT textbook.")
                st.markdown(f"**Explanation:** {exp_text}")

                sp = q_data.get("source_pages") or q_data.get("source_page") or q_data.get("pages")
                if not sp:
                    exp_pages = re.findall(
                        r"(?:\[PAGE:\s*|page\s+|pages\s+|p\.\s*)(\d+)",
                        str(exp_text),
                        re.IGNORECASE,
                    )
                    if exp_pages:
                        sp = [int(p) for p in exp_pages]

                render_citation_box(
                    chapter=chapter_name,
                    class_level=class_level,
                    pages=sp,
                )

        st.write("")

    st.session_state.quiz_user_answers = user_answers

    if not is_submitted:
        if st.button(
            "Submit Quiz & Finalize",
            icon=":material/check_circle:",
            type="primary",
            use_container_width=True,
            key="std_submit_btn",
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
