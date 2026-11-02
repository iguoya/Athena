"""贵州：由两个考期的官方《课程考试安排表》确认范围内本科专业全部不开设。
2026-04 与 2026-10 两期安排表各列 53 个专业（专科 18、本科 35 个口径见各表），本科专业里没有 0807、0809、0808 类；
考试院通告称课程考试日程见该表，各开考专业计划另在其网站与「贵州自考」小程序查看，故安排表即当期开考专业全表。
用法：python -X utf8 build_guizhou_none.py <目录>   目录里放 gz_P020260601415453375982.pdf、gz_sched.txt（10 月表）、gz04_sched.pdf、gz04_sched.pdf.txt（4 月表）
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
N10 = "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/202606/t20260601_90233549.html"
P10 = "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/202606/P020260601415453375982.pdf"
N04 = "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/202512/t20251216_89055430.html"
P04 = "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/202512/P020251218664430474364.pdf"
v = V(N10, f"贵州省招生考试院 2026 年下半年自学考试报名通告附件 2《课程考试安排表》（{P10}）列 53 个专业，其中本科 35 个，无 0807、0809、0808 类专业；"
           f"2026 年上半年（4 月）《课程考试安排表》（通告 {N04}，附件 {P04}）同为 53 个专业、本科专业一致，同样没有此类专业")
p = CONTENT / "provinces" / "guizhou.json"
d = provlib._load(p)
d["offerings"] = none_offerings(load_scope(), set(), v)
provlib._save(p, d)

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "guizhou"
dst.mkdir(parents=True, exist_ok=True)
for src, name, url, note in ((DL / "gz_P020260601415453375982.pdf", "gz_sched_2026-10.pdf", P10, "2026 年下半年课程考试安排表"), (DL / "gz04_sched.pdf", "gz_sched_2026-04.pdf", P04, "2026 年上半年课程考试安排表")):
    shutil.copy2(src, dst / name)
txt10 = (DL / "gz_sched.txt").read_text(encoding="utf-8")
txt04 = (DL / "gz04_sched.pdf.txt").read_text(encoding="utf-8")
save_evidence("guizhou", "gz_sched_2026-10.pdf.txt", txt10, P10, "2026 年下半年课程考试安排表（pymupdf 抽取）", hashlib.sha256((dst / "gz_sched_2026-10.pdf").read_bytes()).hexdigest())
save_evidence("guizhou", "gz_sched_2026-04.pdf.txt", txt04, P04, "2026 年上半年课程考试安排表（pymupdf 抽取）", hashlib.sha256((dst / "gz_sched_2026-04.pdf").read_bytes()).hexdigest())
print("guizhou ok", len(d["offerings"]))
