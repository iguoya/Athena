"""使用者 2026-11-02 在浏览器里下载的甘肃、河南、陕西官方文件入库（这三省官网对程序请求 412，只有真浏览器能打开）。
来源网址取自下载文件的 Zone.Identifier（Windows 记录的下载来源），不是凭印象写的。
只改 provinces/gansu.json、henan.json、shaanxi.json 三个文件里本脚本负责的字段，其余原样保留。
用法：python -X utf8 build_downloads_20261102.py <Downloads 目录> <文本抽取目录>
  文本抽取目录里放各文件的 .txt（pymupdf/openpyxl/HTML 去标签抽取，文件名＝原文件名＋.txt）。
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL, EX = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
EVI = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence"
scope = load_scope()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def keep(province, src, url, note, text_of=None):
    """原文件拷进证据目录；有文本抽取就另存一份 .txt（带 url/fetched/sha256 头）。"""
    d = EVI / province
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, d / src.name)
    if text_of:
        save_evidence(province, src.name + ".txt", (EX / (src.name + ".txt")).read_text(encoding="utf-8"), url, note, sha(src))


def patch_offerings(pid, new_offerings, listed_majors, total_verify):
    """用新记录替换同专业的旧记录，其余 scope 专业按总表写 none。"""
    p = CONTENT / "provinces" / f"{pid}.json"
    d = provlib._load(p)
    keep_old = [o for o in d["offerings"] if o["major"] not in listed_majors and o["status"] != "none"]
    d["offerings"] = new_offerings + keep_old + none_offerings(scope, listed_majors | {o["major"] for o in keep_old}, total_verify)
    provlib._save(p, d)


# ================= 甘肃 =================
GS_H2 = "https://www.ganseea.cn/zixuekaoshi/1820.html"  # 2026 年下半年报考简章（附件为图片：开考专业及课程考试时间安排）
GS_H1 = "https://www.ganseea.cn/zixuekaoshi/1714.html"  # 2026 年上半年报考简章
GS_H1_PDF = "https://www.ganseea.cn/uploads/allimg/20251117/27-25111G43PHO.pdf"
files = DL / "2026年下半年甘肃省高等教育自学考试报考简章_甘肃省教育考试院_files"
H2_HTML = DL / "2026年下半年甘肃省高等教育自学考试报考简章_甘肃省教育考试院.html"
H1_PDF = DL / "27-25111G43PHO.pdf"
keep("gansu", H2_HTML, GS_H2, "甘肃省教育考试院 2026 年下半年报考简章页面文本（发布 2026-03-31）；浏览器另存 HTML，去标签", text_of=True)
keep("gansu", H1_PDF, GS_H1_PDF, "2026 年上半年甘肃省高等教育自学考试开考专业及课程考试时间安排（简章附件 PDF）", text_of=True)
for png in ("31-2603311F1591Q.png", "31-2603311F235525.png", "31-2603311F5334c.png", "31-2603311F3242E.png"):
    shutil.copy2(files / png, (EVI / "gansu"))
(EVI / "gansu" / "images-index.md").write_text(
    "# 甘肃 2026 年下半年开考专业及课程考试时间安排（简章附件，网页内嵌图片）\n\n"
    f"来源页：{GS_H2}（核对 {provlib.DATE}，图片为浏览器另存）。目视转写为 provinces/gansu.json 的依据：\n\n"
    "- 31-2603311F1591Q.png：标题 + 专科 530302/580401/590206/570103K/570116K 及 10 月 24~25 日四个考试时段\n"
    "- 31-2603311F235525.png：专科 510201/520201/570209，专升本 020202/120201K/120203K\n"
    "- 31-2603311F5334c.png：专升本 120901K/120601/030101K/120402/040106/040107/050101\n"
    "- 31-2603311F3242E.png：专升本 050201/080202/080901/081001/101101/030612TK\n\n"
    "合计专科 8 个、专升本 16 个专业；范围内只有 080901 计算机科学与技术。\n", encoding="utf-8")

GS_NOTE_TOTAL = "甘肃省 2026 年下半年高等教育自学考试开考专业及课程考试时间安排（简章附件，24 个专业：专科 8、专升本 16）全表未列此专业；2026 年上半年安排 PDF 中的专升本专业与此一致"
gs_verify = V(GS_H2, "2026 年下半年报考简章附件（图片表格目视转写，转写核对见 evidence/gansu/images-index.md）")
gs_off = [{
    "major": "080901", "track": None, "local_code": "080901", "status": "open", "hosts": [], "plans": [],
    "matched_by": None,
    "complete": {"courses": False, "credits": False, "textbook": False},
    "verify": V(GS_H2, "2026 年下半年开考课程（10 月 24~25 日）：13017 计算机网络与信息安全、00023 高等数学（工本）、13003 数据结构与算法、13180 操作系统、"
                "13005 软件工程、14349 网络应用开发与系统集成、15040/15043/15044 思政课、13000 英语（专升本）；"
                "2026 年上半年（4 月 11~12 日）开考：02324 离散数学、13011 人工智能与大数据、13013 高级语言程序设计、02325 计算机系统结构、13015 计算机系统原理等"
                "（来源 " + GS_H1 + " 附件）。开考安排表不含学分与主考学校，计划与主考院校待查"),
}]
patch_offerings("gansu", gs_off, {"080901"}, V(GS_H2, GS_NOTE_TOTAL))

p = CONTENT / "provinces" / "gansu.json"
d = provlib._load(p)
d["authority"]["verify"] = V(GS_H2, "甘肃省教育考试院官网「自学考试·通知公告」2026 年下半年报考简章页（甘教考自〔2026〕3号所属栏目，用户浏览器另存页面）；站点对程序请求 412，只能真浏览器")
d["calendar"] = [
    {"session": "2026-04", "exam": "2026-04-11~12", "note": "报名时间取自简章页，本轮未取得当期简章原页面快照，只核到考试日期", "verify": V(GS_H1_PDF, "2026 年上半年开考专业及课程考试时间安排 PDF（来源页 " + GS_H1 + "）")},
    {"session": "2026-10", "exam": "2026-10-24~25",
     "register": "社会型专业新考生注册 2026-09-03~06，每日 8:30-18:00；所有网报考生选课缴费 09-03~09，每日 8:30-18:00；逾期不补报",
     "verify": V(GS_H2, "2026 年下半年报考简章「报考时间」条款；考试日期取自附件表（星期六 10 月 24 日、星期日 10 月 25 日）")},
]
d["policy"] = {
    "entry": {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制，均可报名；报考本科层次专业的考生须在毕业前校验国民教育系列专科层次毕业证书；服刑人员经司法劳改管理部门审批后方可报考。"
                      "高职（高专）在校生或自学考试专科在读考生可同时报考本科层次相关专业，办理毕业手续时须交验学信网认证的专科毕业证书。同一考试时间段只能选一门课程，当次最多报四门。",
              "verify": V(GS_H2, "2026 年下半年报考简章「报考条件」「报考手续及相关要求」")},
    "graduate": {"text": "未毕业考生可用同一准考证号选报其他专业课程，达到该专业毕业条件后申请毕业；毕业时到报名地所在市（州）教育考试招生机构办理；本科考生须交验学信网认证的专科毕业证书。"
                         "论文（设计）答辩与考核费 180 元，由考生直接向主考学校缴纳。已停考专业不再办理毕业手续，在籍考生可转入现行开考的同层次相近专业，已通过课程按相同、相近和「一顶一」顶替（公共政治课、英语除外）。"
                         "各专业毕业所需门数与学分见专业考试计划，本轮未取得甘肃现行专业计划。",
                 "verify": V(GS_H2, "2026 年下半年报考简章「报考手续及相关要求」第 5、9 条、「实践性环节考核」、「收费」")},
    "degree": None,
    "exemption": {"text": "依据《甘肃省高等教育自学考试课程免考实施细则》（甘考委发〔2026〕2号），申请免考课程者在取得自学考试考籍后，通过甘肃省教育考试院首页登录甘肃省国家教育考试综合管理平台考生端网上申请办理；免考、转档手续费每人每次按一科次 40 元。"
                           "不参加英语（专升本）考试的考生，可在非本专业的其他专升本专业计划中任选 2 门专业课，成绩合格可顶替英语（专升本）。细则全文本轮未取得。",
                  "verify": V(GS_H2, "2026 年下半年报考简章「注意事项」（一）、「报考手续及相关要求」第 8 条、「收费」")},
}
d["events"] = [e for e in d["events"] if (e.get("date"), e.get("kind")) not in {("2026-04", "stop"), ("2026-01", "policy")}] + [
    {"date": "2026-04", "kind": "stop", "text": "自 2026 年上半年起停考教育管理（独立本科段）、心理健康教育（独立本科段）和汉语言文学（专科）专业，原专业合格课程不作废，未毕业考生可转入现行开考的其他专业；同期开考中文（专科，570209），主考学校兰州大学。",
     "verify": V(GS_H2, "2026 年下半年报考简章「报考手续及相关要求」第 11、12 条（依据考委〔2022〕1号）")},
    {"date": "2026-01", "kind": "policy", "text": "全省高等教育自学考试省际转考自 2026 年起全程线上办理：转出申请上半年 2 月 10~20 日、下半年 8 月 10~20 日；转入信息确认上半年 3 月 20~25 日、下半年 9 月 20~25 日。",
     "verify": V(GS_H2, "2026 年下半年报考简章「电子转考」")},
]
provlib._save(p, d)

# ================= 河南 =================
HN_PAGE = "https://zkwb.haeea.cn/ZKService/PageNormal/ShowContent.aspx?ID=10322"
HN_PDF = "https://zkwb.haeea.cn/PUBLISH/%E6%B2%B3%E5%8D%97%E7%9C%81%E9%AB%98%E7%AD%89%E6%95%99%E8%82%B2%E8%87%AA%E5%AD%A6%E8%80%83%E8%AF%95%E4%B8%93%E4%B8%9A%E4%B8%80%E8%A7%88%E8%A1%A82026.pdf"
HN_FILE = DL / "河南省高等教育自学考试专业一览表2026.pdf"
keep("henan", HN_FILE, HN_PDF, f"河南省高等教育自学考试专业一览表（2026）PDF，88 行；来源页 {HN_PAGE}", text_of=True)
HN_NOTE = f"河南省高等教育自学考试专业一览表（2026，附件 PDF {HN_PDF}，共 88 行，含新专业代码、原专业代码、主考学校）；考生服务平台对程序请求 412，用户浏览器下载"


def hn_off(major, local, hosts, name, merged=False):
    return {"major": major, "track": None, "local_code": local, "status": "stopped" if merged else "open", "hosts": hosts,
            "matched_by": f"一览表新专业代码 {major} 对应原专业代码 {local}（{name}）",
            "complete": {"courses": False, "credits": False, "textbook": False},
            "verify": V(HN_PAGE, HN_NOTE + ("；备注：被合并专业不接受新生报考" if merged else ""))}


hn_new = [
    hn_off("080701", "110110", ["信阳师范大学"], "电子信息工程"),
    hn_off("080702", "080705", ["郑州大学"], "电子科学与技术"),
    hn_off("080901", "080702", ["河南科技大学"], "计算机科学与技术"),
    hn_off("080901", "082208", ["河南科技大学"], "计算机科学与技术", merged=True),
    hn_off("080902", "080711", ["河南科技大学"], "软件工程"),
    hn_off("080902", "080720", ["河南科技大学"], "软件工程", merged=True),
]
patch_offerings("henan", hn_new, {"080701", "080702", "080901", "080902"}, V(HN_PAGE, HN_NOTE + "；全表未列此专业（0807、0809、0808 类仅上列 4 个新专业代码）"))
p = CONTENT / "provinces" / "henan.json"
d = provlib._load(p)
d["events"] = [e for e in d["events"] if e.get("date") != "2027-07-01"] + [
    {"date": "2027-07-01", "kind": "code-change", "text": "一览表注：2027 年 7 月 1 日前报名、考试时仍使用原专业代码；本表新专业代码自此日起使用。", "verify": V(HN_PAGE, HN_NOTE)},
]
provlib._save(p, d)

# ================= 陕西 =================
SX_PDF = "https://www.sneac.com/2025/2026zkkcap2.pdf"
SX_NOTICE = "https://www.sneea.cn/info/1032/16811.htm"
SX_DOCX = "https://www.sneea.cn/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=1925838831&wbfileid=76079"
SX_PDF_FILE = DL / "2026zkkcap2.pdf"
SX_DOCX_FILE = DL / "陕西省自学考试省考课程目录.docx"
keep("shaanxi", SX_PDF_FILE, SX_PDF, "2026 年陕西省高等教育自学考试课程安排 PDF（36 个专业：专科 10、专升本 26），pymupdf 抽取", text_of=True)
keep("shaanxi", SX_DOCX_FILE, SX_DOCX, "陕西省自学考试省考课程目录（附件，省考课程代码与名称），docx 抽取", text_of=True)
SX_NOTE = "2026 年陕西省高等教育自学考试课程安排（陕教考〔2026〕通知附件，36 个专业：专科 10、专升本 26；通知页 " + SX_NOTICE + "）"
sx_new = [
    {"major": "080901", "track": None, "status": "open", "hosts": [], "plans": [],
     "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(SX_PDF, SX_NOTE + "；计算机科学与技术（080901）两个考期开考课程（* 为省考课程）：02324 离散数学、13003 数据结构与算法、00023 高等数学（工本）、13013 高级语言程序设计、13180 操作系统、13015 计算机系统原理、13005 软件工程、"
                "04747 Java 语言程序设计（一）*、02198 线性代数*、04735 数据库系统原理*、13007 编译原理*、14263 数字逻辑设计*、07844 人工智能导论*，加思政课 15040/15043/15044 与 13000 英语（专升本）；"
                "课程安排不含学分与主考学校，计划与主考院校待查")},
    {"major": "080903", "track": None, "status": "open", "hosts": [], "plans": [],
     "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(SX_PDF, SX_NOTE + "；网络工程（080903）两个考期开考课程（* 为省考课程）：02318 计算机组成原理、02324 离散数学、13003 数据结构与算法、00023 高等数学（工本）、04737 C++程序设计、04741 计算机网络原理、"
                "04735 数据库系统原理*、04751 计算机网络安全*、14341 网络工程原理与实践*、02379 计算机网络管理*、01350 网络应用程序开发*、14352 网页设计与网站建设*，加思政课 15040/15043/15044 与 13000 英语（专升本）；"
                "课程安排不含学分与主考学校，计划与主考院校待查")},
]
patch_offerings("shaanxi", sx_new, {"080901", "080903"}, V(SX_PDF, SX_NOTE + "全表未列此专业（范围内只有 080901 计算机科学与技术、080903 网络工程）"))
p = CONTENT / "provinces" / "shaanxi.json"
print("gansu henan shaanxi ok")
