import os

import emoji


def strip_emojis(text):
    return emoji.replace_emoji(text, replace="")


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = strip_emojis(content)

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filepath}")


for root, _, files in os.walk("frontend"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

# Fix ↗ in scholarship_official_info.py as it might not be covered by emoji package
filepath = "frontend/components/scholarship_official_info.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if "↗" in content:
        content = content.replace("↗", "")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath} manually for arrow")
