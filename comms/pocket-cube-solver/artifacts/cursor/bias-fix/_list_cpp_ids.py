#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
data = json.loads(
    Path("programming/c-plus-plus/content/curriculum.json").read_text(encoding="utf-8")
)


def walk(node):
    if isinstance(node, dict):
        sid = node.get("id")
        quiz = node.get("quiz")
        if quiz:
            for i, q in enumerate(quiz):
                print(f"{sid}#{i}\t{q['prompt']}")
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for x in node:
            walk(x)


walk(data)
