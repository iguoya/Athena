"""ADR 0187 新增的五个带电类专业（080601 电气工程及其自动化、080204 机械电子工程、080202 机械设计制造及其自动化、080207 车辆工程、080208 汽车服务工程）：
只补「正面记录」（开考/停考，带主考院校），每条来源是我实际读过的那份省级专业表/简章/总表，备注只写这份文件里这一行说了什么。
不写「未开设」：没有这五个专业的省份保持「待查」，不为它们逐省取证（使用者 2026-11-03 要求核对部分不要乱填）。
各省来源地址：取自该省已入库的「不开设」记录所引的总表网址（同一份文件），或本脚本里写明的文件。
用法：python -X utf8 build_electric_majors_20261103.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403


def src_of(pid):
    d = provlib._load(CONTENT / "provinces" / f"{pid}.json")
    return next(o["verify"]["source"] for o in d["offerings"] if o["status"] == "none")


def rec(major, status, hosts, source, note, local=None, level="official"):
    if status == "open" and not hosts:
        note += "；主考院校待查（该文件未给主考学校）"
    o = {"major": major, "track": None, "status": status, "hosts": hosts, "plans": [],
         "complete": {"courses": False, "credits": False, "textbook": False}, "verify": V(source, note, level=level)}
    if local:
        o["local_code"] = local
    return o


MAJ = {"080601": "电气工程及其自动化", "080204": "机械电子工程", "080202": "机械设计制造及其自动化", "080207": "车辆工程", "080208": "汽车服务工程"}
HAINAN = "https://ea.hainan.gov.cn/ywdt/zxks/202506/t20250626_3886359.html"
LN = "https://www.lnzsks.com/newsinfo/IMS_20260708_46185_mqz2C6QR9o.htm"
X_JZ10 = "https://www.hneeb.cn/hnxxg/761/762/2026072901.xlsx"
X_JZ04 = "https://www.hneeb.cn/hnxxg/761/762/20260114.xls"

DATA = {
    "henan": lambda: [
        rec("080202", "open", ["河南科技大学"], src_of("henan"), "一览表：新代码 080202，原代码 080302（另并入 080327、080741），河南科技大学", "080302"),
        rec("080204", "open", ["河南科技大学"], src_of("henan"), "一览表：新代码 080204，原代码 080307（另并入 080338、080339、994108），河南科技大学", "080307"),
        rec("080601", "open", ["华北水利水电大学"], src_of("henan"), "一览表：新代码 080601，原代码 080612（另并入 080605），华北水利水电大学", "080612"),
    ],
    "hunan": lambda: [
        rec("080202", "open", ["长沙理工大学", "南华大学"], X_JZ10, "2026 年 10 月报考简章附表 1：长沙理工大学、南华大学"),
        rec("080208", "open", ["长沙理工大学", "中南林业科技大学", "湖南涉外经济学院"], X_JZ10, "2026 年 10 月报考简章附表 1：长沙理工大学、中南林业科技大学、湖南涉外经济学院"),
        rec("080601", "open", ["长沙理工大学"], X_JZ10, "2026 年 10 月报考简章附表 1：长沙理工大学"),
        rec("080204", "stopped", ["湖南大学"], X_JZ04, "2026 年 4 月报考简章附表 1 列湖南大学（标●）；4 月简章称湖南大学所有主考专业已停止接受新生入籍，仅机械电子工程接受在籍考生的实践课程报考；10 月附表 1 已不列"),
    ],
    "hainan": lambda: [
        rec("080204", "open", ["长沙理工大学"], HAINAN, "《开考专业汇编（2025 年修订版）》第 34 页：助学，长沙理工大学"),
        rec("080207", "open", ["三亚学院"], HAINAN, "汇编第 35 页：助学，三亚学院；海南省考试局 2026-10-30 公告列车辆工程自 2027-01-01 起停止接受新生注册报名"),
        rec("080208", "open", ["长沙理工大学"], HAINAN, "汇编第 36 页：助学，长沙理工大学"),
        rec("080601", "open", ["长沙理工大学"], HAINAN, "汇编第 37 页：助学，长沙理工大学"),
    ],
    "liaoning": lambda: [
        rec("080202", "open", ["沈阳工业大学"], LN, "简章附表一、附表三：辽宁专业序号 524，实践环节与毕业论文主考学校沈阳工业大学", "524/080202"),
        rec("080601", "stopped", ["沈阳工程学院"], LN, "简章附表二、附表四：519，停止接纳新生报名；实践环节主考学校沈阳工程学院；简章三（一）2 称 2024 年上半年起停止接纳新考生、2027 年上半年起停止颁发毕业证书", "519/080601"),
        rec("080208", "stopped", ["辽宁工业大学"], LN, "简章附表二、附表四：830，停止接纳新生报名；实践环节主考学校辽宁工业大学；简章三（一）4 称 2025 年上半年起停止接纳新考生、2028 年上半年起停止颁发毕业证书", "830/080208"),
    ],
    "hebei": lambda: [
        rec("080204", "open", ["河北科技大学"], src_of("hebei"), "河北自考信息系统开考专业表：河北科技大学，面向社会开考，原专业机电一体化工程", "080204"),
        rec("080202", "open", ["石家庄铁道大学"], src_of("hebei"), "河北自考信息系统开考专业表：石家庄铁道大学，面向社会开考，原专业机械制造及自动化", "080202"),
    ],
    "tianjin": lambda: [
        rec("080601", "open", ["天津理工大学"], "https://www.zikaoben.cn/article/e260519153572.html", "2026 年下半年专业一览表（附件原件的第三方托管版）：天津理工大学，开考", level="report"),
        rec("080204", "stopped", ["天津理工大学"], "https://www.zikaoben.cn/article/e260519153572.html", "2026 年下半年专业一览表（附件原件的第三方托管版）：天津理工大学，备注「2025 年 4 月考试报名起不再接收新考生，2027 年起停止安排考试、停办毕业证」", level="report"),
        rec("080208", "open", ["长沙理工大学"], "https://www.zikaoben.cn/article/e260519153572.html", "2026 年下半年专业一览表（附件原件的第三方托管版）：长沙理工大学，开考", level="report"),
    ],
    "chongqing": lambda: [
        rec("080204", "open", ["重庆科技大学", "重庆理工大学", "重庆三峡科技大学", "重庆文理学院", "重庆交通大学"], "https://www.zikaoben.cn/cate/tid-128", "自考本科网「重庆自学考试专业及院校一览表」：面向社会，正常", level="report"),
        rec("080207", "open", ["重庆理工大学"], "https://www.zikaoben.cn/cate/tid-128", "自考本科网「重庆自学考试专业及院校一览表」：面向社会，正常", level="report"),
        rec("080601", "open", ["重庆科技大学", "重庆文理学院"], "https://www.zikaoben.cn/cate/tid-128", "自考本科网「重庆自学考试专业及院校一览表」：面向社会，正常", level="report"),
    ],
    "heilongjiang": lambda: [
        rec("080207", "open", ["北京交通大学"], "https://zxks.hljea.org.cn/lzk/UploadFile/xskzczy251.htm", "新生可注册专业列表（自考表）：80207 车辆工程，北京交通大学", "80207"),
        rec("080601", "open", ["北京交通大学"], "https://zxks.hljea.org.cn/lzk/UploadFile/xskzczy251.htm", "新生可注册专业列表（自考表）：80601 电气工程及其自动化，北京交通大学", "80601"),
    ],
    "jilin": lambda: [
        rec(m, "open", [], "https://www.jleea.com.cn/front/channel/12028", f"专业课程查询页专业下拉列表列有 [{m}]{MAJ[m]}（专升本）") for m in ("080204", "080207", "080601")
    ],
    "shaanxi": lambda: [
        rec(m, "open", [], "https://www.sneac.com/2025/2026zkkcap2.pdf", f"2026 年课程安排列有 {MAJ[m]}（{m}）") for m in ("080202", "080601")
    ],
    "guizhou": lambda: [
        rec("080208", "open", [], "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/202606/t20260601_90233549.html", "2026 年 10 月课程考试安排表与 4 月表均列有汽车服务工程（080208，专升本）")
    ],
    "zhejiang": lambda: [
        rec("080208", "open", ["宁波工程学院"], "https://www.zjzs.net/art/2024/1/4/art_41_3655.html", "专业对应表列汽车服务工程（080208）；专业考试计划第 15 个专业，主考学校宁波工程学院")
    ],
    "beijing": lambda: [
        rec("080208", "stopped", [], "https://www.bjeea.cn/html/selfstudy/xxfbt/2025/1125/87664.html", "2026 年考试安排通知「停考过渡期专业」：汽车服务工程（专升本）01B0003，2026 年上半年最后一次安排考试", "01B0003")
    ],
    "shanghai": lambda: [
        rec("080202", "stopped", ["上海大学"], "https://www.shmeea.edu.cn/page/04100/20260121/20022.html", "开考专业信息汇总表「停考过渡专业」：上海大学，专升本，毕业证停发时间 2026 年 12 月，最后理论考试 2026 年 4 月")
    ],
    "gansu": lambda: [
        rec("080202", "open", ["待查"][:0], "https://www.ganseea.cn/zixuekaoshi/1820.html", "2026 年下半年开考专业及课程考试时间安排（简章附件）列有机械设计制造及其自动化（080202，专升本）")
    ],
}
for pid, fn in DATA.items():
    p = CONTENT / "provinces" / f"{pid}.json"
    d = provlib._load(p)
    new = fn()
    keys = {(o["major"], o.get("local_code")) for o in new}
    d["offerings"] = [o for o in d["offerings"] if not (o["major"] in MAJ and o["status"] != "none" and (o["major"], o.get("local_code")) in keys)] + new
    # 若该省早先已为这些专业写过「不开设」，与新的正面记录冲突时以正面记录为准
    d["offerings"] = [o for o in d["offerings"] if not (o["status"] == "none" and o["major"] in {n["major"] for n in new})]
    provlib._save(p, d)
    print(pid, [(o["major"], o["status"]) for o in new])
