"""Study Twin Academic Matching Engine (Deterministic Multidimensional Similarity, Zero LLM Calls).

Matches students based on:
1. Strict Boundary Hard Filters (Same Class Level, Same Subject)
2. Action Plan Priority Alignment (30%)
3. Overlapping Weak Topics (25%)
4. Current/Recent Chapter Focus (25%)
5. Mastery Profile Distance (15%)
6. Activity Recency (5%)
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.analytics.action_plan import generate_action_plan
from backend.analytics.swat import get_student_swat
from backend.curriculum.service import curriculum_service
from backend.models.study_twin import StudyTwinMatch, StudyTwinProfile
from backend.storage.repository import (
    get_all_candidate_student_ids,
    get_saved_study_twin_match,
    quiz_repository,
    save_study_twin_match,
)

logger = logging.getLogger(__name__)

# Weighting configuration (Phase 11)
WEIGHT_ACTION_PLAN = 0.30
WEIGHT_WEAK_TOPICS = 0.25
WEIGHT_CURRENT_TOPICS = 0.25
WEIGHT_MASTERY_PROFILE = 0.15
WEIGHT_RECENCY = 0.05

MIN_MATCH_THRESHOLD = 25.0  # Percentage below which match is deemed insufficient


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Computes Jaccard index J(A, B) = |A ∩ B| / |A ∪ B|."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


def _parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Safely parses ISO timestamps."""
    if not ts_str:
        return None
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def build_study_twin_profile(
    student_id: str,
    class_level: int,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> StudyTwinProfile:
    """
    Derives a student's StudyTwinProfile directly from their existing SWAT and Action Plan.
    Guarantees single source of truth without duplicating state (Phases 3-4, 26).
    """
    clean_student_id = str(student_id).strip()
    class_int = int(class_level)
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"

    # 1. Fetch SWAT analytics (0 LLM tokens)
    swat = get_student_swat(
        clean_student_id, class_level=class_int, subject=subj_clean, db_path=db_path
    )

    # 2. Fetch Action Plan (0 LLM tokens)
    action_plan = generate_action_plan(
        clean_student_id, class_level=class_int, subject=subj_clean, db_path=db_path
    )

    # 3. Categorized topics
    weak_topics = [item["chapter"] for item in swat.get("weak", []) if "chapter" in item]
    avg_topics = [item["chapter"] for item in swat.get("average", []) if "chapter" in item]
    strong_topics = [item["chapter"] for item in swat.get("strong", []) if "chapter" in item]
    unattempted_topics = [
        item["chapter"] for item in swat.get("unattempted", []) if "chapter" in item
    ]

    # 4. Action plan priorities (ordered top recommendations)
    action_priorities = [
        act["chapter"] for act in action_plan.get("actions", []) if "chapter" in act
    ]

    # 5. Normalized topic mastery vector across all curriculum chapters
    all_chapters = curriculum_service.get_chapters_for_grade(class_int, subject=subj_clean)
    ch_breakdown = swat.get("chapter_breakdown", {})
    topic_mastery: Dict[str, float] = {}

    for ch in all_chapters:
        ch_title = ch.chapter_title
        ch_data = ch_breakdown.get(ch_title)
        if ch_data and ch_data.get("score") is not None:
            topic_mastery[ch_title] = float(ch_data["score"]) / 100.0
        else:
            topic_mastery[ch_title] = 0.5  # Neutral baseline for unattempted

    # 6. Current/recent chapters and recency from quiz history
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(
        clean_student_id, class_level=class_int, subject=subj_clean, include_questions=False
    )

    current_chapters: List[str] = []
    seen_chs = set()
    for att in history:
        ch_name = att.get("chapter")
        if ch_name and ch_name not in seen_chs:
            seen_chs.add(ch_name)
            current_chapters.append(ch_name)
        if len(current_chapters) >= 3:
            break

    total_quizzes = swat.get("overall", {}).get("quizzes_attempted", len(history))
    total_q = swat.get("overall", {}).get("total_questions", 0)
    has_data = total_quizzes > 0 or len(weak_topics) > 0 or len(strong_topics) > 0

    last_ts = None
    if history:
        last_ts = history[0].get("timestamp")

    return StudyTwinProfile(
        student_id=clean_student_id,
        class_level=class_int,
        subject=subj_clean,
        current_chapters=current_chapters,
        weak_topics=weak_topics,
        average_topics=avg_topics,
        strong_topics=strong_topics,
        unattempted_topics=unattempted_topics,
        topic_mastery=topic_mastery,
        action_plan_priorities=action_priorities,
        quizzes_attempted=total_quizzes,
        total_questions=total_q,
        has_sufficient_data=has_data,
        last_activity_timestamp=last_ts,
    )


def calculate_twin_similarity(
    profile_a: StudyTwinProfile, profile_b: StudyTwinProfile
) -> Tuple[float, Dict[str, float], Dict[str, List[str]]]:
    """
    Computes multidimensional similarity score between two student profiles (Phases 5-11).

    Enforces strict class & subject boundary. Returns:
      - similarity_score (0.0 to 100.0)
      - component_scores (individual breakdown)
      - shared_items (shared weak topics, shared current chapters, shared action goals)
    """
    # Hard boundary check (Phase 2)
    if profile_a.class_level != profile_b.class_level or profile_a.subject != profile_b.subject:
        return 0.0, {}, {"shared_weak": [], "shared_current": [], "shared_actions": []}

    set_curr_a = set(profile_a.current_chapters)
    set_curr_b = set(profile_b.current_chapters)
    shared_current = sorted(list(set_curr_a.intersection(set_curr_b)))
    score_current = _jaccard_similarity(set_curr_a, set_curr_b)

    set_weak_a = set(profile_a.weak_topics)
    set_weak_b = set(profile_b.weak_topics)
    shared_weak = sorted(list(set_weak_a.intersection(set_weak_b)))
    score_weak = _jaccard_similarity(set_weak_a, set_weak_b)

    set_act_a = set(profile_a.action_plan_priorities)
    set_act_b = set(profile_b.action_plan_priorities)
    shared_actions = sorted(list(set_act_a.intersection(set_act_b)))
    score_actions = _jaccard_similarity(set_act_a, set_act_b)

    # 4. Mastery Profile Similarity (Cosine / Manhattan Distance)
    all_keys = set(profile_a.topic_mastery.keys()).union(set(profile_b.topic_mastery.keys()))
    if all_keys:
        total_diff = sum(
            abs(profile_a.topic_mastery.get(k, 0.5) - profile_b.topic_mastery.get(k, 0.5))
            for k in all_keys
        )
        score_mastery = max(0.0, 1.0 - (total_diff / len(all_keys)))
    else:
        score_mastery = 1.0

    # 5. Activity Recency (Phase 10)
    score_recency = 0.5
    ts_a = _parse_timestamp(profile_a.last_activity_timestamp)
    ts_b = _parse_timestamp(profile_b.last_activity_timestamp)
    if ts_a and ts_b:
        now = datetime.now(timezone.utc)
        if ts_a.tzinfo is None:
            ts_a = ts_a.replace(tzinfo=timezone.utc)
        if ts_b.tzinfo is None:
            ts_b = ts_b.replace(tzinfo=timezone.utc)
        days_gap = abs((now - ts_b).total_seconds()) / 86400.0
        # Exponential decay: e^(-0.05 * days)
        score_recency = math.exp(-0.05 * min(days_gap, 60.0))
    elif ts_b:
        score_recency = 0.7

    # Weighted Composite Score (Phase 11)
    raw_composite = (
        (WEIGHT_ACTION_PLAN * score_actions)
        + (WEIGHT_WEAK_TOPICS * score_weak)
        + (WEIGHT_CURRENT_TOPICS * score_current)
        + (WEIGHT_MASTERY_PROFILE * score_mastery)
        + (WEIGHT_RECENCY * score_recency)
    )

    similarity_percentage = round(min(100.0, max(0.0, raw_composite * 100.0)), 1)

    components = {
        "action_plan_similarity": round(score_actions * 100, 1),
        "weak_topics_similarity": round(score_weak * 100, 1),
        "current_topics_similarity": round(score_current * 100, 1),
        "mastery_profile_similarity": round(score_mastery * 100, 1),
        "recency_similarity": round(score_recency * 100, 1),
    }

    shared = {
        "shared_weak": shared_weak,
        "shared_current": shared_current,
        "shared_actions": shared_actions,
    }

    return similarity_percentage, components, shared


def _generate_deterministic_explanation(
    shared_weak: List[str],
    shared_current: List[str],
    shared_actions: List[str],
    class_level: int,
    subject: str,
) -> str:
    """Generates deterministic, transparent match explanation without LLM calls (Phase 16)."""
    clauses = []
    if shared_current:
        topics_str = ", ".join(f"**{t}**" for t in shared_current[:2])
        clauses.append(f"are both currently studying {topics_str}")

    if shared_weak:
        weak_str = ", ".join(f"**{w}**" for w in shared_weak[:2])
        clauses.append(f"both need practice in {weak_str}")

    if shared_actions:
        act_str = ", ".join(f"**{a}**" for a in shared_actions[:2])
        clauses.append(f"share priority goals for {act_str}")

    if not clauses:
        return f"You both share curriculum focus and study momentum in Class {class_level} {subject}."

    if len(clauses) == 1:
        return f"You and your Study Twin {clauses[0]} in Class {class_level} {subject}."

    return (
        f"You and your Study Twin {clauses[0]} and {clauses[1]} in Class {class_level} {subject}."
    )


def find_study_twin(
    student_id: str,
    class_level: int,
    subject: str = "Science",
    db_path: Optional[str] = None,
    force_refresh: bool = False,
) -> StudyTwinMatch:
    """
    Orchestrates the complete Study Twin matching pipeline (Phases 12-16, 21-25).

    Pipeline:
      1. Check cache (unless force_refresh is True).
      2. Build student's own StudyTwinProfile.
      3. Verify sufficient data threshold (Phase 13).
      4. Retrieve eligible candidates in the exact same class & subject (Phase 2, 12).
      5. Rank candidates by deterministic similarity score.
      6. Return highest scoring match (or transparent no_match state).
      7. Cache result in SQLite database.
    """
    clean_student_id = str(student_id).strip()
    class_int = int(class_level)
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"

    # 1. Cached Match Check (Phase 24)
    if not force_refresh:
        cached = get_saved_study_twin_match(
            clean_student_id, class_int, subj_clean, db_path=db_path
        )
        if cached and cached.get("match_data"):
            m_data = cached["match_data"]
            return StudyTwinMatch(
                student_id=clean_student_id,
                twin_student_id=cached.get("twin_student_id", "anonymous_twin"),
                class_level=class_int,
                subject=subj_clean,
                similarity_score=float(cached.get("similarity_score", 0.0)),
                shared_current_chapters=m_data.get("shared_current_chapters", []),
                shared_weak_topics=m_data.get("shared_weak_topics", []),
                shared_action_goals=m_data.get("shared_action_goals", []),
                component_scores=m_data.get("component_scores", {}),
                explanation=m_data.get("explanation", ""),
                status=m_data.get("status", "active"),
                created_at=cached.get("created_at", datetime.now(timezone.utc).isoformat()),
            )

    # 2. Build Student's Profile
    target_profile = build_study_twin_profile(
        clean_student_id, class_level=class_int, subject=subj_clean, db_path=db_path
    )

    # 3. Insufficient Data Check (Phase 13)
    if not target_profile.has_sufficient_data:
        match_obj = StudyTwinMatch(
            student_id=clean_student_id,
            twin_student_id="",
            class_level=class_int,
            subject=subj_clean,
            similarity_score=0.0,
            status="insufficient_data",
            explanation="Complete a few practice quizzes to build your academic profile and find your Study Twin.",
        )
        save_study_twin_match(
            clean_student_id,
            "",
            class_int,
            subj_clean,
            0.0,
            match_obj.to_dict(),
            db_path=db_path,
        )
        return match_obj

    # 4. Discover Candidates (Phase 12)
    candidate_ids = get_all_candidate_student_ids(
        class_level=class_int,
        subject=subj_clean,
        exclude_student_id=clean_student_id,
        db_path=db_path,
    )

    if not candidate_ids:
        match_obj = StudyTwinMatch(
            student_id=clean_student_id,
            twin_student_id="",
            class_level=class_int,
            subject=subj_clean,
            similarity_score=0.0,
            status="no_candidates",
            explanation=f"No other student profiles found in Class {class_int} {subj_clean} yet.",
        )
        save_study_twin_match(
            clean_student_id,
            "",
            class_int,
            subj_clean,
            0.0,
            match_obj.to_dict(),
            db_path=db_path,
        )
        return match_obj

    # 5. Score Candidates
    best_candidate_id: Optional[str] = None
    best_score = -1.0
    best_components: Dict[str, float] = {}
    best_shared: Dict[str, List[str]] = {}

    for cand_id in candidate_ids:
        try:
            cand_profile = build_study_twin_profile(
                cand_id, class_level=class_int, subject=subj_clean, db_path=db_path
            )
            sim_score, comps, shared = calculate_twin_similarity(target_profile, cand_profile)
            if sim_score > best_score:
                best_score = sim_score
                best_candidate_id = cand_id
                best_components = comps
                best_shared = shared
        except Exception as e:
            logger.warning(f"Error evaluating candidate {cand_id}: {e}")

    # 6. Evaluate Quality Threshold (Phase 21)
    if not best_candidate_id or best_score < MIN_MATCH_THRESHOLD:
        match_obj = StudyTwinMatch(
            student_id=clean_student_id,
            twin_student_id=best_candidate_id or "",
            class_level=class_int,
            subject=subj_clean,
            similarity_score=max(0.0, best_score if best_score >= 0 else 0.0),
            status="no_strong_match",
            explanation="We couldn't find a strong Study Twin right now. Keep practicing and we'll look again as your mastery evolves.",
        )
        save_study_twin_match(
            clean_student_id,
            best_candidate_id or "",
            class_int,
            subj_clean,
            match_obj.similarity_score,
            match_obj.to_dict(),
            db_path=db_path,
        )
        return match_obj

    # 7. Formulate Successful Match (Phase 16, 18)
    explanation_text = _generate_deterministic_explanation(
        shared_weak=best_shared.get("shared_weak", []),
        shared_current=best_shared.get("shared_current", []),
        shared_actions=best_shared.get("shared_actions", []),
        class_level=class_int,
        subject=subj_clean,
    )

    match_obj = StudyTwinMatch(
        student_id=clean_student_id,
        twin_student_id=best_candidate_id,  # Internal ID for server persistence
        class_level=class_int,
        subject=subj_clean,
        similarity_score=best_score,
        shared_current_chapters=best_shared.get("shared_current", []),
        shared_weak_topics=best_shared.get("shared_weak", []),
        shared_action_goals=best_shared.get("shared_actions", []),
        component_scores=best_components,
        explanation=explanation_text,
        status="active",
    )

    save_study_twin_match(
        clean_student_id,
        best_candidate_id,
        class_int,
        subj_clean,
        best_score,
        match_obj.to_dict(),
        db_path=db_path,
    )

    return match_obj
