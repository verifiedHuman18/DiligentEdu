"""Knowledge Graph data models for concept-level curriculum mastery and network maps."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConceptStatus(str, Enum):
    """Concept mastery diagnostic categorization."""

    STRONG = "strong"  # >= 80%
    MODERATE = "moderate"  # 60% - 79%
    WEAK = "weak"  # < 60%
    UNATTEMPTED = "unattempted"  # 0 attempts


class EdgeRelationship(str, Enum):
    """Semantic relationship between curriculum concepts."""

    PREREQUISITE = "prerequisite"
    RELATED = "related"
    DERIVED_FROM = "derived_from"
    COMPONENT_OF = "component_of"


@dataclass
class ConceptNode:
    """Individual concept / subtopic within an NCERT chapter."""

    id: str  # Unique stable ID: e.g. "electricity_ohms_law"
    name: str  # Display name: "Ohm's Law"
    chapter: str  # "Electricity"
    chapter_number: int  # 12
    class_level: int  # 10
    section: str = ""  # e.g. "12.2"
    description: str = ""  # Core concept explanation
    tier: int = 1  # 1: Foundations, 2: Core Principles, 3: Applications / Synthesis
    keywords: List[str] = field(default_factory=list)
    mastery: Optional[float] = None  # Percentage score 0.0 - 100.0 or None if unattempted
    status: ConceptStatus = ConceptStatus.UNATTEMPTED
    attempts: int = 0
    correct: int = 0
    confidence: str = "Unassessed"  # "High", "Medium", "Low", "Unassessed"
    pos_x: float = 0.0  # Normalized X coordinate (0 - 1000) for deterministic layout
    pos_y: float = 0.0  # Normalized Y coordinate (0 - 600)
    recommended_resources: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = (
            self.status.value if isinstance(self.status, ConceptStatus) else str(self.status)
        )
        return data


@dataclass
class ConceptEdge:
    """Directed dependency or conceptual relation between two concepts."""

    source: str  # Source concept ID
    target: str  # Target concept ID
    relationship: EdgeRelationship = EdgeRelationship.PREREQUISITE
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship.value
            if isinstance(self.relationship, EdgeRelationship)
            else str(self.relationship),
            "label": self.label,
        }


@dataclass
class ChapterKnowledgeGraph:
    """Complete intra-chapter concept graph for an NCERT chapter."""

    chapter: str
    chapter_number: int
    class_level: int
    nodes: List[ConceptNode] = field(default_factory=list)
    edges: List[ConceptEdge] = field(default_factory=list)
    overall_mastery: Optional[float] = None
    total_concepts: int = 0
    strong_count: int = 0
    moderate_count: int = 0
    weak_count: int = 0
    unattempted_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "chapter_number": self.chapter_number,
            "class_level": self.class_level,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "overall_mastery": self.overall_mastery,
            "total_concepts": self.total_concepts,
            "strong_count": self.strong_count,
            "moderate_count": self.moderate_count,
            "weak_count": self.weak_count,
            "unattempted_count": self.unattempted_count,
        }
