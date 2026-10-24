"""宁夏、重庆、西藏、贵州：官方通知页能取得的机构、考期、政策部分（开设矩阵与计划本轮未取得，如实待查）。
用法：python -X utf8 build_lite.py <scratchpad 根目录>   （里面有 dl_nx/ dl_misc/ dl_gz/ 三个下载目录）
"""
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

R = pathlib.Path(sys.argv[1])
EMPTY = {"entry": None, "graduate": None, "degree": None, "exemption": None}


def ev(prov, name, path, url, note, raw):
    save_evidence(prov, name, (R / path).read_text(encoding="utf-8"), url, note, hashlib.sha256((R / raw).read_bytes()).hexdigest())


# ---- 宁夏 ----
NX50 = "https://nxzsks.cn/bkzn4/50.html"
NX22 = "https://nxzsks.cn/bkzn4/22.html"
write_province("ningxia", {
    "authority": {"name": "宁夏教育考试院（宁夏招生考试网）", "url": "https://nxzsks.cn/", "verify": V(NX50)},
    "selfstudy_portal": {"name": "宁夏自考考生服务平台", "url": "https://baoming.nxjyks.cn:20062/login", "verify": V(NX22, "网址取自宁夏招生考试网首页「宁夏2026年高等教育自学考试成绩查询」入口；毕业审定通告称考生在宁夏自考考生服务平台申请毕业")},
    "calendar": [{"session": "2026-04", "exam": "2026-04-11~12", "register": "建档注册 03-02 9:00~03-05 18:00；审核确认 03-02~03-06 12:00；报考课程 03-02~03-06 17:00；缴费 03-02~03-06 18:00", "verify": V(NX50, "宁夏2026年上半年高等教育自学考试报考通告（2026-01-28）")}],
    "policy": {
        "entry": {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制均可报名（有特殊要求的专业除外）；社会考生可报考面向社会开考专业，报考委托助学单位开考专业须与助学单位咨询；区内高职高专（中职中专）在校生可报考衔接自学考试专业；被暂停参加自学考试且在停考期内者不得报考。", "verify": V(NX50)},
        "graduate": {"text": "考完专业考试计划规定的全部课程并取得合格成绩，完成毕业论文（设计）或其他实践性环节并合格，学分达到计划要求，思想品德鉴定合格，课程免考与替换符合规定；申请专升本（独立本科段）毕业须持专科（或以上）学历证书；毕业审定每年两次（上半年初审 5 月 18—22 日、复审 6 月 1—30 日；下半年初审 11 月 16—20 日、复审 12 月 1—30 日），申请本科毕业须提供学信网前置学历电子注册备案表。", "verify": V(NX22, "宁夏教育考试院关于做好 2026 年高等教育自学考试毕业审定工作的通告（2026-03-03）")},
        "degree": None, "exemption": None,
    },
    "offerings": [], "plans": [], "events": [],
})
ev("ningxia", "nx_n50.txt", "dl_nx/n50.txt", NX50, "宁夏2026年上半年报考通告页文本；开考专业与课程安排表为附件，页面无直链未取得", "dl_nx/n50.html")
ev("ningxia", "nx_n22.txt", "dl_nx/n22.txt", NX22, "毕业审定工作通告页文本", "dl_nx/n22.html")

# ---- 重庆 ----
CQ = "https://www.cqksy.cn/web/article/2026-07/24/content_7059.html"
write_province("chongqing", {
    "authority": {"name": "重庆市教育考试院", "url": "https://www.cqksy.cn/", "verify": V(CQ)},
    "selfstudy_portal": {"name": "重庆市高等教育自学考试信息管理系统", "url": "https://zk.cqksy.cn", "verify": V(CQ, "报考须知：登录该系统在线报考")},
    "calendar": [{"session": "2026-10", "register": "2026-09-01 9:00~09-15 15:00；首次报名建档费 48 元/人，报考费 40 元/科", "note": "考试日期须知页未写，待核", "verify": V(CQ, "重庆市2026年下半年高等教育自学考试报名报考须知（2026-07-24）")}],
    "policy": {
        "entry": {"text": "护理专业（专科）限获得中等卫生（或护理）学校护理专业毕业证书且持护士执业证书的在岗护理工作人员报考；护理学专业（专升本）限获得护理（含助产士）专业专科毕业证书且持护士执业证书的在岗护理类专业人员报考；助学考生与行业合作开考专业考生由所属主考学校通过系统集体报名。", "verify": V(CQ)},
        "graduate": None, "degree": None, "exemption": None,
    },
    "offerings": [], "plans": [], "events": [],
})
ev("chongqing", "cq_7059.txt", "dl_misc/cq7059.txt", CQ, "2026 年下半年报名报考须知页文本", "dl_misc/cq7059.html")

# ---- 西藏 ----
XZ = "http://zsks.edu.xizang.gov.cn/57/154/8296.html"
write_province("xizang", {
    "authority": {"name": "西藏自治区教育考试院", "url": "http://zsks.edu.xizang.gov.cn/", "verify": V(XZ)},
    "selfstudy_portal": {"name": "西藏自治区高等教育自学考试信息管理综合平台", "url": "http://zsks.edu.xizang.gov.cn/", "verify": V(XZ, "公告：登录教育考试院官网，点击「自学考试」栏目右侧的该平台报考；平台独立网址未给出，暂填考试院官网")},
    "calendar": [{"session": "2026-10", "exam": "2026-10-24~25", "register": "报考缴费 2026-09-23 15:30~09-29 18:00", "verify": V(XZ, "西藏2026年10月自学考试报名公告（2026-09-23）")}],
    "policy": {
        "entry": {"text": "中华人民共和国公民不受性别、年龄、民族、学历等限制均可报考；报考本科专业的考生须具备国民教育专科（含）以上学历；被给予暂停参加自考处理且在停考期内的考生不得报考。", "verify": V(XZ)},
        "graduate": None,
        "degree": {"text": "自 2025 年起执行《自考主考院校变更的通知》，西藏自治区教育考试院目前只负责毕业证办理，学位证申请事宜由各高校办理。", "verify": V(XZ)},
        "exemption": None,
    },
    "offerings": [], "plans": [],
    "events": [{"date": "2023-10", "kind": "stop", "text": "2023 年 10 月《关于自考停考专业的公告》：停考监所管理（本）、藏语言文学（专、本）、英语（专）、汉语言文学（专）五个专业，2026 年起不再办理毕业、转考等工作。", "verify": V(XZ, "转述自 2026 年 10 月报名公告第五条；停考公告原文未取得")}],
})
ev("xizang", "xz_8296.txt", "dl_misc/xz8296.txt", XZ, "西藏2026年10月自学考试报名公告页文本", "dl_misc/xz8296.html")

# ---- 贵州 ----
GZ = "http://zsksy.guizhou.gov.cn/zxks/ksjh/202404/t20240410_84187881.html"
write_province("guizhou", {
    "authority": {"name": "贵州省招生考试院", "url": "http://zsksy.guizhou.gov.cn/", "verify": V(GZ)},
    "selfstudy_portal": None,
    "calendar": [],
    "policy": {
        "entry": None, "graduate": None,
        "degree": {"text": "本科各专业的学士学位授予条件及要求由相应主考学校制定和发布，各专业考试计划中不做具体说明。", "verify": V(GZ, "贵州省教育厅办公室关于调整我省高等教育自学考试专业考试计划的通知 五（三）")},
        "exemption": {"text": "2024 年 10 月前已取得合格成绩的课程继续有效，2024 年 12 月后可按各专业新旧课程替换表顶替为新计划课程（只能在同一专业内替换，不能跨专业）；「英语（专升本）」可用《替换课程表》中任选的 2 门课程（合计不低于 7 学分且不为本专业包含的课程）替换。", "verify": V(GZ, "通知三（一）（二）")},
    },
    "offerings": [], "plans": [],
    "events": [
        {"date": "2024-04-10", "kind": "new-plan", "text": "贵州省教育厅办公室通知：调整 43 个专业的考试计划并新开考 5 个专业（医学检验技术、食品卫生与营养、工程造价、工业设计、艺术设计），2024 年 10 月起按新计划开考，2024 年 12 月起须按新计划申请毕业；药物制剂（专升本）、农林经济管理（专升本）2024 年 10 月起停止接纳新生，过渡期至 2026 年 10 月，2027 年起不再安排考试。附件《贵州省高等教育自学考试专业考试计划（2024）》调整列表中无 0807/0809 类专业，范围内专业（如 080901 计算机科学与技术）是否仍开考及其计划本轮未能确认。", "verify": V(GZ)},
    ],
})
ev("guizhou", "gz_n84187881.txt", "dl_gz/n84187881.txt", GZ, "调整专业考试计划通知页文本；附件 PDF（345 页）本轮仅核对调整列表，未入库", "dl_gz/n84187881.html")

# ---- 甘肃 ----（官网 ganseea.cn 对非浏览器请求 412/重置，取用靖远县政府网转载的《甘肃省2026年下半年自学考试网报须知》）
GS = "https://www.jingyuan.gov.cn/zfxxgk/bmhxzxxgk/bmdw/jyj/fdzdgknr/jyxx/art/2026/art_1534f5e3dbb6404da7e5c4017b0e56eb.html"
write_province("gansu", {
    "authority": {"name": "甘肃省教育考试院", "url": "https://www.ganseea.cn/", "verify": V(GS, "靖远县人民政府网转载的甘肃省教育考试院网报须知所指官方网站；官网本身对非浏览器请求返回 412，未能直接打开")},
    "selfstudy_portal": {"name": "甘肃省国家教育考试综合管理平台·高等教育自学考试报名系统", "url": "https://kw.ganseea.cn", "verify": V(GS, "须知：登录 https://kw.ganseea.cn 或官网「甘肃省国家教育考试综合管理平台」考生入口选择自学考试报名系统")},
    "calendar": [{"session": "2026-10", "register": "社会型新考生注册及缴电子注册费 2026-09-03 8:30~09-06 18:00；选课缴费 09-03 8:30~09-09 18:00", "note": "考试日期须知未写，开考专业与时间见甘教考自〔2026〕3号报考简章（未取得）", "verify": V(GS, "甘肃省2026年下半年自学考试网报须知（政府网转载，2026-08-13）")}],
    "policy": {"entry": None, "graduate": None, "degree": None, "exemption": None},
    "offerings": [], "plans": [],
    "events": [{"date": "2024-04", "kind": "new-plan", "text": "甘肃自 2024 年上半年起全面实施新专业课程设置，所有考生按新专业代码、名称和课程设置参加报名报考；2026 年起暂停武威市民勤县、古浪县、天祝县分考区。", "verify": V(GS)}],
})
ev("gansu", "gs_bm_gov.txt", "dl_gs/bm_gov.txt", GS, "甘肃省2026年下半年自学考试网报须知（靖远县政府网转载）页文本", "dl_gs/bm_gov.html")
print("lite ok")
