import os

import emoji


def find_emojis():
    for root, _, files in os.walk("frontend"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if any(char in emoji.EMOJI_DATA for char in line):
                        print(f"{path}:{i+1}:{line.strip()}")


find_emojis()
