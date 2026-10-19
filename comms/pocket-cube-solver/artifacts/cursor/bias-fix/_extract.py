#!/usr/bin/env python3
"""Extract all MCQs from the three apps into _source_*.json dumps."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
APPS = {
    "snake": ROOT / "programming/snake/content",
    "chinese-chess": ROOT / "programming/chinese-chess/content",
    "c-plus-plus": ROOT / "programming/c-plus-plus/content",
}


def questions(node):
    if isinstance(node, dict):
        choices = node.get("choices") or node.get("options")
        answer = node.get("answer")
        if (
            isinstance(choices, list)
            and len(choices) >= 2
            and all(isinstance(c, str) for c in choices)
            and isinstance(answer, int)
        ):
            yield {
                "id": node.get("id"),
                "prompt": node.get("prompt")
                or node.get("question")
                or node.get("stem")
                or "",
                "choices": choices,
                "answer": answer,
                "explanation": node.get("explanation") or node.get("rationale") or "",
            }
        for value in node.values():
            yield from questions(value)
    elif isinstance(node, list):
        for item in node:
            yield from questions(item)


def main() -> None:
    for name, content in APPS.items():
        qs = []
        for path in sorted(content.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for q in questions(data):
                q["_file"] = path.relative_to(ROOT).as_posix()
                qs.append(q)
        (OUT / f"_source_{name}.json").write_text(
            json.dumps(qs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        pos = Counter(q["answer"] for q in qs)
        longest = sum(
            1
            for q in qs
            if len(q["choices"][q["answer"]]) == max(len(c) for c in q["choices"])
        )
        nch = Counter(len(q["choices"]) for q in qs)
        print(f"{name}: {len(qs)} questions")
        print(f"  positions: {dict(sorted(pos.items()))} longest={longest}/{len(qs)}")
        print(f"  nchoices: {dict(nch)}")


if __name__ == "__main__":
    main()
