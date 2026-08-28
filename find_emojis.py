import os

import emoji


def find_emojis(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    emojis_found = [c for c in content if c in emoji.EMOJI_DATA]
                    if emojis_found:
                        print(f"{path}: {set(emojis_found)}")


find_emojis("frontend")
