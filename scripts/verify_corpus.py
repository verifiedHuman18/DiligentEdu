#!/usr/bin/env python3
"""
NCERT Corpus Verification Script (Phase 2.1)
Verifies integrity, text extractability, completeness, and mapping for Class 9 & Class 10 NCERT Science PDFs.
"""

import json
import os
import sys

import pymupdf

# Set UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "metadata", "ncert_mapping.json")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def verify_corpus():
    print("=" * 60)
    print("Checking NCERT corpus...")
    print("=" * 60)

    # 1. Check mapping file
    if not os.path.exists(MAPPING_FILE):
        print(f"❌ Error: Mapping file not found at {MAPPING_FILE}")
        return False

    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    total_chapters_verified = 0
    errors_found = 0

    for class_key in ["class9", "class10"]:
        display_name = "Class 9" if class_key == "class9" else "Class 10"
        expected_prefix = "iesc" if class_key == "class9" else "jesc"
        class_folder = os.path.join(DATA_DIR, class_key)

        print(f"\n{display_name}:")
        if not os.path.exists(class_folder):
            print(f"  ❌ Directory not found: {class_folder}")
            errors_found += 1
            continue

        class_map = mapping.get(class_key, {})
        expected_chapters = set(range(1, 14))
        found_chapters = set()

        # Sort by chapter number
        sorted_files = sorted(class_map.items(), key=lambda item: item[1].get("chapter_number", 0))

        for filename, info in sorted_files:
            ch_num = info.get("chapter_number")
            ch_title = info.get("chapter", "Unknown")
            pdf_path = os.path.join(class_folder, filename)

            # Check prefix consistency
            if not filename.startswith(expected_prefix):
                print(
                    f"  ❌ File naming inconsistency: {filename} does not start with expected prefix '{expected_prefix}'"
                )
                errors_found += 1

            # Check file existence
            if not os.path.exists(pdf_path):
                print(f"  ❌ Missing file: {filename} (Chapter {ch_num})")
                errors_found += 1
                continue

            # Check readability and text extractability
            try:
                doc = pymupdf.open(pdf_path)
                num_pages = len(doc)

                if num_pages == 0:
                    print(f"  ❌ Empty PDF: {filename}")
                    errors_found += 1
                    continue

                total_chars = 0
                for page_idx in range(num_pages):
                    page_text = doc[page_idx].get_text("text")
                    total_chars += len(page_text.strip())

                if total_chars < 500:
                    print(
                        f"  ⚠️ Warning: Low extractable text in {filename} ({total_chars} characters)"
                    )

                found_chapters.add(ch_num)
                total_chapters_verified += 1
                print(
                    f"  ✓ Chapter {ch_num:2d}: {ch_title} ({filename} - {num_pages} pages, {total_chars:,} chars)"
                )

            except Exception as e:
                print(f"  ❌ Error opening {filename}: {e}")
                errors_found += 1

        # Check for missing chapters
        missing = expected_chapters - found_chapters
        if missing:
            print(f"  ❌ Missing chapters in {display_name}: {sorted(list(missing))}")
            errors_found += len(missing)

    print("\n" + "=" * 60)
    if errors_found == 0:
        print(
            f"✅ Corpus verification successful! All {total_chapters_verified} chapters verified and readable."
        )
        print("Mapping file: data/metadata/ncert_mapping.json")
        print("=" * 60)
        return True
    else:
        print(f"❌ Corpus verification finished with {errors_found} errors.")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = verify_corpus()
    sys.exit(0 if success else 1)
