"""Math-to-Speech Converter and TTS Text Preparation Engine (Phases 9, 10, 11, 12, 13, 14).

Provides robust conversion of academic Science and Mathematics text (LaTeX, formulas,
chemical notations, citations) into natural, fluent speech text for browser SpeechSynthesis.

Maintains strict separation between:
- display_text: Full formatted markdown with equations, diagrams, and citations.
- speech_text: Cleaned, natural spoken English representation.
"""

import re
from typing import Optional


def strip_citations_and_metadata(text: str) -> str:
    """
    Removes citation sections, source tags, page markers, and metadata
    so that only the pedagogical explanation is read aloud.
    """
    if not text:
        return ""

    cleaned = text

    # Remove NCERT citations section and everything that follows
    cleaned = re.split(r"(?i)###\s*NCERT\s*Textbook\s*Citations", cleaned)[0]
    
    # Remove Student Reference Material citations section and everything that follows
    cleaned = re.split(r"(?i)###\s*Student\s*Reference\s*Material\s*Citations", cleaned)[0]
    
    # Remove Related questions or Follow-up section if present
    cleaned = re.split(r"(?i)###\s*Related\s*Questions", cleaned)[0]
    cleaned = re.split(r"(?i)###\s*Suggested\s*Follow-ups", cleaned)[0]

    # Remove inline source markers like [SOURCE: ...] or [PAGE: ...] or (Page 123)
    cleaned = re.sub(r"\[SOURCE:[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[PAGE:[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[NCERT[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(Page\s*\d+\)", "", cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()


def _extract_balanced_group(text: str, start_idx: int) -> tuple[Optional[str], int]:
    """Extracts a balanced curly brace group {...} from text starting at start_idx."""
    if start_idx >= len(text) or text[start_idx] != "{":
        return None, start_idx
    depth = 0
    content_start = start_idx + 1
    for i in range(start_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[content_start:i], i + 1
    return None, start_idx


def _replace_latex_fractions(text: str) -> str:
    """Converts \\frac{num}{den} into 'num over den' handling arbitrary nested braces."""
    pattern = r"\\frac\s*\{"
    while True:
        match = re.search(pattern, text)
        if not match:
            break
        
        brace1_start = match.end() - 1
        num, next_idx = _extract_balanced_group(text, brace1_start)
        if num is None:
            break
        
        # Look for next '{'
        while next_idx < len(text) and text[next_idx].isspace():
            next_idx += 1
            
        if next_idx < len(text) and text[next_idx] == "{":
            den, end_idx = _extract_balanced_group(text, next_idx)
            if den is not None:
                replacement = f"{num} over {den}"
                text = text[:match.start()] + replacement + text[end_idx:]
                continue
        break
    return text


def convert_math_to_speech(text: str) -> str:
    """
    Translates mathematical formulas, LaTeX notation, Greek symbols,
    and chemical formulas into naturally spoken English phrases.
    """
    if not text:
        return ""

    s = text

    # 1. Quadratic equation specific: b^2 - 4ac -> "b squared minus 4 a c"
    s = re.sub(r"b\^2\s*-\s*4ac", "b squared minus 4 a c", s, flags=re.IGNORECASE)
    s = re.sub(r"b²\s*-\s*4ac", "b squared minus 4 a c", s, flags=re.IGNORECASE)

    # 2. LaTeX Square roots & roots: \sqrt[n]{x} -> "n-th root of x", \sqrt{x} -> "square root of x"
    s = re.sub(r"\\sqrt\[(\d+)\]\{([^{}]+)\}", r"\1th root of \2", s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"square root of \1", s)
    s = re.sub(r"√\s*\(?([A-Za-z0-9\+\-\s\^]+)\)?", r"square root of \1", s)
    s = re.sub(r"∛\s*\(?([A-Za-z0-9\+\-\s\^]+)\)?", r"cube root of \1", s)

    # 3. Trigonometric Functions (Priority before generic power rules)
    s = re.sub(r"\\sin\^2\s*\\?theta", "sine squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\\cos\^2\s*\\?theta", "cosine squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\\tan\^2\s*\\?theta", "tangent squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\\sec\^2\s*\\?theta", "secant squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"sin²\s*θ", "sine squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"cos²\s*θ", "cosine squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"tan²\s*θ", "tangent squared theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\\sin\s*\\?theta", "sine theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\\cos\s*\\?theta", "cosine theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\\tan\s*\\?theta", "tangent theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\bsin\s*θ", "sine theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\bcos\s*θ", "cosine theta", s, flags=re.IGNORECASE)
    s = re.sub(r"\btan\s*θ", "tangent theta", s, flags=re.IGNORECASE)

    # 4. LaTeX Fractions (Balanced Brace Parsing)
    s = _replace_latex_fractions(s)

    # 5. Powers and Superscripts
    s = re.sub(r"(\w+)²\b", r"\1 squared", s)
    s = re.sub(r"(\w+)³\b", r"\1 cubed", s)
    s = re.sub(r"\(([^\(\)]+)\)²", r"(\1) squared", s)
    s = re.sub(r"\(([^\(\)]+)\)³", r"(\1) cubed", s)
    s = re.sub(r"(\w+)\^2\b", r"\1 squared", s)
    s = re.sub(r"(\w+)\^3\b", r"\1 cubed", s)
    s = re.sub(r"\(([^\(\)]+)\)\^2", r"(\1) squared", s)
    s = re.sub(r"(\w+)\^(\d+)", r"\1 to the power \2", s)
    s = re.sub(r"(\w+)\^\{([^{}]+)\}", r"\1 to the power \2", s)

    # 6. Subscripts (Sequences / Physics / Chem)
    s = re.sub(r"\ba_n\b", "a sub n", s)
    s = re.sub(r"\ba_\{n\}", "a sub n", s)
    s = re.sub(r"\bS_n\b", "S sub n", s)
    s = re.sub(r"\bS_\{n\}", "S sub n", s)
    s = re.sub(r"\ba_1\b", "a sub 1", s)
    s = re.sub(r"\bd\b(?=\s*=|\s+is\s+the\s+common)", "common difference d", s)

    # 7. Greek letters & Math Symbols
    greek_replacements = [
        (r"\\theta\b|θ", "theta"),
        (r"\\pi\b|π", "pi"),
        (r"\\alpha\b|α", "alpha"),
        (r"\\beta\b|β", "beta"),
        (r"\\gamma\b|γ", "gamma"),
        (r"\\delta\b|δ", "delta"),
        (r"\\Delta\b|Δ", "delta"),
        (r"\\lambda\b|λ", "lambda"),
        (r"\\mu\b|μ", "micro"),
        (r"\\Omega\b|Ω", "ohms"),
        (r"\\rho\b|ρ", "rho"),
        (r"\\sigma\b|σ", "sigma"),
        (r"\\pm\b|±", "plus or minus"),
        (r"\\mp\b|∓", "minus or plus"),
        (r"\\neq\b|≠", "is not equal to"),
        (r"\\approx\b|≈", "is approximately equal to"),
        (r"\\leq\b|\\le\b|≤", "is less than or equal to"),
        (r"\\geq\b|\\ge\b|≥", "is greater than or equal to"),
        (r"\\times\b|×", "multiplied by"),
        (r"\\div\b|÷", "divided by"),
        (r"\\infty\b|∞", "infinity"),
        (r"\\sum\b|∑", "sum of"),
        (r"\\Delta\s*x", "change in x"),
    ]
    for pattern, replacement in greek_replacements:
        s = re.sub(pattern, replacement, s)

    # 8. Common Chemical formulas
    chem_replacements = [
        (r"\bH_2O\b|H₂O", "H 2 O"),
        (r"\bCO_2\b|CO₂", "C O 2"),
        (r"\bO_2\b|O₂", "O 2"),
        (r"\bH_2\b|H₂", "H 2"),
        (r"\bN_2\b|N₂", "N 2"),
        (r"\bCH_4\b|CH₄", "methane"),
        (r"\bCaCO_3\b|CaCO₃", "calcium carbonate"),
        (r"\bCaO\b", "calcium oxide"),
        (r"\bCa\(OH\)_2\b|Ca\(OH\)₂", "calcium hydroxide"),
        (r"\bFe_2O_3\b|Fe₂O₃", "iron oxide"),
        (r"\bCuSO_4\b|CuSO₄", "copper sulphate"),
        (r"\bZnSO_4\b|ZnSO₄", "zinc sulphate"),
        (r"\bNaCl\b", "sodium chloride"),
        (r"\bHCl\b", "hydrochloric acid"),
        (r"\bH_2SO_4\b|H₂SO₄", "sulphuric acid"),
        (r"\bHNO_3\b|HNO₃", "nitric acid"),
        (r"\bNaOH\b", "sodium hydroxide"),
    ]
    for pattern, replacement in chem_replacements:
        s = re.sub(pattern, replacement, s)

    # 9. Clean up LaTeX formatting delimiters: $, $$, \text{...}, \mathbf{...}, \mathrm{...}
    s = re.sub(r"\\text\{([^{}]+)\}", r"\1", s)
    s = re.sub(r"\\mathbf\{([^{}]+)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", s)
    s = re.sub(r"\\left\(", "(", s)
    s = re.sub(r"\\right\)", ")", s)
    s = re.sub(r"\\left\[", "[", s)
    s = re.sub(r"\\right\]", "]", s)
    s = re.sub(r"\\left\{", "{", s)
    s = re.sub(r"\\right\}", "}", s)
    s = re.sub(r"\${1,2}", "", s)  # Remove math $ delimiters

    return s


def clean_markdown_for_speech(text: str) -> str:
    """
    Removes markdown markup, code formatting, table pipes, and extra symbols.
    """
    if not text:
        return ""

    s = text

    # Remove code blocks
    s = re.sub(r"```[\s\S]*?```", "", s)
    # Remove inline code backticks
    s = re.sub(r"`([^`]+)`", r"\1", s)

    # Remove headers (### ...)
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.MULTILINE)

    # Remove bold & italics: **text**, *text*, __text__, _text_
    s = re.sub(r"\*\*([^\*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^\*]+)\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"_([^_]+)_", r"\1", s)

    # Remove blockquotes
    s = re.sub(r"^>\s*", "", s, flags=re.MULTILINE)

    # Remove horizontal rules
    s = re.sub(r"^---+$", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\*\*\*+$", "", s, flags=re.MULTILINE)

    # Remove list bullets
    s = re.sub(r"^\s*[\*\-\+]\s+", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\s*\d+\.\s+", "", s, flags=re.MULTILINE)

    # Remove table formatting pipes
    s = re.sub(r"\|", " ", s)
    s = re.sub(r"-{2,}", "", s)

    # Remove emojis and non-standard symbols
    s = re.sub(r"[\U00010000-\U0010ffff]", "", s)

    # Clean redundant whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def prepare_text_for_speech(display_text: str) -> str:
    """
    Master pipeline that transforms rich markdown/LaTeX Tutor responses into
    clean, natural speech-ready text.
    
    1. Strips citations and metadata blocks.
    2. Converts mathematical, Greek, and chemical notation to words.
    3. Cleans markdown styling, headers, and symbols.
    
    Args:
        display_text: The complete formatted markdown response generated by Gemini.
        
    Returns:
        speech_text: Pristine spoken narrative for browser TTS synthesis.
    """
    if not display_text or not isinstance(display_text, str):
        return ""

    # 1. Strip citations and metadata
    narrative = strip_citations_and_metadata(display_text)

    # 2. Convert mathematical and chemical formulas
    narrative = convert_math_to_speech(narrative)

    # 3. Clean markdown formatting
    speech_text = clean_markdown_for_speech(narrative)

    return speech_text
