"""Authoritative NCERT Curriculum Service."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.config import config
from backend.exceptions import ChapterNotFoundError, CurriculumError
from backend.models.curriculum import ChapterInfo

logger = logging.getLogger(__name__)


DEFAULT_CURRICULUM_MAPPING = {
    "class9": {
        "iesc101.pdf": {
            "chapter_number": 1,
            "chapter": "Exploration: Entering the World of Secondary Science",
        },
        "iesc102.pdf": {"chapter_number": 2, "chapter": "Cell: The Building Block of Life"},
        "iesc103.pdf": {"chapter_number": 3, "chapter": "Tissues in Action"},
        "iesc104.pdf": {"chapter_number": 4, "chapter": "Describing Motion Around Us"},
        "iesc105.pdf": {"chapter_number": 5, "chapter": "Exploring Mixtures and their Separation"},
        "iesc106.pdf": {"chapter_number": 6, "chapter": "How Forces Affect Motion"},
        "iesc107.pdf": {"chapter_number": 7, "chapter": "Work, Energy, and Simple Machines"},
        "iesc108.pdf": {"chapter_number": 8, "chapter": "Journey Inside the Atom"},
        "iesc109.pdf": {"chapter_number": 9, "chapter": "Atomic Foundations of Matter"},
        "iesc110.pdf": {
            "chapter_number": 10,
            "chapter": "Sound Waves: Characteristics and Applications",
        },
        "iesc111.pdf": {"chapter_number": 11, "chapter": "Reproduction: How Life Continues"},
        "iesc112.pdf": {
            "chapter_number": 12,
            "chapter": "Patterns in Life: Diversity and Classification",
        },
        "iesc113.pdf": {
            "chapter_number": 13,
            "chapter": "Earth as a System: Energy, Matter, and Life",
        },
    },
    "class10": {
        "jesc101.pdf": {"chapter_number": 1, "chapter": "Chemical Reactions and Equations"},
        "jesc102.pdf": {"chapter_number": 2, "chapter": "Acids, Bases and Salts"},
        "jesc103.pdf": {"chapter_number": 3, "chapter": "Metals and Non-metals"},
        "jesc104.pdf": {"chapter_number": 4, "chapter": "Carbon and its Compounds"},
        "jesc105.pdf": {"chapter_number": 5, "chapter": "Life Processes"},
        "jesc106.pdf": {"chapter_number": 6, "chapter": "Control and Coordination"},
        "jesc107.pdf": {"chapter_number": 7, "chapter": "How do Organisms Reproduce?"},
        "jesc108.pdf": {"chapter_number": 8, "chapter": "Heredity"},
        "jesc109.pdf": {"chapter_number": 9, "chapter": "Light – Reflection and Refraction"},
        "jesc110.pdf": {"chapter_number": 10, "chapter": "The Human Eye and the Colourful World"},
        "jesc111.pdf": {"chapter_number": 11, "chapter": "Electricity"},
        "jesc112.pdf": {"chapter_number": 12, "chapter": "Magnetic Effects of Electric Current"},
        "jesc113.pdf": {"chapter_number": 13, "chapter": "Our Environment"},
    },
    "class9_science": {
        "iesc101.pdf": {
            "chapter_number": 1,
            "chapter": "Exploration: Entering the World of Secondary Science",
        },
        "iesc102.pdf": {"chapter_number": 2, "chapter": "Cell: The Building Block of Life"},
        "iesc103.pdf": {"chapter_number": 3, "chapter": "Tissues in Action"},
        "iesc104.pdf": {"chapter_number": 4, "chapter": "Describing Motion Around Us"},
        "iesc105.pdf": {"chapter_number": 5, "chapter": "Exploring Mixtures and their Separation"},
        "iesc106.pdf": {"chapter_number": 6, "chapter": "How Forces Affect Motion"},
        "iesc107.pdf": {"chapter_number": 7, "chapter": "Work, Energy, and Simple Machines"},
        "iesc108.pdf": {"chapter_number": 8, "chapter": "Journey Inside the Atom"},
        "iesc109.pdf": {"chapter_number": 9, "chapter": "Atomic Foundations of Matter"},
        "iesc110.pdf": {
            "chapter_number": 10,
            "chapter": "Sound Waves: Characteristics and Applications",
        },
        "iesc111.pdf": {"chapter_number": 11, "chapter": "Reproduction: How Life Continues"},
        "iesc112.pdf": {
            "chapter_number": 12,
            "chapter": "Patterns in Life: Diversity and Classification",
        },
        "iesc113.pdf": {
            "chapter_number": 13,
            "chapter": "Earth as a System: Energy, Matter, and Life",
        },
    },
    "class9_mathematics": {
        "iemh101.pdf": {
            "chapter_number": 1,
            "chapter": "Orienting Yourself: The Use of Coordinates",
        },
        "iemh102.pdf": {"chapter_number": 2, "chapter": "Introduction to Linear Polynomials"},
        "iemh103.pdf": {"chapter_number": 3, "chapter": "The World of Numbers"},
        "iemh104.pdf": {"chapter_number": 4, "chapter": "Exploring Algebraic Identities"},
        "iemh105.pdf": {"chapter_number": 5, "chapter": "I'm Up and Down, and Round and Round"},
        "iemh106.pdf": {"chapter_number": 6, "chapter": "Measuring Space: Perimeter and Area"},
        "iemh107.pdf": {
            "chapter_number": 7,
            "chapter": "The Mathematics of Maybe: Introduction to Probability",
        },
        "iemh108.pdf": {
            "chapter_number": 8,
            "chapter": "Predicting What Comes Next: Exploring Sequences and Progressions",
        },
    },
    "class10_science": {
        "jesc101.pdf": {"chapter_number": 1, "chapter": "Chemical Reactions and Equations"},
        "jesc102.pdf": {"chapter_number": 2, "chapter": "Acids, Bases and Salts"},
        "jesc103.pdf": {"chapter_number": 3, "chapter": "Metals and Non-metals"},
        "jesc104.pdf": {"chapter_number": 4, "chapter": "Carbon and its Compounds"},
        "jesc105.pdf": {"chapter_number": 5, "chapter": "Life Processes"},
        "jesc106.pdf": {"chapter_number": 6, "chapter": "Control and Coordination"},
        "jesc107.pdf": {"chapter_number": 7, "chapter": "How do Organisms Reproduce?"},
        "jesc108.pdf": {"chapter_number": 8, "chapter": "Heredity"},
        "jesc109.pdf": {"chapter_number": 9, "chapter": "Light – Reflection and Refraction"},
        "jesc110.pdf": {"chapter_number": 10, "chapter": "The Human Eye and the Colourful World"},
        "jesc111.pdf": {"chapter_number": 11, "chapter": "Electricity"},
        "jesc112.pdf": {"chapter_number": 12, "chapter": "Magnetic Effects of Electric Current"},
        "jesc113.pdf": {"chapter_number": 13, "chapter": "Our Environment"},
    },
    "class10_mathematics": {
        "jemh101.pdf": {"chapter_number": 1, "chapter": "Real Numbers"},
        "jemh102.pdf": {"chapter_number": 2, "chapter": "Polynomials"},
        "jemh103.pdf": {
            "chapter_number": 3,
            "chapter": "Pair of Linear Equations in Two Variables",
        },
        "jemh104.pdf": {"chapter_number": 4, "chapter": "Quadratic Equations"},
        "jemh105.pdf": {"chapter_number": 5, "chapter": "Arithmetic Progressions"},
        "jemh106.pdf": {"chapter_number": 6, "chapter": "Triangles"},
        "jemh107.pdf": {"chapter_number": 7, "chapter": "Coordinate Geometry"},
        "jemh108.pdf": {"chapter_number": 8, "chapter": "Introduction to Trigonometry"},
        "jemh109.pdf": {"chapter_number": 9, "chapter": "Some Applications of Trigonometry"},
        "jemh110.pdf": {"chapter_number": 10, "chapter": "Circles"},
        "jemh111.pdf": {"chapter_number": 11, "chapter": "Areas Related to Circles"},
        "jemh112.pdf": {"chapter_number": 12, "chapter": "Surface Areas and Volumes"},
        "jemh113.pdf": {"chapter_number": 13, "chapter": "Statistics"},
        "jemh114.pdf": {"chapter_number": 14, "chapter": "Probability"},
    },
}


class CurriculumService:
    """Provides access to NCERT textbook syllabus, chapters, and resolver utilities."""

    def __init__(self, mapping_path: Optional[str] = None):
        self.mapping_path = mapping_path or str(config.mapping_file_path)
        self._cached_mapping: Optional[Dict[str, Any]] = None

    def get_mapping(self) -> Dict[str, Any]:
        """Loads and caches the raw JSON curriculum mapping."""
        if self._cached_mapping is not None:
            return self._cached_mapping

        if os.path.exists(self.mapping_path):
            try:
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self._cached_mapping = json.load(f)
                    return self._cached_mapping
            except Exception as e:
                logger.error(f"Error loading {self.mapping_path}: {e}")

        # Fallback to built-in curriculum mapping
        self._cached_mapping = DEFAULT_CURRICULUM_MAPPING
        return self._cached_mapping

    def get_chapters_for_grade(
        self, class_level: int, subject: str = "Science"
    ) -> List[ChapterInfo]:
        """Returns sorted list of all chapters in a grade and subject (Class 9 or 10, Science or Mathematics)."""
        mapping = self.get_mapping()
        class_int = int(class_level)
        subj_clean = str(subject).strip().lower()
        is_math = "math" in subj_clean

        if is_math:
            class_key = f"class{class_int}_mathematics"
            subj_canonical = "Mathematics"
        else:
            class_key = f"class{class_int}_science"
            subj_canonical = "Science"

        class_map = mapping.get(class_key)
        if not class_map and not is_math:
            # Legacy fallback for pure class key
            class_map = mapping.get(f"class{class_int}", {})

        if not class_map:
            class_map = {}

        chapters = []
        for fname, info in class_map.items():
            chapters.append(
                ChapterInfo(
                    chapter_number=int(info.get("chapter_number", 0)),
                    chapter_title=str(info.get("chapter", "")),
                    filename=fname,
                    class_level=class_int,
                    subject=subj_canonical,
                )
            )

        chapters.sort(key=lambda x: x.chapter_number)
        return chapters

    def resolve_chapter(
        self,
        class_level: int,
        chapter_identifier: Union[str, int],
        subject: str = "Science",
    ) -> Tuple[int, str]:
        """
        Resolves chapter identifier (int, digit str, or title substring) into
        (chapter_number, canonical_title) for a specific class and subject.
        """
        try:
            class_int = int(class_level)
        except (ValueError, TypeError):
            raise CurriculumError(f"Invalid class level: {class_level}. Must be 9 or 10.")

        if class_int not in (9, 10):
            raise CurriculumError(
                f"Invalid class level: {class_int}. Supported class levels are 9 and 10."
            )

        subj_clean = str(subject).strip().lower()
        is_math = "math" in subj_clean
        subj_canonical = "Mathematics" if is_math else "Science"

        mapping = self.get_mapping()
        class_key = f"class{class_int}_mathematics" if is_math else f"class{class_int}_science"
        class_map = mapping.get(class_key)
        if not class_map and not is_math:
            class_map = mapping.get(f"class{class_int}", {})

        if not class_map:
            raise CurriculumError(
                f"No curriculum mapping data found for Class {class_int} {subj_canonical}"
            )

        # Case 1: Integer or numeric string
        if isinstance(chapter_identifier, int) or (
            isinstance(chapter_identifier, str) and chapter_identifier.strip().isdigit()
        ):
            target_num = int(chapter_identifier)
            for fname, info in class_map.items():
                if int(info.get("chapter_number", 0)) == target_num:
                    return target_num, str(info.get("chapter", ""))
            raise ChapterNotFoundError(
                f"Chapter number {target_num} not found in Class {class_int} NCERT {subj_canonical}."
            )

        # Case 2: String matching
        clean_query = str(chapter_identifier).strip().lower()
        if ":" in clean_query:
            clean_query = clean_query.split(":", 1)[1].strip()
        elif "-" in clean_query:
            clean_query = clean_query.split("-", 1)[1].strip()

        # Exact / Substring search
        for fname, info in class_map.items():
            ch_title = str(info.get("chapter", ""))
            ch_title_lower = ch_title.lower()
            if (
                clean_query == ch_title_lower
                or clean_query in ch_title_lower
                or ch_title_lower in clean_query
            ):
                return int(info.get("chapter_number", 0)), ch_title

        # Keyword match
        words = [w for w in clean_query.split() if len(w) > 3]
        for fname, info in class_map.items():
            ch_title = str(info.get("chapter", ""))
            if any(w in ch_title.lower() for w in words):
                return int(info.get("chapter_number", 0)), ch_title

        raise ChapterNotFoundError(
            f"Could not resolve chapter '{chapter_identifier}' for Class {class_int} {subj_canonical}."
        )

    def get_next_chapter(
        self, class_level: int, current_chapter_num: int, subject: str = "Science"
    ) -> Tuple[int, str, bool]:
        """
        Finds the next sequential chapter in the NCERT curriculum.
        Returns: (next_chapter_number, next_chapter_title, has_more_chapters)
        """
        chapters = self.get_chapters_for_grade(class_level, subject=subject)
        subj_name = "Mathematics" if "math" in str(subject).lower() else "Science"
        if not chapters:
            return current_chapter_num, f"General {subj_name}", False

        for idx, ch in enumerate(chapters):
            if ch.chapter_number == current_chapter_num:
                if idx + 1 < len(chapters):
                    next_ch = chapters[idx + 1]
                    return next_ch.chapter_number, next_ch.chapter_title, True
                else:
                    return ch.chapter_number, ch.chapter_title, False

        return chapters[0].chapter_number, chapters[0].chapter_title, True


# Singleton instance
curriculum_service = CurriculumService()


def get_ncert_curriculum(class_level: int, subject: str = "Science") -> List[Dict[str, Any]]:
    """
    Retrieves the authoritative NCERT curriculum for a specific class (9 or 10) and subject (Science or Mathematics).
    Guarantees strict class and subject scoping with zero cross-contamination.

    Args:
        class_level: 9 or 10 (int)
        subject: "Science" or "Mathematics" (str)

    Returns:
        List of chapter dictionaries containing chapter_number, chapter, chapter_id, filename, pdf_path, and subject.
    """
    try:
        cls_int = int(class_level)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid class_level {class_level!r}. Must be an integer 9 or 10.")

    if cls_int not in (9, 10):
        raise ValueError(
            f"Unsupported class_level {cls_int}. Only Class 9 and Class 10 are supported."
        )

    subj_clean = str(subject).strip().lower()
    is_math = "math" in subj_clean
    subj_canonical = "Mathematics" if is_math else "Science"
    subj_slug = "math" if is_math else "science"

    chapters = curriculum_service.get_chapters_for_grade(cls_int, subject=subj_canonical)
    results = []
    folder_name = f"class{cls_int}_{'maths' if is_math else 'sci'}"
    for ch in chapters:
        slug = (
            ch.chapter_title.lower()
            .replace(" ", "_")
            .replace("–", "-")
            .replace(":", "")
            .replace("'", "")
        )
        chapter_id = f"class{cls_int}_{subj_slug}_{slug}"
        pdf_path = f"data/{folder_name}/{ch.filename}"
        static_url = f"app/static/{folder_name}/{ch.filename}"
        results.append(
            {
                "class_level": cls_int,
                "subject": subj_canonical,
                "chapter_id": chapter_id,
                "chapter_number": ch.chapter_number,
                "chapter": ch.chapter_title,
                "filename": ch.filename,
                "pdf_path": pdf_path,
                "static_url": static_url,
            }
        )
    return results


def ensure_static_assets() -> None:
    """Ensures that the static/ directory contains PDF assets for Streamlit static serving."""
    import shutil

    for cls_int in (9, 10):
        for sub_dir in (f"class{cls_int}_sci", f"class{cls_int}_maths", f"class{cls_int}"):
            src_dir = os.path.join("data", sub_dir)
            dst_dir = os.path.join("static", sub_dir)
            if os.path.isdir(src_dir):
                os.makedirs(dst_dir, exist_ok=True)
                for fname in os.listdir(src_dir):
                    if fname.endswith(".pdf"):
                        dst_path = os.path.join(dst_dir, fname)
                        if not os.path.exists(dst_path):
                            try:
                                shutil.copy2(os.path.join(src_dir, fname), dst_path)
                            except Exception:
                                pass


def get_chapter_pdf(
    class_level: int, chapter_identifier: Union[int, str], subject: str = "Science"
) -> Dict[str, Any]:
    """
    Resolves the authoritative NCERT textbook PDF for a specific class, subject, and chapter.
    Guarantees class and subject isolation via composite key (class_level, subject, chapter_identifier).

    Args:
        class_level: 9 or 10 (int)
        chapter_identifier: Chapter number (int) or Chapter title (str)
        subject: "Science" or "Mathematics" (str)

    Returns:
        Dict with class_level, subject, chapter_id, chapter_number, chapter_name, filename, pdf_path, static_url, exists.
    """
    try:
        cls_int = int(class_level)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid class_level {class_level!r}. Must be an integer 9 or 10.")

    if cls_int not in (9, 10):
        raise ValueError(
            f"Unsupported class_level {cls_int}. Only Class 9 and Class 10 are supported."
        )

    subj_clean = str(subject).strip().lower()
    is_math = "math" in subj_clean
    subj_canonical = "Mathematics" if is_math else "Science"
    subj_slug = "math" if is_math else "science"

    ch_num, ch_title = curriculum_service.resolve_chapter(
        cls_int, chapter_identifier, subject=subj_canonical
    )

    # Lookup authoritative filename
    class_key = f"class{cls_int}_mathematics" if is_math else f"class{cls_int}_science"
    class_map = curriculum_service.get_mapping().get(class_key, {})
    if not class_map and not is_math:
        class_map = curriculum_service.get_mapping().get(f"class{cls_int}", {})

    filename = None
    for fname, info in class_map.items():
        if info.get("chapter_number") == ch_num or info.get("chapter") == ch_title:
            filename = fname
            break

    if is_math:
        prefix = "iemh1" if cls_int == 9 else "jemh1"
    else:
        prefix = "iesc1" if cls_int == 9 else "jesc1"

    if not filename:
        filename = f"{prefix}{ch_num:02d}.pdf"

    folder_name = f"class{cls_int}_{'maths' if is_math else 'sci'}"
    pdf_path = os.path.join("data", folder_name, filename)
    clean_pdf_path = pdf_path.replace("\\", "/")
    slug = ch_title.lower().replace(" ", "_").replace("–", "-").replace(":", "").replace("'", "")
    chapter_id = f"class{cls_int}_{subj_slug}_{slug}"
    static_url = f"app/static/{folder_name}/{filename}"
    external_url = f"https://ncert.nic.in/textbook.php?{prefix}=1-14"
    official_pdf_url = f"https://ncert.nic.in/textbook/pdf/{filename}"

    return {
        "class_level": cls_int,
        "subject": subj_canonical,
        "chapter_id": chapter_id,
        "chapter_number": ch_num,
        "chapter_name": ch_title,
        "filename": filename,
        "pdf_path": clean_pdf_path,
        "static_url": static_url,
        "external_url": external_url,
        "official_pdf_url": official_pdf_url,
        "exists": os.path.isfile(pdf_path),
    }


# Automatically ensure static PDF directory is ready for Streamlit static serving
try:
    ensure_static_assets()
except Exception as _e:
    logger.warning(f"Static assets initialization warning: {_e}")
