"""测验重做的小工具：用「正确项 + 干扰项 + 目标位置」写题，生成 curriculum.json 要的结构并回写。

题的规格（dict）：
  id, page(可空=章末综合), stem, code(可选), lang(可选), right, wrong[list], pos, why, ref(出处 note)
build() 把正确项插到 pos 位置，其余干扰项按顺序填。
"""
import json
import math
from pathlib import Path

CUR = Path(__file__).resolve().parents[3] / "guide" / "gtkmm" / "content" / "curriculum.json"
SITE = "https://gnome.pages.gitlab.gnome.org/gtkmm-documentation/"


def build(spec):
    wrong = list(spec["wrong"])
    pos = spec["pos"]
    options = wrong[:pos] + [spec["right"]] + wrong[pos:]
    item = {"id": spec["id"]}
    if spec.get("page"):
        item = {"type": spec.get("type", "quiz"), "id": spec["id"], "page_ref": spec["page"]}
        if spec.get("demo_ref"):
            item["demo_ref"] = spec["demo_ref"]
    item["stem"] = spec["stem"]
    if spec.get("code"):
        item["code"] = spec["code"].strip("\n")
        item["lang"] = spec.get("lang", "cpp")
    item["options"] = options
    item["answer"] = pos
    item["explanation"] = spec["why"]
    refs = []
    for r in spec.get("refs", []):
        refs.append(r)
    if not refs:
        loc = f"官方节页 {spec['page']}" if spec.get("page") else spec.get("locator", "本章各节")
        refs.append({"relation": "adapted", "url": SITE, "locator": loc, "note": spec["ref"]})
    item["source_refs"] = refs
    return item


def report(items):
    n = len(items)
    limit = math.ceil(0.4 * n)
    pos = {}
    longest = coded = 0
    for it in items:
        pos[it["answer"]] = pos.get(it["answer"], 0) + 1
        lens = [len(o) for o in it["options"]]
        a = it["answer"]
        if lens[a] == max(lens) and lens.count(max(lens)) == 1:
            longest += 1
        if it.get("code"):
            coded += 1
    print(f"n={n} 位置={dict(sorted(pos.items()))} 上限={limit} 最长即答案={longest} 带代码={coded}(需≥{math.ceil(n/3)})")
    for it in items:
        lens = [len(o) for o in it["options"]]
        flag = " ←答案最长" if lens[it["answer"]] == max(lens) and lens.count(max(lens)) == 1 else ""
        spread = max(lens) / max(1, min(lens))
        if flag or spread > 1.8:
            print(f"  {it['id']}: 选项长度 {lens}{flag}")


def apply(section_id, kp_index, inpage, checkpoint, standard=2):
    raw = CUR.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    data = json.loads(raw.replace("\r\n", "\n"))
    sec = next(s for s in data["sections"] if s["id"] == section_id)
    kp = sec["knowledge_points"][kp_index]
    kp["blocks"] = inpage
    sec["checkpoint"] = checkpoint
    sec["quiz_standard"] = standard
    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    CUR.write_bytes(out.replace("\n", nl).encode("utf-8"))
