#!/usr/bin/env python3
"""自检三份选项重写补丁（T-003）。

读补丁 + 读原内容，对每个应用打印：
题数、位置占比、正确项最长占比、选项里含中文括号注释的个数、
与原题答案内容是否一致（不同的逐条列出改写前后）。
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
# check_patch.py → bias-fix → cursor → artifacts → pocket-cube-solver → comms → 仓库根
ROOT = Path(__file__).resolve().parents[5]
CONTENT = {
    "snake": ROOT / "programming/snake/content",
    "chinese-chess": ROOT / "programming/chinese-chess/content",
    "c-plus-plus": ROOT / "programming/c-plus-plus/content",
}
# 中文全角括号作「注释套话」标记；ASCII () 留给代码与坐标
PAREN_RE = re.compile(r"（[^）]*）")


def iter_questions(node, section_id=None):
    if isinstance(node, dict):
        sid = node.get("id") if isinstance(node.get("id"), str) else section_id
        choices = node.get("choices") or node.get("options")
        answer = node.get("answer")
        if (
            isinstance(choices, list)
            and len(choices) >= 2
            and all(isinstance(c, str) for c in choices)
            and isinstance(answer, int)
        ):
            qid = node.get("id")
            yield {
                "id": qid,
                "section_id": sid,
                "prompt": node.get("prompt") or "",
                "choices": choices,
                "answer": answer,
            }
        quiz = node.get("quiz")
        if isinstance(quiz, list) and sid:
            for i, item in enumerate(quiz):
                if not isinstance(item, dict):
                    continue
                ch = item.get("choices") or item.get("options")
                ans = item.get("answer")
                if (
                    isinstance(ch, list)
                    and len(ch) >= 2
                    and all(isinstance(c, str) for c in ch)
                    and isinstance(ans, int)
                ):
                    yield {
                        "id": item.get("id") or f"{sid}#{i}",
                        "section_id": sid,
                        "prompt": item.get("prompt") or "",
                        "choices": ch,
                        "answer": ans,
                        "_quiz_index": i,
                    }
            # quiz 已单独展开，勿再递归进 quiz 列表以免重复
            for key, value in node.items():
                if key == "quiz":
                    continue
                yield from iter_questions(value, sid)
            return
        for value in node.values():
            yield from iter_questions(value, sid)
    elif isinstance(node, list):
        for item in node:
            yield from iter_questions(item, section_id)


def load_original(app: str) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for path in sorted(CONTENT[app].rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for q in iter_questions(data):
            qid = q["id"]
            if not qid:
                continue
            if qid in by_id:
                raise SystemExit(f"duplicate id {qid!r} in {app}")
            by_id[qid] = q
    return by_id


def length_ok(choices: list[str], answer: int) -> bool:
    """正确项与每个干扰项长度差不超过 40%（相对正确项）。"""
    correct = len(choices[answer])
    if correct == 0:
        return False
    for i, c in enumerate(choices):
        if i == answer:
            continue
        if abs(len(c) - correct) / correct > 0.40:
            return False
    return True


def unique_longest(choices: list[str], answer: int) -> bool:
    """正确项独占最长（并列不算）。"""
    L = len(choices[answer])
    return all(len(c) < L for i, c in enumerate(choices) if i != answer)


CLAUSE_SPLIT = re.compile(r"[，；：]")


def clause_reuse_violations(patch: list[dict]) -> list[tuple[str, int, list[str]]]:
    """任意 ≥6 字从句若出现在 ≥3 个不同选项中 → 违规。

    返回 [(从句, 出现次数, 选项摘录前几条), ...]
    """
    clause_hits: dict[str, list[str]] = {}
    for item in patch:
        for ci, c in enumerate(item["choices"]):
            seen_parts: set[str] = set()
            for part in CLAUSE_SPLIT.split(c):
                part = part.strip()
                if len(part) < 6 or part in seen_parts:
                    continue
                seen_parts.add(part)
                # 每个选项槽位计一次
                clause_hits.setdefault(part, []).append(f"{item['id']}[{ci}]")
    bad = []
    for clause, hits in sorted(clause_hits.items(), key=lambda x: -len(x[1])):
        if len(hits) >= 3:
            bad.append((clause, len(hits), hits[:5]))
    return bad



def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    overall_ok = True
    for app in ("snake", "chinese-chess", "c-plus-plus"):
        patch_path = HERE / f"{app}.json"
        if not patch_path.exists():
            print(f"\n=== {app} ===\n  MISSING {patch_path.name}")
            overall_ok = False
            continue
        patch = json.loads(patch_path.read_text(encoding="utf-8"))
        original = load_original(app)
        print(f"\n=== {app} ===")
        print(f"  原题 {len(original)} · 补丁 {len(patch)}")

        if len(patch) != len(original):
            print("  FAIL: 题数不一致")
            overall_ok = False

        positions: Counter[int] = Counter()
        longest = 0
        paren = 0
        rewritten: list[tuple[str, str, str]] = []
        missing = []
        extra = []
        bad_len = []
        seen = set()

        for item in patch:
            qid = item["id"]
            choices = item["choices"]
            answer = item["answer"]
            if qid in seen:
                print(f"  FAIL: 补丁重复 id {qid}")
                overall_ok = False
            seen.add(qid)
            if qid not in original:
                extra.append(qid)
                continue
            orig = original[qid]
            if not (0 <= answer < len(choices)):
                print(f"  FAIL: {qid} answer 越界")
                overall_ok = False
                continue
            positions[answer] += 1
            if unique_longest(choices, answer):
                longest += 1
            for c in choices:
                if PAREN_RE.search(c):
                    paren += 1
            old_text = orig["choices"][orig["answer"]]
            new_text = choices[answer]
            if old_text != new_text:
                rewritten.append((qid, old_text, new_text))
            if not length_ok(choices, answer):
                bad_len.append(qid)

        missing = [qid for qid in original if qid not in seen]
        n = len(patch)
        four = [item for item in patch if len(item["choices"]) == 4]
        n4 = len(four)
        pos4 = Counter(item["answer"] for item in four)

        print(f"  四选一题数: {n4}/{n}")
        if n4:
            shares = " ".join(
                f"第{i+1}位 {pos4[i]/n4:.0%}({pos4[i]})" for i in range(4)
            )
            print(f"  答案位置: {shares}")
            for i in range(4):
                share = pos4[i] / n4
                if not (0.18 <= share <= 0.32):
                    print(f"  FAIL: 第{i+1}位占比 {share:.0%} 不在 18%~32%")
                    overall_ok = False
        print(
            f"  正确项独占最长: {longest}/{n} = {longest/n:.0%}"
            if n
            else "  正确项独占最长: n/a"
        )
        if n and not (0.20 <= longest / n <= 0.35):
            print("  FAIL: 正确项独占最长占比不在 20%~35%（并列不计）")
            overall_ok = False
        print(f"  含中文括号选项: {paren}")
        if paren:
            print("  FAIL: 选项含中文括号注释")
            overall_ok = False
        reused = clause_reuse_violations(patch)
        print(f"  重复从句(≥6字且≥3选项): {len(reused)}")
        if reused:
            print("  FAIL: 发现批量填充从句")
            overall_ok = False
            for clause, cnt, samples in reused[:12]:
                print(f"    ×{cnt} 「{clause}」")
                for s in samples:
                    print(f"      - {s}")
        print(f"  正确项措辞改写: {len(rewritten)} 题")
        for qid, old, new in rewritten:
            print(f"    - {qid}")
            print(f"        原: {old}")
            print(f"        新: {new}")
        if missing:
            print(f"  FAIL: 补丁缺少 {len(missing)} 题: {missing[:5]}…")
            overall_ok = False
        if extra:
            print(f"  FAIL: 补丁多出 {len(extra)} 题: {extra[:5]}…")
            overall_ok = False
        if bad_len:
            print(f"  WARN: {len(bad_len)} 题正确项与干扰项长度差>40%: {bad_len[:8]}…")

    print("\n=== 汇总 ===")
    print("PASS" if overall_ok else "FAIL")
    return 0 if overall_ok else 1



if __name__ == "__main__":
    raise SystemExit(main())
