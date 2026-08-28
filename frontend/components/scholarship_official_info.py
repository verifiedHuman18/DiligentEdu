"""Reusable Official Scholarship Government Information Component (Phases 4, 5, 6, 7, 9, 10, 11, 12, 13).

Provides the canonical authoritative footer and disclaimer for all scholarship surfaces:
- Informational separation between discovery tools and government authorities.
- Single global destination link to the National Scholarship Portal (https://scholarships.gov.in).
"""

import json
from pathlib import Path
from typing import Dict, Optional

import streamlit as st


def get_canonical_portal_info(sources_path: Optional[str] = None) -> Dict[str, str]:
    """Retrieve canonical portal source name and URL from sources.json (Phase 5)."""
    default_info = {
        "source_name": "National Scholarship Portal",
        "portal_url": "https://scholarships.gov.in",
        "domain": "scholarships.gov.in",
    }

    try:
        path = Path(sources_path) if sources_path else Path("scholarships/sources.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta = data.get("metadata", {})
                return {
                    "source_name": meta.get("source", default_info["source_name"]),
                    "portal_url": meta.get("portal_url", default_info["portal_url"]),
                    "domain": "scholarships.gov.in",
                }
    except Exception:
        pass

    return default_info


def render_official_scholarship_info(
    source_name: Optional[str] = None,
    source_url: Optional[str] = None,
    custom_note: Optional[str] = None,
) -> None:
    """Renders the official government information and disclaimer banner (Phases 4, 6, 7, 11).

    Parameters:
        source_name: Name of authoritative portal (defaults to sources.json metadata).
        source_url: Canonical portal URL (defaults to https://scholarships.gov.in).
        custom_note: Optional contextual guidance for empty/incomplete profile scenarios.
    """
    info = get_canonical_portal_info()
    name = source_name or info["source_name"]
    url = source_url or info["portal_url"]

    # Phase 7 & 13: Clear disclaimer wording
    disclaimer_text = (
        "Scholarship information is provided for discovery and eligibility guidance. "
        "Final eligibility, selection, application dates and requirements are determined "
        "by the respective scholarship authority. Please verify the latest information "
        f"on the official government portal ({info['domain']}) before applying."
    )

    guidance_intro = custom_note or (
        f"The scholarship information shown above is provided for discovery and eligibility guidance. "
        f"For complete and latest eligibility criteria, application dates, required documents "
        f"and application instructions, visit the official {name}."
    )

    st.markdown(
        f"""
        <div style="background: var(--surface-container-high); border: 1px solid var(--outline-variant); border-left: 4px solid var(--md-primary); border-radius: 12px; padding: 1.5rem; margin-top: 2rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div style="flex: 1; min-width: 280px;">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--on-surface); font-size: 1.15rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                        Official Government Portal Information
                    </h4>
                    <p style="font-size: 0.9rem; color: var(--on-surface); line-height: 1.5; margin: 0 0 0.8rem 0;">
                        {guidance_intro}
                    </p>
                    <div style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.4; background: var(--surface-container-low); padding: 8px 12px; border-radius: 6px; border: 1px dashed var(--outline-variant);">
                        <b>Notice:</b> {disclaimer_text}
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; justify-content: center; align-self: center;">
                    <a href="{url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; text-align: center; background: var(--md-primary); color: var(--on-primary); padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: 700; text-decoration: none; box-shadow: 0 2px 6px rgba(0,0,0,0.15); white-space: nowrap;">
                        Visit {name}
                    </a>
                    <div style="font-size: 0.7rem; color: var(--text-secondary); text-align: center; margin-top: 6px;">
                        {info["domain"]} (New tab)
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
