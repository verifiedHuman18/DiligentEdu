"""Phonetic and STEM speech normalizer for NCERT Science and Mathematics (Phases 4, 5, 8).

Provides lightweight normalization of common Speech-to-Text phonetic misrecognitions
specifically for Indian NCERT curriculum terms, scientists, theorems, and mathematical
phrases without altering the core semantics or performing unsolicited LLM rewrites.
"""

import re
from typing import List, Tuple

# Common phonetic misrecognitions -> Authoritative NCERT terms
PHONETIC_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    # Mathematicians & Scientists with full phrases first
    (re.compile(r"\b(you\s*clids?|youclid|euclids)\b", re.IGNORECASE), "Euclid's"),
    (re.compile(r"\b(pythagorus|pythagaras|pythogoras)\b", re.IGNORECASE), "Pythagoras"),
    (re.compile(r"\b(ohms?\s*law)\b", re.IGNORECASE), "Ohm's law"),
    (re.compile(r"\bohms\b", re.IGNORECASE), "Ohm's"),
    (re.compile(r"\bohm\b", re.IGNORECASE), "Ohm"),
    (re.compile(r"\b(bohrs?)\b", re.IGNORECASE), "Bohr's"),
    (re.compile(r"\b(mendeleevs?|mendeleeff)\b", re.IGNORECASE), "Mendeleev's"),
    (re.compile(r"\b(snells?\s*law)\b", re.IGNORECASE), "Snell's law"),
    (re.compile(r"\b(flemings?\s*(left|right)\s*hand\s*rule)\b", re.IGNORECASE), r"Fleming's \2-hand rule"),
    (re.compile(r"\bflemings\b", re.IGNORECASE), "Fleming's"),
    (re.compile(r"\barchimedes\b", re.IGNORECASE), "Archimedes'"),
    (re.compile(r"\brutherfords\b", re.IGNORECASE), "Rutherford's"),
    (re.compile(r"\bmendels\b", re.IGNORECASE), "Mendel's"),
    (re.compile(r"\bthales?\s*theorem\b", re.IGNORECASE), "Thales' Theorem"),
    
    # Common Abbreviations in NCERT Science & Math
    (re.compile(r"\b(h\s*c\s*f|highest common factor)\b", re.IGNORECASE), "HCF"),
    (re.compile(r"\b(l\s*c\s*m|lowest common multiple|least common multiple)\b", re.IGNORECASE), "LCM"),
    (re.compile(r"\b(b\s*p\s*t|basic proportionality theorem)\b", re.IGNORECASE), "Basic Proportionality Theorem (BPT)"),
    (re.compile(r"\b(a\s*p|arithmetic progression)\b", re.IGNORECASE), "Arithmetic Progression (AP)"),
    (re.compile(r"\b(l\s*h\s*s|left hand side)\b", re.IGNORECASE), "LHS"),
    (re.compile(r"\b(r\s*h\s*s|right hand side)\b", re.IGNORECASE), "RHS"),
    
    # Math symbols spoken phonetically
    (re.compile(r"\bsquare\s+root\s+of\s+([a-zA-Z0-9]+)\b", re.IGNORECASE), r"√\1"),
    (re.compile(r"\bcube\s+root\s+of\s+([a-zA-Z0-9]+)\b", re.IGNORECASE), r"∛\1"),
    (re.compile(r"\bsquare\s+of\s+([a-zA-Z0-9]+)\b", re.IGNORECASE), r"\1²"),
    (re.compile(r"\bcube\s+of\s+([a-zA-Z0-9]+)\b", re.IGNORECASE), r"\1³"),
    (re.compile(r"\b([a-zA-Z0-9]+)\s+square(d)?\b", re.IGNORECASE), r"\1²"),
    (re.compile(r"\b([a-zA-Z0-9]+)\s+cube(d)?\b", re.IGNORECASE), r"\1³"),

    (re.compile(r"\bplus\s+or\s+minus\b", re.IGNORECASE), "±"),
    (re.compile(r"\bnot\s+equal\s+to\b", re.IGNORECASE), "≠"),
    (re.compile(r"\bgreater\s+than\s+or\s+equal\s+to\b", re.IGNORECASE), "≥"),
    (re.compile(r"\bless\s+than\s+or\s+equal\s+to\b", re.IGNORECASE), "≤"),
    (re.compile(r"\bdivided\s+by\b", re.IGNORECASE), "/"),
    (re.compile(r"\bequals?\s+to\b", re.IGNORECASE), "="),
]


def normalize_voice_transcript(raw_transcript: str) -> str:
    """
    Cleans and normalizes a speech transcript specifically for NCERT Science & Mathematics.
    
    Performs lightweight phonetic cleanup on recognized words without silently
    altering the student's question intent or delegating to an external LLM.
    
    Args:
        raw_transcript: Raw text returned from Speech-to-Text recognition.
        
    Returns:
        Cleaned and normalized question string ready for user review or RAG retrieval.
    """
    if not raw_transcript or not isinstance(raw_transcript, str):
        return ""
        
    normalized = raw_transcript.strip()
    
    # Apply phonetic and term replacements
    for pattern, replacement in PHONETIC_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
        
    # Collapse multiple whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    # Capitalize first letter only for regular English words (preserves variables like x², y, etc.)
    if normalized:
        first_token = normalized.split()[0]
        # Do not capitalize single variables x, y, z or formulas starting with a variable
        if len(first_token) > 1 and first_token[0].islower() and not first_token.startswith(("x", "y", "z", "a", "b", "c")):
            normalized = normalized[0].upper() + normalized[1:]
        elif len(first_token) > 2 and first_token[0].islower():
            normalized = normalized[0].upper() + normalized[1:]
        
    return normalized

