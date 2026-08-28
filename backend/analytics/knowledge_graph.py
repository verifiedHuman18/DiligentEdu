"""Knowledge Graph Analytics Service (Phases 1-31).

Provides intra-chapter concept-level graph synthesis, student concept mastery calculations,
multi-concept telemetry weighting, unattempted concept isolation, and recommended study resources.
"""

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from backend.config import config
from backend.curriculum.concepts import (
    get_all_registered_chapters,
    get_chapter_concept_metadata,
)
from backend.models.knowledge_graph import (
    ChapterKnowledgeGraph,
    ConceptEdge,
    ConceptNode,
    ConceptStatus,
    EdgeRelationship,
)
from backend.storage.database import get_db_connection

logger = logging.getLogger(__name__)


def _match_question_to_concepts(
    question_text: str,
    chapter_concepts: List[Dict[str, Any]],
) -> List[str]:
    """
    Fallback matcher: infers concept IDs from question text using keyword analysis
    when explicit concept tags are missing (e.g. legacy quizzes).
    """
    if not question_text:
        return []

    q_lower = question_text.lower()
    matched_ids = []

    for c in chapter_concepts:
        c_id = c["id"]
        c_name = c["name"].lower()
        keywords = [k.lower() for k in c.get("keywords", [])]

        if c_name in q_lower or any(kw in q_lower for kw in keywords):
            matched_ids.append(c_id)

    return matched_ids


def calculate_student_concept_telemetry(
    student_id: str,
    class_level: int,
    chapter_name: Optional[str] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Calculates detailed concept-level telemetry (attempts, correct, mastery) for a student,
    isolated strictly to the active class level and subject.
    Handles multi-concept questions via equal weighting (w = 1/n).
    Strictly keeps unassessed concepts as None / unattempted.
    """
    target_db = db_path or str(config.default_db_path)
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    concept_stats: Dict[str, Dict[str, float]] = {}

    try:
        with get_db_connection(target_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    qr.question_id,
                    qr.question_text,
                    qr.chapter,
                    qr.is_correct,
                    qr.concept_id,
                    qa.class_level,
                    qa.subject
                FROM question_responses qr
                JOIN quiz_attempts qa ON qr.quiz_id = qa.quiz_id
                WHERE qa.student_id = ? AND qa.class_level = ? AND qa.subject = ?
            """
            params: List[Any] = [str(student_id).strip(), int(class_level), subj_clean]

            if chapter_name:
                query += " AND qr.chapter = ?"
                params.append(str(chapter_name).strip())

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            for row in rows:
                q_text = row["question_text"] or ""
                ch_name = row["chapter"] or ""
                is_correct = int(row["is_correct"]) == 1
                raw_concept = row["concept_id"]

                target_concepts: List[str] = []

                if raw_concept:
                    try:
                        parsed = json.loads(raw_concept)
                        if isinstance(parsed, list):
                            target_concepts = [
                                str(item).strip() for item in parsed if str(item).strip()
                            ]
                        elif isinstance(parsed, str) and parsed.strip():
                            target_concepts = [parsed.strip()]
                    except Exception:
                        if str(raw_concept).strip():
                            target_concepts = [str(raw_concept).strip()]

                # If no explicit concept tag stored, match dynamically
                if not target_concepts:
                    ch_meta = get_chapter_concept_metadata(
                        ch_name, class_level=class_level, subject=subj_clean
                    )
                    if ch_meta:
                        target_concepts = _match_question_to_concepts(
                            q_text, ch_meta.get("nodes", [])
                        )

                if not target_concepts:
                    continue

                weight = 1.0 / len(target_concepts)
                for c_id in target_concepts:
                    if c_id not in concept_stats:
                        concept_stats[c_id] = {"attempts": 0.0, "correct": 0.0}

                    concept_stats[c_id]["attempts"] += weight
                    if is_correct:
                        concept_stats[c_id]["correct"] += weight

    except Exception as e:
        logger.error(f"Error computing concept telemetry for student {student_id}: {e}")

    # Format telemetry results
    results: Dict[str, Dict[str, Any]] = {}
    for c_id, stats in concept_stats.items():
        attempts = round(stats["attempts"], 2)
        correct = round(stats["correct"], 2)

        if attempts > 0:
            mastery_pct = int(round((correct / attempts) * 100.0))
            if mastery_pct >= 80:
                status = ConceptStatus.STRONG
            elif mastery_pct >= 60:
                status = ConceptStatus.MODERATE
            else:
                status = ConceptStatus.WEAK

            if attempts >= 4:
                conf = "High"
            elif attempts >= 2:
                conf = "Medium"
            else:
                conf = "Low"
        else:
            mastery_pct = None
            status = ConceptStatus.UNATTEMPTED
            conf = "Unassessed"

        results[c_id] = {
            "concept_id": c_id,
            "attempts": int(round(attempts)),
            "correct": int(round(correct)),
            "mastery": mastery_pct,
            "status": status,
            "confidence": conf,
        }

    return results


def get_chapter_knowledge_graph(
    student_id: str,
    class_level: int,
    chapter_name: str,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs the complete concept knowledge graph for a specific chapter, subject, and student.
    Merges authoritative NCERT concepts, dependency edges, student performance telemetry,
    and linked uploaded study materials.
    """
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    ch_meta = get_chapter_concept_metadata(
        chapter_name, class_level=class_level, subject=subj_clean
    )
    target_class = int(class_level)

    if ch_meta:
        ch_title = chapter_name
        ch_num = int(ch_meta.get("chapter_number", 1))
        nodes_raw = ch_meta.get("nodes", [])
        edges_raw = ch_meta.get("edges", [])
    else:
        # Fallback dynamic node for unregistered chapter
        ch_title = chapter_name
        ch_num = 1
        nodes_raw = [
            {
                "id": f"{ch_title.lower().replace(' ', '_')}_overview",
                "name": f"{ch_title} Overview",
                "section": "General",
                "tier": 1,
                "description": f"Foundational concepts and principles of {ch_title}.",
                "keywords": [ch_title.lower()],
                "pos_x": 400,
                "pos_y": 150,
            }
        ]
        edges_raw = []

    # Calculate student concept mastery telemetry
    telemetry = calculate_student_concept_telemetry(
        student_id=student_id,
        class_level=target_class,
        chapter_name=ch_title,
        subject=subj_clean,
        db_path=db_path,
    )

    # Fetch student uploaded documents for resource linking
    student_docs: List[Dict[str, Any]] = []
    try:
        from backend.storage.repository import study_material_repository

        m_repo = (
            study_material_repository
            if db_path is None
            else type(study_material_repository)(db_path=db_path)
        )
        student_docs = m_repo.get_student_documents(
            student_id=student_id,
            class_level=target_class,
            subject=subj_clean,
        )
    except Exception as e:
        logger.debug(f"Could not load study materials for resource linking: {e}")

    # Filter study materials relevant to this chapter or general reference
    matching_materials = []
    for doc in student_docs:
        doc_ch = doc.get("chapter")
        if (
            not doc_ch
            or doc_ch == "All Chapters"
            or doc_ch.lower() in ch_title.lower()
            or ch_title.lower() in doc_ch.lower()
        ):
            matching_materials.append(
                {
                    "document_id": doc.get("document_id"),
                    "title": doc.get("material_name") or doc.get("filename"),
                    "filename": doc.get("filename"),
                    "source_type": "user_upload",
                }
            )

    constructed_nodes: List[ConceptNode] = []
    attempted_mastery_sum = 0.0
    attempted_nodes_count = 0
    strong_c = 0
    mod_c = 0
    weak_c = 0
    unatt_c = 0

    for nr in nodes_raw:
        c_id = nr["id"]
        t_data = telemetry.get(c_id, {})

        attempts = t_data.get("attempts", 0)
        correct = t_data.get("correct", 0)
        mastery = t_data.get("mastery")
        status = t_data.get("status", ConceptStatus.UNATTEMPTED)
        conf = t_data.get("confidence", "Unassessed")

        if attempts == 0 or mastery is None:
            status = ConceptStatus.UNATTEMPTED
            mastery = None
            conf = "Unassessed"
            unatt_c += 1
        else:
            attempted_mastery_sum += mastery
            attempted_nodes_count += 1
            if status == ConceptStatus.STRONG:
                strong_c += 1
            elif status == ConceptStatus.MODERATE:
                mod_c += 1
            else:
                weak_c += 1

        resources = [
            {
                "title": f"NCERT Class {target_class} Science · Chapter {ch_num} ({ch_title})",
                "source_type": "ncert",
                "section": nr.get("section", ""),
            }
        ]
        resources.extend(matching_materials)

        node = ConceptNode(
            id=c_id,
            name=nr["name"],
            chapter=ch_title,
            chapter_number=ch_num,
            class_level=target_class,
            section=nr.get("section", ""),
            description=nr.get("description", ""),
            tier=nr.get("tier", 1),
            keywords=nr.get("keywords", []),
            mastery=mastery,
            status=status,
            attempts=attempts,
            correct=correct,
            confidence=conf,
            pos_x=float(nr.get("pos_x", 400)),
            pos_y=float(nr.get("pos_y", 150)),
            recommended_resources=resources,
        )
        constructed_nodes.append(node)

    constructed_edges: List[ConceptEdge] = []
    for er in edges_raw:
        rel = er.get("relationship", "prerequisite")
        try:
            rel_enum = EdgeRelationship(rel)
        except ValueError:
            rel_enum = EdgeRelationship.PREREQUISITE

        edge = ConceptEdge(
            source=er["source"],
            target=er["target"],
            relationship=rel_enum,
            label=rel.replace("_", " ").title(),
        )
        constructed_edges.append(edge)

    overall_mastery = (
        round(attempted_mastery_sum / attempted_nodes_count, 1)
        if attempted_nodes_count > 0
        else None
    )

    graph = ChapterKnowledgeGraph(
        chapter=ch_title,
        chapter_number=ch_num,
        class_level=target_class,
        nodes=constructed_nodes,
        edges=constructed_edges,
        overall_mastery=overall_mastery,
        total_concepts=len(constructed_nodes),
        strong_count=strong_c,
        moderate_count=mod_c,
        weak_count=weak_c,
        unattempted_count=unatt_c,
    )

    return graph.to_dict()


def get_available_knowledge_map_chapters(
    class_level: int, subject: str = "Science"
) -> List[Dict[str, Any]]:
    """Returns sorted list of chapters supported by the Knowledge Map for the selected class and subject."""
    return get_all_registered_chapters(class_level=class_level, subject=subject)
