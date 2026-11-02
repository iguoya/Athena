"""上海：上海市教育考试院《开考专业信息汇总表（2026年）》（官方，2026-01-21 工作提示附件）——全表 36 个新计划专业 + 旧计划 2 个 + 停考过渡专业。
范围内只有 080901 计算机科学与技术（上海交通大学）；该表是官方全表，其余范围内专业写不开设。专业考试计划（沪自考委〔2024〕1号）本轮未取得。
用法：python -X utf8 build_shanghai.py <目录>   目录里放 sh_notice.html、sh_notice.txt、sh_list.pdf、sh_list.pdf.txt
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
NOTICE = "https://www.shmeea.edu.cn/page/04100/20260121/20022.html"
LIST = "https://www.shmeea.edu.cn/download/20260121/01.pdf"
V0 = V(NOTICE, f"上海市高等教育自学考试委员会办公室 2026-01-20《关于上海市高等教育自学考试2026年启用新专业考试计划的工作提示》；附件《开考专业信息汇总表（2026年）》{LIST}")

p = CONTENT / "provinces" / "shanghai.json"
d = provlib._load(p)
d["authority"] = {"name": "上海市教育考试院", "url": "https://www.shmeea.edu.cn/", "verify": V0}
d["calendar"] = [
    {"session": "2026-04", "exam": "2026-04-11~12", "note": "开考课程见沪教考院自考〔2025〕23号《2026年4月上海市高等教育自学考试各专业课程考试日程安排表》（本轮未取得）", "verify": V(NOTICE, "工作提示「考试时间及课程安排」")},
    {"session": "2026-10", "exam": "2026-10-24~25", "note": "开考课程安排称将于 2026-06-30 前公布（本轮未取得）", "verify": V(NOTICE, "工作提示「考试时间及课程安排」")},
]
d["policy"]["exemption"] = {
    "text": "2026 年 1 月 1 日起施行新版《上海市高等教育自学考试课程免考规定》（沪自考委办〔2025〕1 号），符合条件的考生在规定时间内向主考高校提出免考申请；课程与不同学习成果的学分认定与转换办法见沪自考委办〔2025〕2 号。规定全文本轮未取得。",
    "verify": V(NOTICE, "工作提示「其他注意事项」"),
}
d["offerings"] = [{
    "major": "080901", "track": None, "local_code": "080901", "status": "open", "hosts": ["上海交通大学"], "plans": [],
    "matched_by": None, "complete": {"courses": False, "credits": False, "textbook": False},
    "verify": V(NOTICE, f"《开考专业信息汇总表（2026年）》序号 12：上海交通大学，专升本，080901 计算机科学与技术，执行新考试计划（2026 年起）；{LIST}；专业考试计划与课程表本轮未取得"),
}] + none_offerings(load_scope(), {"080901"}, V(NOTICE, f"《开考专业信息汇总表（2026年）》（{LIST}）：执行新考试计划 36 个专业、旧计划 2 个、停考过渡 9 个，全表未列此专业（停考过渡里的 080202 机械设计制造及其自动化不在范围内）"))
d["events"] = [e for e in d["events"] if e.get("date") != "2026-01-01"] + [
    {"date": "2026-01-01", "kind": "new-plan", "text": "按沪自考委〔2024〕1号，2026 年 1 月 1 日起上海高等教育自学考试执行新考试计划，36 个专业开考新计划课程，另有 9 个专业处于停考过渡期；2026 年起 156 门市级统考课程启用新教材新考纲。", "verify": V(NOTICE)},
]
provlib._save(p, d)

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "shanghai"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "sh_list.pdf", dst / "sh_list_2026.pdf")
save_evidence("shanghai", "sh_notice_20260121.txt", (DL / "sh_notice.txt").read_text(encoding="utf-8"), NOTICE, "2026 年启用新专业考试计划的工作提示页面文本", hashlib.sha256((DL / "sh_notice.html").read_bytes()).hexdigest())
save_evidence("shanghai", "sh_list_2026.pdf.txt", (DL / "sh_list.pdf.txt").read_text(encoding="utf-8"), LIST, "开考专业信息汇总表（2026年）PDF，pymupdf 抽取", hashlib.sha256((DL / "sh_list.pdf").read_bytes()).hexdigest())
print("shanghai ok")
