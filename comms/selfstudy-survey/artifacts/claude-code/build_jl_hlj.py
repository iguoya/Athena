"""吉林、黑龙江（使用者 2026-11-03 浏览器保存的官方页面，来源网址取自下载文件的 Zone.Identifier）：
  吉林：吉林省教育考试院「专业课程查询」页（https://www.jleea.com.cn/front/channel/12028，保存的框架页 kechengchaxun.html）——专业下拉列表 31 个专业代码，
        范围内只有 080902 软件工程；该专业计划（主考吉林大学，15 门 73 学分）与学位授予说明全文在页面里。没有 080901，其余范围内专业写不开设。
  黑龙江：黑龙江省招生考试院 zxks.hljea.org.cn 的「新生可注册专业列表」（自考、二学历两张表，专业代码缺前导零）——范围内只有 80901（080901）。
        自考本科网的黑龙江 080901 计划页（第三方）文字缺失严重（课程名被截掉、旧新课程栏错位），课程表不采。
用法：python -X utf8 build_jl_hlj.py <Downloads 目录> <抽取目录>
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403
from planlib import attach, build_plan  # noqa: E402

DL, EX = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
EVI = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence"

# ---------------- 吉林 ----------------
JL = "https://www.jleea.com.cn/front/channel/12028"
jl_page = (EX / "jl_kecheng.txt").read_text(encoding="utf-8")
assert "[080902]软件工程（专升本）" in jl_page and "[080901]" not in jl_page and "主考学校：吉林大学" in jl_page and "总学分" in jl_page
PUB = [("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None), ("15043", "中国近现代史纲要", 3, "public", None, "", None),
       ("15044", "马克思主义基本原理", 3, "public", None, "", None), ("13000", "英语（专升本）", 7, "public", None, "", None)]


def R(code, name, cr, pair=None):
    return (code, name, cr, "practice" if pair else "required", pair, "", None)


rows = PUB + [R("00023", "高等数学（工本）", 10), R("02324", "离散数学", 4), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计（实践）", 2, "13013"),
              R("13003", "数据结构与算法", 4), R("13004", "数据结构与算法（实践）", 2, "13003"), R("13180", "操作系统", 4), R("13005", "软件工程", 3),
              R("13006", "软件工程（实践）", 2, "13005"), R("13009", "数据库原理与技术", 4), R("13010", "人机交互的软件工程方法", 4), R("13011", "人工智能与大数据", 6),
              R("13015", "计算机系统原理", 4), R("14126", "软件过程与管理", 4)]
assert sum(r[2] for r in rows) == 73
plan, courses = build_plan("jl-080902-2026", "080902", "专业考试计划（页面未标版本）", "未标注", 73, 73,
                           "页面「总学分 73」，15 门课程（含配套实践课）逐行相加 73，全部为必考；毕业论文 06999 不计学分。每门课程及格 60 分；毕业须取得全部课程合格成绩、实践环节考核合格、撰写毕业论文并答辩合格，由吉林省高等教育自学考试委员会颁发毕业证书，吉林大学副署。",
                           rows, ("06999", "毕业论文", "不计学分"),
                           V(JL, "吉林省教育考试院「专业课程查询」页：软件工程（专升本）080902 专业考试计划，主考学校吉林大学；使用者 2026-11-03 保存的网页"),
                           "毕业论文不计学分，论文与答辩由主考学校组织。", [])
courses.save()
p = CONTENT / "provinces" / "jilin.json"
d = provlib._load(p)
d["authority"] = {"name": "吉林省教育考试院", "url": "https://www.jleea.com.cn/", "verify": V(JL, "吉林省教育考试院网站「考试项目→自学考试→专业课程查询」页")}
d["plans"] = [plan]
d["offerings"] = [{"major": "080902", "track": None, "local_code": "080902", "status": "open", "hosts": ["吉林大学"], "plans": [plan["id"]],
                   "matched_by": None, "complete": {"courses": True, "credits": True, "textbook": False},
                   "verify": V(JL, "专业课程查询页：软件工程（专升本）080902，主考学校吉林大学；专业下拉列表共 31 个专业代码，其中范围内只有该专业")}] + none_offerings(
    load_scope(), {"080902"}, V(JL, "吉林省教育考试院「专业课程查询」页专业下拉列表（31 个专业代码，含专升本与专科）全表未列此专业；列表是否包含全部在籍专业未核，开考状态以考试院公告为准"))
d["policy"]["degree"] = {"text": "软件工程专业毕业生达到国家规定的学位授予条件的，依据《中华人民共和国高等教育法》《中华人民共和国学位条例》，由主考学校吉林大学授予学士学位。", "verify": V(JL, "专业课程查询页软件工程（专升本）080902 专业考试计划末段说明")}
d["policy"]["graduate"] = {"text": "取得本专业考试计划规定的全部课程且合格、累计 73 学分以上，实践环节考核合格，撰写毕业论文并答辩合格，思想品德鉴定符合要求，经审核合格后由吉林省高等教育自学考试委员会颁发毕业证书，主考学校吉林大学副署，国家承认学历。", "verify": V(JL, "专业课程查询页软件工程（专升本）080902 专业考试计划末段说明")}
provlib._save(p, d)
dst = EVI / "jilin"
dst.mkdir(parents=True, exist_ok=True)
save_evidence("jilin", "jl_kechengchaxun.txt", jl_page, JL, "吉林省教育考试院专业课程查询页（浏览器保存的框架页 kechengchaxun.html，HTML 去标签）", hashlib.sha256((DL / "吉林省教育考试院_files" / "kechengchaxun.html").read_bytes()).hexdigest())

# ---------------- 黑龙江 ----------------
HL = "https://zxks.hljea.org.cn/lzk/UploadFile/xskzczy251.htm"
hl_page = (EX / "hlj_sheet001.txt").read_text(encoding="utf-8")
assert "80901" in hl_page and "二学历" in hl_page and "哈尔滨工程大学" in hl_page
NOTE = "黑龙江省招生考试院「新生可注册专业列表」（自考、二学历两张表，专业代码缺前导零；页面未标年份）"
p = CONTENT / "provinces" / "heilongjiang.json"
d = provlib._load(p)
d["authority"] = {"name": "黑龙江省招生考试院", "url": "https://zxks.hljea.org.cn/", "verify": V(HL, "自学考试主页站点 zxks.hljea.org.cn 发布的新生可注册专业列表")}
d["offerings"] = [{"major": "080901", "track": None, "local_code": "80901", "status": "open", "hosts": ["哈尔滨工程大学", "北京交通大学"], "mode": "自考",
                   "plans": [], "matched_by": "列表专业代码「80901 计算机科学与技术（专升本）」，缺前导零，按名称对应 080901",
                   "complete": {"courses": False, "credits": False, "textbook": False},
                   "verify": V(HL, NOTE + "：自考表主考院校哈尔滨工程大学、北京交通大学；二学历表主考院校哈尔滨工程大学、佳木斯大学、哈尔滨商业大学、东北农业大学；课程计划待查（自考本科网页面文字缺失，未采）")}] + none_offerings(
    load_scope(), {"080901"}, V(HL, NOTE + "两张表均未列此专业；该列表只含新生可注册的专业，在籍考生仍可能在考的停招专业未核"))
provlib._save(p, d)
save_evidence("heilongjiang", "hlj_xinsheng_zhuanye.txt", hl_page, HL, "黑龙江省招生考试院新生可注册专业列表（自考与二学历两表，浏览器保存的 sheet001.html，HTML 去标签）", hashlib.sha256((DL / "xskzczy251_files" / "sheet001.html").read_bytes()).hexdigest())
print("jilin heilongjiang ok")
