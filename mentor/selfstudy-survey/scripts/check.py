#!/usr/bin/env python3
"""自考专业调查的验证入口：数据纪律校验、id 与端口对账、前端构建、cargo check。

这是参考类应用，正确性靠数据纪律（ADR 0186）：每条事实要么带来源与核对日期，要么如实标 pending；
课程表只收 official / notice 来源。机器能拦的结构错误在这里拦，内容对不对靠 leader 抽查原文。

用法：
    python3 scripts/check.py               # 全部检查
    python3 scripts/check.py --skip-rust   # 跳过 cargo check
    python3 scripts/check.py --data-only   # 只校验数据（采集时自查用）
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
APP_JSON = ROOT / "app.json"
EXPECTED_ID = "selfstudy-survey"
EXPECTED_PORT = 1535
PROVINCES = [
    "beijing", "tianjin", "hebei", "shanxi", "neimenggu", "liaoning", "jilin", "heilongjiang",
    "shanghai", "jiangsu", "zhejiang", "anhui", "fujian", "jiangxi", "shandong", "henan",
    "hubei", "hunan", "guangdong", "guangxi", "hainan", "chongqing", "sichuan", "guizhou",
    "yunnan", "xizang", "shaanxi", "gansu", "qinghai", "ningxia", "xinjiang",
]
CATALOG_PROV = PROVINCES
LEVELS = {"official", "notice", "report", "pending"}
HARD_LEVELS = {"official", "notice"}  # 课程表、政策只收这两级
STATUS = {"open", "stopped", "upcoming", "none", "pending"}
CATEGORY = {"public", "basic", "core", "required", "elective", "topup", "practice", "graduation"}
EXAM = {"unified", "provincial", "host", None}
PLAN_STATE = {"current", "legacy", "upcoming", "superseded"}
COURSE_KIND = {"theory", "practice", "mixed", "graduation"}
TEXTBOOK_KIND = {"national", "host", "provincial", "other", None}  # None＝来源未标明教材性质
EVENT_KIND = {"new-plan", "stop", "code-change", "policy", "other"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_OR_DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
SESSION = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
COURSE_CODE = re.compile(r"^\d{5}$")
PLAN_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$")
BANNED = ("TODO", "待补", "占位", "FIXME")
ERRORS: list[str] = []
TODAY = datetime.date.today().isoformat()


def fail(msg: str) -> None:
    ERRORS.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"{path.relative_to(ROOT)}: {e}")
        return None


def check_verify(v, where: str, allowed: set[str] = LEVELS, need_real: bool = False) -> None:
    """verify 规则（DESIGN.md §2）：pending 不带来源日期；其余必须 https 来源 + 日期，且日期不在未来。"""
    if not isinstance(v, dict):
        fail(f"{where}: verify 缺失")
        return
    level = v.get("level")
    if level not in LEVELS:
        fail(f"{where}: verify.level 只能是 {sorted(LEVELS)}")
        return
    if level not in allowed:
        fail(f"{where}: 这里只收 {sorted(allowed)} 级来源，实际 {level}")
    if level == "pending":
        if need_real:
            fail(f"{where}: 有结论的数据不能是 pending")
        if v.get("source") or v.get("date"):
            fail(f"{where}: pending 不该带 source/date")
        return
    if not str(v.get("source", "")).startswith(("https://", "http://")):
        fail(f"{where}: 需要 http(s) 来源")  # 部分省考试院只提供 http，不强求 https
    d = str(v.get("date", ""))
    if not DATE.match(d):
        fail(f"{where}: verify.date 必须是 YYYY-MM-DD")
    elif d > TODAY:
        fail(f"{where}: verify.date {d} 在未来")


def check_identity() -> None:
    app = load(APP_JSON)
    if not app:
        return
    if app.get("id") != EXPECTED_ID:
        fail(f"app.json: id 应为 {EXPECTED_ID}，实际 {app.get('id')!r}")
    dev = app.get("dev", {})
    port = str(dev.get("ready", {}).get("http", "")).rsplit(":", 1)[-1]
    if port != str(EXPECTED_PORT):
        fail(f"app.json: dev.ready.http 端口应为 {EXPECTED_PORT}，实际 {port!r}")
    if dev.get("binary") != f"athena-{EXPECTED_ID}":
        fail(f"app.json: dev.binary 应为 athena-{EXPECTED_ID}")
    if "progress" in app:
        fail("app.json: 图谱/参考类不建进度库，不应有 progress 声明")
    for path in (ROOT / "vite.config.ts", ROOT / "src-tauri" / "tauri.conf.json"):
        if str(EXPECTED_PORT) not in path.read_text(encoding="utf-8"):
            fail(f"{path.relative_to(ROOT)}: 找不到端口 {EXPECTED_PORT}（三处必须一致）")


def merge_shards(key: str) -> dict | None:
    """content/<key>/*.json 按成员分文件存放，合并读取；同键必须同内容，否则是两边采集口径冲突。"""
    merged: dict = {}
    owner: dict[str, str] = {}
    for f in sorted((CONTENT / key).glob("*.json")):
        d = load(f)
        if d is None:
            return None
        for k, v in (d.get(key) or {}).items():
            if k in merged and merged[k] != v:
                fail(f"{key}[{k}]: {owner[k]} 与 {f.name} 的内容不一致，请协调后统一")
            merged[k] = v
            owner.setdefault(k, f.name)
    return {key: merged}


def check_data() -> None:
    print("== 数据校验 ==", flush=True)
    scope = load(CONTENT / "scope.json")
    courses_doc = merge_shards("courses")
    books_doc = merge_shards("textbooks")
    athena = load(CONTENT / "athena-map.json")
    if not (scope and courses_doc is not None and books_doc is not None and athena is not None):
        return

    classes = {c["code"] for c in scope["classes"]}
    majors: dict[str, dict] = {}
    for m in scope["majors"]:
        if m["code"] in majors:
            fail(f"scope: 专业 {m['code']} 重复")
        majors[m["code"]] = m
        if m.get("class") not in classes:
            fail(f"scope: 专业 {m['code']} 的类 {m.get('class')!r} 不存在")
        if m.get("tier") not in {"core", "edge"}:
            fail(f"scope: 专业 {m['code']} 的 tier 只能是 core/edge")

    courses = courses_doc.get("courses", {})
    for code, c in courses.items():
        w = f"courses[{code}]"
        if not COURSE_CODE.match(code):
            fail(f"{w}: 课程代码必须是 5 位数字")
        if not str(c.get("name", "")).strip():
            fail(f"{w}: name 不能为空")
        if c.get("kind") not in COURSE_KIND:
            fail(f"{w}: kind 只能是 {sorted(COURSE_KIND)}")

    books = books_doc.get("textbooks", {})
    for bid, b in books.items():
        w = f"textbooks[{bid}]"
        if not re.match(r"^tb-[a-z0-9]+(-[a-z0-9]+)*$", bid):
            fail(f"{w}: id 格式 tb-<关键词>-<年>-<社>")
        for k in ("title", "publisher", "edition"):
            if not str(b.get(k, "")).strip():
                fail(f"{w}: {k} 不能为空")
        if not isinstance(b.get("authors"), list):
            fail(f"{w}: authors 必须是数组")
        if b.get("kind") not in TEXTBOOK_KIND:
            fail(f"{w}: kind 只能是 {sorted(TEXTBOOK_KIND)}")
        isbn = b.get("isbn")
        if isbn is not None and not re.fullmatch(r"[0-9Xx-]{10,17}", str(isbn)):
            fail(f"{w}: isbn 格式不对（抄不准就写 null）")
        check_verify(b.get("verify"), f"{w}.verify", HARD_LEVELS, need_real=True)

    for code, names in athena.get("map", {}).items():
        if code not in courses:
            fail(f"athena-map: 课程代码 {code} 不在课程库（content/courses/*.json）")
        if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names):
            fail(f"athena-map[{code}]: 必须是显示名字符串数组")

    files = sorted((CONTENT / "provinces").glob("*.json"))
    ids = [f.stem for f in files]
    if ids != sorted(PROVINCES):
        miss = sorted(set(PROVINCES) - set(ids))
        extra = sorted(set(ids) - set(PROVINCES))
        fail(f"provinces: 文件集合不对，缺 {miss}，多 {extra}")
    plan_ids: set[str] = set()
    n_plans = n_off = 0
    for f in files:
        d = load(f)
        if not d:
            continue
        pid = f.stem
        where = f"provinces/{pid}"
        if d.get("id") != pid:
            fail(f"{where}: id 必须等于文件名")
        if d.get("schema") != 1:
            fail(f"{where}: schema 应为 1")
        if not str(d.get("name", "")).strip():
            fail(f"{where}: name 不能为空")
        auth = d.get("authority", {})
        check_verify(auth.get("verify"), f"{where}.authority.verify")
        if auth.get("verify", {}).get("level") == "pending":
            if auth.get("name") or auth.get("url"):
                fail(f"{where}.authority: pending 不该有 name/url")
        else:
            if not auth.get("name"):
                fail(f"{where}.authority: 缺 name")
            if auth.get("url") is not None and not str(auth["url"]).startswith(("https://", "http://")):
                fail(f"{where}.authority: url 只收 http(s)")
        portal = d.get("selfstudy_portal")
        if portal is not None:
            if not str(portal.get("url", "")).startswith("https://") and not str(portal.get("url", "")).startswith("http://"):
                fail(f"{where}.selfstudy_portal: 需要 url")
            check_verify(portal.get("verify"), f"{where}.selfstudy_portal.verify", HARD_LEVELS, need_real=True)
        seen_sessions: set[str] = set()
        for c in d.get("calendar", []):
            w = f"{where}.calendar[{c.get('session')}]"
            if not SESSION.match(str(c.get("session", ""))):
                fail(f"{w}: session 必须是 YYYY-MM")
            if c.get("session") in seen_sessions:
                fail(f"{w}: 考期重复")
            seen_sessions.add(c.get("session"))
            check_verify(c.get("verify"), f"{w}.verify", HARD_LEVELS, need_real=True)
        for k, item in (d.get("policy") or {}).items():
            if item is None:
                continue
            w = f"{where}.policy.{k}"
            if not str(item.get("text", "")).strip():
                fail(f"{w}: text 不能为空（没查到就写 null）")
            check_verify(item.get("verify"), f"{w}.verify", HARD_LEVELS, need_real=True)

        local_plans = {p.get("id"): p for p in d.get("plans", [])}
        for p in d.get("plans", []):
            n_plans += 1
            plan_check(p, f"{where}.plans[{p.get('id')}]", pid, majors, courses, books, plan_ids)
        for o in d.get("offerings", []):
            n_off += 1
            w = f"{where}.offerings[{o.get('major')}/{o.get('track')}]"
            if o.get("major") not in majors:
                fail(f"{w}: 专业 {o.get('major')!r} 不在 scope.json")
            if o.get("status") not in STATUS:
                fail(f"{w}: status 只能是 {sorted(STATUS)}")
            if not isinstance(o.get("hosts"), list):
                fail(f"{w}: hosts 必须是数组")
            if o.get("mode") is not None and not str(o["mode"]).strip():
                fail(f"{w}: mode 不能是空串（四川社会型/应用型这类办学类型，没有就省略）")
            if o.get("matched_by") is not None and not str(o["matched_by"]).strip():
                fail(f"{w}: matched_by 不能是空串（本省专业码映射到国标专业的依据，如「旧专业名称」）")
            comp = o.get("complete")
            if comp is not None and not (isinstance(comp, dict) and set(comp) <= {"courses", "credits", "textbook"} and all(isinstance(v, bool) for v in comp.values())):
                fail(f"{w}: complete 只能是 {{courses, credits, textbook}} 三个布尔")
            if o.get("status") == "pending":
                check_verify(o.get("verify"), f"{w}.verify", {"pending"})
            else:
                check_verify(o.get("verify"), f"{w}.verify", need_real=True)
                if o.get("status") == "open" and o.get("verify", {}).get("level") != "report" and not o.get("hosts")                         and "主考院校待查" not in str(o.get("verify", {}).get("note", "")):
                    fail(f"{w}: 开考且来源可靠时必须写主考院校 hosts；确实查不到的在 verify.note 写「主考院校待查」")
            for ref in o.get("plans", []) or []:
                lp = local_plans.get(ref)
                if lp is None:
                    fail(f"{w}: 引用的计划 {ref!r} 不在本省 plans")
                elif lp.get("major") != o.get("major"):
                    fail(f"{w}: 计划 {ref} 的专业与本条不一致")
        for e in d.get("events", []):
            w = f"{where}.events[{e.get('date')}]"
            if not MONTH_OR_DATE.match(str(e.get("date", ""))):
                fail(f"{w}: date 必须是 YYYY-MM 或 YYYY-MM-DD")
            if e.get("kind") not in EVENT_KIND:
                fail(f"{w}: kind 只能是 {sorted(EVENT_KIND)}")
            if e.get("major") is not None and e["major"] not in majors:
                fail(f"{w}: 专业 {e['major']!r} 不在 scope.json")
            if not str(e.get("text", "")).strip():
                fail(f"{w}: text 不能为空")
            check_verify(e.get("verify"), f"{w}.verify", HARD_LEVELS, need_real=True)

    for f in list(CONTENT.rglob("*.json")):
        blob = f.read_text(encoding="utf-8")
        for banned in BANNED:
            if banned in blob:
                fail(f"{f.relative_to(ROOT)}: 出现 {banned!r}——不留占位（ADR 0129）")
    print(f"31 省文件，开设记录 {n_off} 条，课程计划 {n_plans} 份，课程库 {len(courses)} 门，教材库 {len(books)} 本")


def plan_check(p: dict, w: str, pid: str, majors, courses, books, plan_ids: set[str]) -> None:
    plan_id = p.get("id", "")
    if not PLAN_ID.match(plan_id):
        fail(f"{w}: id 格式不对（小写字母数字连字符）")
    if plan_id in plan_ids:
        fail(f"{w}: id 全局重复")
    plan_ids.add(plan_id)
    if p.get("major") not in majors:
        fail(f"{w}: 专业 {p.get('major')!r} 不在 scope.json")
    if p.get("state") not in PLAN_STATE:
        fail(f"{w}: state 只能是 {sorted(PLAN_STATE)}")
    if not str(p.get("version", "")).strip():
        fail(f"{w}: version 不能为空（版本看不出写「未标注」）")
    if p.get("hosts") is not None and not (isinstance(p["hosts"], list) and all(isinstance(h, str) and h for h in p["hosts"])):
        fail(f"{w}: hosts 若写必须是字符串数组（主考院校以 offerings.hosts 为准，plan 级只在计划间确有差异时写）")
    if p.get("source_files") is not None and not isinstance(p["source_files"], list):
        fail(f"{w}: source_files 必须是数组（证据文件名）")
    for k in ("total_credits", "required_credits"):
        v = p.get(k)
        if v is not None and not (isinstance(v, (int, float)) and v >= 0):
            fail(f"{w}: {k} 必须是非负数或 null")
    check_verify(p.get("verify"), f"{w}.verify", HARD_LEVELS, need_real=True)
    codes: set[str] = set()
    codes_all = {c.get("code") for c in p.get("courses", [])}
    for c in p.get("courses", []):
        cw = f"{w}.courses[{c.get('code')}]"
        code = c.get("code", "")
        if not COURSE_CODE.match(str(code)):
            fail(f"{cw}: 课程代码必须是 5 位数字")
        if code in codes:
            fail(f"{cw}: 本计划内课程重复")
        codes.add(code)
        if code not in courses:
            fail(f"{cw}: 课程代码不在课程库（content/courses/*.json）（先登记课程库）")
        elif c.get("name") != courses[code].get("name") and c.get("name") not in courses[code].get("aliases", []):
            fail(f"{cw}: 名称 {c.get('name')!r} 与课程库 {courses[code].get('name')!r} 不一致（不同写法登记为 aliases）")
        if not isinstance(c.get("credits"), (int, float)) or c["credits"] < 0:
            fail(f"{cw}: credits 必须是非负数")
        if c.get("category") not in CATEGORY:
            fail(f"{cw}: category 只能是 {sorted(CATEGORY)}")
        if c.get("exam") not in EXAM:
            fail(f"{cw}: exam 只能是 unified/provincial/host/null")
        if c.get("textbook") is not None and c["textbook"] not in books:
            fail(f"{cw}: 教材 {c['textbook']!r} 不在教材库（content/textbooks/*.json）")
        if c.get("pair") is not None and c["pair"] not in codes_all:
            fail(f"{cw}: pair {c['pair']!r} 不在本计划课程里")
        if c.get("pair") is not None and c.get("category") != "practice":
            fail(f"{cw}: 只有实践课行可以有 pair")
        pr = c.get("practice")
        if pr is not None and not str(pr.get("type", "")).strip():
            fail(f"{cw}: practice 需要 type")
    if not p.get("courses"):
        fail(f"{w}: 计划没有课程行")


def check_pending() -> None:
    """待人工核实清单（content/pending.json）：结构、分组与省份引用。"""
    path = CONTENT / "pending.json"
    d = load(path)
    if d is None:
        return
    if d.get("schema") != 1:
        fail("pending: schema 应为 1")
    if not DATE.match(str(d.get("updated", ""))):
        fail("pending: updated 必须是 YYYY-MM-DD")
    groups = {g.get("id") for g in d.get("groups", [])}
    if len(groups) != len(d.get("groups", [])):
        fail("pending: groups id 重复")
    seen: set[str] = set()
    for it in d.get("items", []):
        w = f"pending[{it.get('id')}]"
        if not it.get("id") or it["id"] in seen:
            fail(f"{w}: id 缺失或重复")
        seen.add(it.get("id"))
        if it.get("group") not in groups:
            fail(f"{w}: group {it.get('group')!r} 不在 groups")
        if not str(it.get("title", "")).strip():
            fail(f"{w}: title 不能为空")
        if it.get("priority") not in {"high", "medium", "low", None}:
            fail(f"{w}: priority 只能是 high/medium/low")
        provs = it.get("provinces") or ([it["province"]] if it.get("province") else [])
        for pid in provs:
            if pid not in PROVINCES:
                fail(f"{w}: 省份 {pid!r} 不在省 id 集合")
    print(f"待人工核实清单 {len(seen)} 项（human {sum(1 for i in d.get('items', []) if i.get('group') == 'human')}）")


def run(cmd: list[str], step: str) -> None:
    print(f"== {step}", flush=True)
    exe = shutil.which(cmd[0])
    if exe is None:
        fail(f"{step}: 找不到 {cmd[0]}")
        return
    if subprocess.run([exe, *cmd[1:]], cwd=ROOT).returncode != 0:
        fail(f"{step} 失败")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-rust", action="store_true")
    ap.add_argument("--data-only", action="store_true")
    args = ap.parse_args()
    check_identity()
    check_data()
    check_pending()
    if not ERRORS and not args.data_only:
        if not (ROOT / "node_modules").is_dir():
            run(["pnpm", "install"], "安装前端依赖")
        run(["pnpm", "run", "build"], "前端构建")
        if not args.skip_rust:
            run(["cargo", "check", "-p", "athena-selfstudy-survey"], "cargo check")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
