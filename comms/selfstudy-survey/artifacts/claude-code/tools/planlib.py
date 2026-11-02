"""把一份官方专业考试计划（逐行抄录的课程表）写进 provinces/<id>.json 的 plans，并登记课程库、挂到对应 offerings。
课程名按课程库已有名称对账（官方写法不同的写进行 note，官方页的「（实践）」后缀按课程库约定去掉，实践行 pair 指理论课）。
"""
from __future__ import annotations

import provlib
from provlib import CONTENT, Shard, V, course_row


def _lib() -> dict:
    out = {}
    for f in (CONTENT / "courses").glob("*.json"):
        out.update(provlib._load(f)["courses"])
    return out


def build_plan(pid, major, version, effective, total, required, rules, rows, grad, verify, graduation_note, source_files):
    """rows: (code, 官方写法, credits, category, pair, note, elective_group)；grad: (code, 官方写法, note)。返回 (plan, courses_shard)。"""
    lib = _lib()
    courses = Shard("courses")
    crow = []

    def norm(name):
        return name.replace("(", "（").replace(")", "）").replace(" ", "")

    for code, name, cr, cat, pair, note, eg in rows:
        name = norm(name)
        base = name[: -len("（实践）")] if name.endswith("（实践）") else name
        n = lib[code]["name"] if code in lib else base
        notes = note
        if n != base and n != name:
            notes = (notes + "；" if notes else "") + f"官方写作「{name}」"
        courses.add(code, {"name": n, "aliases": [], "kind": "practice" if cat == "practice" else "theory", "note": ""})
        crow.append(course_row(code, n, cr, cat, pair=pair, textbook=None, note=notes, elective_group=eg))
    gc, gn, gnote = grad
    gn = norm(gn)
    gname = lib[gc]["name"] if gc in lib else gn
    courses.add(gc, {"name": gname, "aliases": [], "kind": "graduation", "note": ""})
    crow.append(course_row(gc, gname, 0, "graduation", note=(gnote + "；" if gnote else "") + (f"官方写作「{gn}」" if gname != gn else ""), elective_group=None))
    plan = {"id": pid, "major": major, "track": None, "version": version, "effective": effective, "state": "current",
            "total_credits": total, "required_credits": required, "rules": rules, "courses": crow,
            "graduation": {"thesis": True, "credits": 0, "note": graduation_note}, "source_files": source_files, "verify": verify}
    return plan, courses


def attach(province, plan, offering_filter, offering_patch):
    """替换同 id 计划，并把计划挂到匹配 offering_filter(o) 的开设记录上（再用 offering_patch 更新字段）。"""
    p = CONTENT / "provinces" / f"{province}.json"
    d = provlib._load(p)
    d["plans"] = [x for x in d["plans"] if x["id"] != plan["id"]] + [plan]
    hit = 0
    for o in d["offerings"]:
        if offering_filter(o):
            o["plans"] = sorted(set(o.get("plans") or []) | {plan["id"]})
            o.update(offering_patch)
            hit += 1
    assert hit, f"{province}: 没有匹配的开设记录"
    provlib._save(p, d)
    return d
