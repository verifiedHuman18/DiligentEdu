"""Reusable Minimalist Cards and Badges UI Components (Flat, No Heavy Boxes)."""

import textwrap
from typing import Any, Optional

import streamlit as st


def render_metric_card(label: str, value: Any, delta: Optional[str] = None) -> None:
    """Renders a flat minimalist metric with clean typography (no box)."""
    delta_html = (
        f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem;">{delta}</div>'
        if delta
        else ""
    )
    html = textwrap.dedent(f"""\
<div class="metric-flat">
<div class="metric-label">{label}</div>
<div class="metric-value">{value}</div>
{delta_html}
</div>\
""")
    st.markdown(html, unsafe_allow_html=True)


def format_source_pages(pages: Optional[Any]) -> str:
    """Formats source page references into human-friendly strings (e.g., 'Page 12' or 'Pages 12, 13')."""
    import re

    if not pages:
        return "Referenced in Chapter"
    if isinstance(pages, (int, float)):
        return f"Page {int(pages)}"
    if isinstance(pages, str):
        pages_clean = pages.strip()
        if not pages_clean or pages_clean.lower() in ["none", "[]", "null"]:
            return "Referenced in Chapter"
        if pages_clean.lower().startswith("page"):
            return pages_clean
        nums = re.findall(r"\b\d+\b", pages_clean)
        if len(nums) == 1:
            return f"Page {nums[0]}"
        elif len(nums) > 1:
            return f"Pages {', '.join(nums)}"
        return pages_clean
    if isinstance(pages, list):
        flattened = []
        for p in pages:
            if isinstance(p, (int, float)):
                flattened.append(str(int(p)))
            elif isinstance(p, str):
                nums = re.findall(r"\b\d+\b", p)
                if nums:
                    flattened.extend(nums)
                elif p.strip():
                    flattened.append(p.strip())
        if not flattened:
            return "Referenced in Chapter"
        seen = set()
        unique = [x for x in flattened if not (x in seen or seen.add(x))]
        if len(unique) == 1 and unique[0].isdigit():
            return f"Page {unique[0]}"
        elif all(x.isdigit() for x in unique):
            return f"Pages {', '.join(unique)}"
        return ", ".join(unique)
    return str(pages)


def render_citation_box(
    chapter: str,
    class_level: int,
    pages: Optional[Any] = None,
    explanation: Optional[str] = None,
) -> None:
    """Renders a clean citation line with textbook references (no chunky box)."""
    pages_str = format_source_pages(pages)
    exp_html = (
        f"<div style='margin-bottom: 0.35rem; line-height: 1.5;'>{explanation}</div>"
        if explanation
        else ""
    )
    html = textwrap.dedent(f"""\
<div class="citation-clean">
<div class="citation-title">NCERT Class {class_level} Science — {chapter}</div>
{exp_html}
<div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;"><b>Source:</b> {pages_str}</div>
</div>\
""")
    st.markdown(html, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Returns HTML for a simple textual status badge."""
    status_lower = status.lower()
    if status_lower in ["strong", "performing_well"]:
        return '<span class="minimal-badge badge-accent">STRONG</span>'
    elif status_lower in ["average", "monitor", "improving"]:
        return '<span class="minimal-badge">AVERAGE</span>'
    elif status_lower in ["weak", "intervention_needed"]:
        return '<span class="minimal-badge" style="color: var(--danger-text);">WEAK</span>'
    return f'<span class="minimal-badge">{status.upper()}</span>'


def render_swat_columns(swat_data: Any) -> None:
    """Renders a sleek, overflow-prevented 4-column SWAT matrix with fixed height and internal scrolling."""
    strong = swat_data.get("strong") or swat_data.get("strengths") or []
    average = swat_data.get("average") or swat_data.get("average_topics") or []
    weak = swat_data.get("weak") or swat_data.get("weak_topics") or []
    unattempted = swat_data.get("unattempted") or swat_data.get("unattempted_topics") or []

    def _render_items_html(items, category: str) -> str:
        if not items:
            return '<div class="swat-empty-state">No chapters in this category</div>'
        html_items = []
        for it in items:
            ch_name = it.get("chapter", "Chapter")
            ch_num = it.get("chapter_number")
            num_prefix = (
                f'<span class="swat-item-num">{ch_num}.</span>' if ch_num is not None else ""
            )

            if category == "strong":
                score = it.get("score", 0)
                badge = f'<span class="swat-item-score swat-score-strong">{score}%</span>'
            elif category == "average":
                score = it.get("score", 0)
                badge = f'<span class="swat-item-score swat-score-average">{score}%</span>'
            elif category == "weak":
                score = it.get("score", 0)
                badge = f'<span class="swat-item-score swat-score-weak">{score}%</span>'
            else:
                badge = ""

            html_items.append(
                f'<div class="swat-item-card" title="{ch_name}">'
                f'<div class="swat-item-title">{num_prefix}{ch_name}</div>'
                f"{badge}"
                f"</div>"
            )
        return "".join(html_items)

    strong_body = _render_items_html(strong, "strong")
    avg_body = _render_items_html(average, "average")
    weak_body = _render_items_html(weak, "weak")
    unatt_body = _render_items_html(unattempted, "unattempted")

    board_html = textwrap.dedent(f"""\
<div class="swat-board-grid">
<div class="swat-col-card">
<div class="swat-col-header swat-col-header-strong">
<span>Strong (≥ 70%)</span>
<span class="swat-count-badge">{len(strong)}</span>
</div>
<div class="swat-col-scroll">
{strong_body}
</div>
</div>
<div class="swat-col-card">
<div class="swat-col-header swat-col-header-average">
<span>Average (50%–69%)</span>
<span class="swat-count-badge">{len(average)}</span>
</div>
<div class="swat-col-scroll">
{avg_body}
</div>
</div>
<div class="swat-col-card">
<div class="swat-col-header swat-col-header-weak">
<span>Weak (&lt; 50%)</span>
<span class="swat-count-badge">{len(weak)}</span>
</div>
<div class="swat-col-scroll">
{weak_body}
</div>
</div>
<div class="swat-col-card">
<div class="swat-col-header swat-col-header-unattempted">
<span>Not Attempted</span>
<span class="swat-count-badge">{len(unattempted)}</span>
</div>
<div class="swat-col-scroll">
{unatt_body}
</div>
</div>
</div>\
""")
    st.markdown(board_html, unsafe_allow_html=True)
