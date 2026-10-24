"""河南：由河南省教育考试院 2026 年上半年考试日程（官方 PDF）生成 provinces/henan.json 的开设记录。
河南官网与考生服务平台对非浏览器请求返回 412（反爬），下半年日程、主考学校表、专业计划均未能取得，如实标待查。
用法：python -X utf8 build_henan.py <下载目录>
"""
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
PDF = "https://www.haeea.cn/attach/file/20260105/20260105084606_6071_ae89791d.pdf"
NOTE = "河南省高等教育自学考试 2026 年上半年考试日程安排（官方 PDF）；专业代码为省内原代码、名称为调整后名称，据名称对应国标专业；主考院校待查（日程不含主考学校，官网 412 反爬未取得主考表）"


def off(major, local, name):
    return {"major": major, "track": None, "local_code": local, "status": "open", "hosts": [],
            "matched_by": f"日程表专业名称「{name}（专升本）」",
            "complete": {"courses": False, "credits": False, "textbook": False},
            "verify": V(PDF, NOTE)}


offerings = [
    off("080901", "080702", "计算机科学与技术"), off("080901", "082208", "计算机科学与技术"),
    off("080902", "080711", "软件工程"), off("080902", "080720", "软件工程"),
    off("080702", "080705", "电子科学与技术"),
    off("080701", "110110", "电子信息工程"),
]
write_province("henan", {
    "authority": {"name": "河南省教育考试院", "url": "https://www.haeea.cn/", "verify": V(PDF, "站点域名 haeea.cn，署名河南省教育考试院；自学考试由其自学考试处负责")},
    "selfstudy_portal": {"name": "河南省高等教育自学考试考生服务平台", "url": "https://zkwb.haeea.cn/ZKService/default.aspx", "verify": V(PDF, "平台名称取自搜索结果标题；站点对非浏览器请求返回 412，未能打开核实内容")},
    "calendar": [{"session": "2026-04", "exam": "2026-04-11~12", "note": "报名时间未取得", "verify": V(PDF)}],
    "policy": {"entry": None, "graduate": None, "degree": None, "exemption": None},
    "offerings": offerings, "plans": [], "events": [],
})
sha = hashlib.sha256((DL / "ha_sched04.pdf").read_bytes()).hexdigest()
save_evidence("henan", "ha_sched04.txt", (DL / "ha_sched04.txt").read_text(encoding="utf-8"), PDF, "河南省高等教育自学考试 2026 年上半年考试日程安排；pypdf 抽取", sha)
print("henan ok")
