"""陕西：陕西省教育考试院《2026 年陕西省高等教育自学考试课程安排》（36 个专业全表）与 2026 年报名通知。
课程安排表只列课程代码与考次，无学分、无主考学校，因此只入库开设记录（080901、080903 开考）、考期与报名政策，计划留待查。
用法：python -X utf8 build_shaanxi.py <下载目录>
"""
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
N_ARR = "https://www.sneea.cn/info/1032/16811.htm"  # 陕试自考〔2025〕13号：2026 年课程安排（2025-11-28）
P_ARR = "https://www.sneac.com/2025/2026zkkcap2.pdf"  # 附：2026 年陕西省高等教育自学考试课程安排
N_REG = "https://www.sneea.cn/info/1032/16978.htm"  # 2026 年自学考试报名工作的通知（2026-01-14）
NOTE = "主考院校待查（课程安排表不含主考学校；第三方陕西自考网称 080901 主考学校为西安电子科技大学，仅作线索未入库）"


def off(code, name):
    return {"major": code, "track": None, "status": "open", "hosts": [], "plans": [],
            "complete": {"courses": False, "credits": False, "textbook": False},
            "verify": V(P_ARR, f"2026 年陕西省高等教育自学考试课程安排（本科 26 个专业之一：{name}，课程与考次见附表）；" + NOTE)}


scope = load_scope()
offerings = [off("080901", "计算机科学与技术"), off("080903", "网络工程")]
offerings += none_offerings(scope, {"080901", "080903"},
                            V(P_ARR, "2026 年陕西省高等教育自学考试课程安排列出全部 36 个开考专业（专科 10、本科 26），其中无此专业"))
write_province("shaanxi", {
    "authority": {"name": "陕西省教育考试院", "url": "https://www.sneea.cn/", "verify": V(N_ARR)},
    "selfstudy_portal": {"name": "陕西省高等教育自学考试服务平台（经陕西省教育考试院或陕西招生考试信息网进入）", "url": "https://www.sneac.com/", "verify": V(N_REG, "报名通知：登录陕西省教育考试院门户网站或陕西招生考试信息网，进入「高等教育自学考试服务平台」")},
    "calendar": [
        {"session": "2026-04", "exam": "2026-04-11~12", "register": "2026-03-05 8:00~03-11 18:00（首次报考信息注册 03-05~09）；缴费 03-05~03-12 18:00", "verify": V(N_REG, "陕西省教育考试院关于做好 2026 年高等教育自学考试报名工作的通知")},
        {"session": "2026-10", "exam": "2026-10-24~25", "register": "2026-09-05 8:00~09-11 18:00（首次报考信息注册 09-05~09）；缴费 09-05~09-12 18:00", "verify": V(N_REG)},
    ],
    "policy": {
        "entry": {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制均可报名，有特殊要求的专业除外；被给予暂停参加自学考试处理且在停考期内的考生不得报名。", "verify": V(N_REG)},
        "graduate": None, "degree": None, "exemption": None,
    },
    "offerings": offerings, "plans": [],
    "events": [{"date": "2025-11-28", "kind": "policy", "text": "陕试自考〔2025〕13号：公布 2026 年课程安排，全年两次考试（4 月 11—12 日、10 月 24—25 日），共开考 36 个专业（专科 10、本科 26）；金融服务与管理（专科）、大数据与会计（专科）继续执行旧专业计划。", "verify": V(N_ARR)}],
})
sha = lambda p: hashlib.sha256((DL / p).read_bytes()).hexdigest()  # noqa: E731
save_evidence("shaanxi", "sn_kcap2026.txt", (DL / "sn_kcap2026.txt").read_text(encoding="utf-8"), P_ARR, "2026 年陕西省高等教育自学考试课程安排；pypdf 抽取", sha("sn_kcap2026.pdf"))
save_evidence("shaanxi", "sn_notice16811.txt", (DL / "n16811.txt").read_text(encoding="utf-8"), N_ARR, "课程安排通知页文本", sha("n16811.html"))
save_evidence("shaanxi", "sn_notice16978.txt", (DL / "n16978.txt").read_text(encoding="utf-8"), N_REG, "2026 年报名通知页文本", sha("n16978.html"))
print("shaanxi ok")
