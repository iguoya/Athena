"""2026-11-03 复查 Downloads 时补上的遗漏：
  - 天津：0919351964.pdf 是《2026年下半年天津市高等教育自学考试专业一览表》全表（12 所主考学校、约 60 行，附件原件，自考本科网托管，第三方级）。
    范围内只有 080901（天津工业大学、天津师范大学开考）、080902（天津理工大学开考）、080701（中国民航大学，停止新生报名）；据此写其余专业「不开设」。
  - 陕西：使用者 2026-11-03 截图（阳光自考网「西安电子科技大学自考计算机科学与技术（独立本科段）专业自考课程一览表」）给出 080901 主考院校西安电子科技大学；
    截图里的课程表是旧计划（03708/03709、英语（二）14 学分等），不入库。
  - 山西：2023 年官方报考简章（山西招生考试网站页打印 PDF，ABUIABA9GAAg5tiEugYo3ryhvgc.pdf）的开考专业、主考院校一览表：080901 太原理工大学（B080702 计算机及应用）。
  - 陕西 2025 年通知写明「2025 年起开始执行新的专业计划，见陕西省教育考试院门户网站 服务→自考服务→新专业计划」——这是陕西计划文件的位置，写进待核实清单。
用法：python -X utf8 build_followup_20261103.py <Downloads 目录> <抽取目录>
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403

DL, EX = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
EVI = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence"
TJ_PDF = "https://www.zikaoben.cn/uploads/file/260519/0919351964.pdf"
TJ_PAGE = "https://www.zikaoben.cn/article/e260519153572.html"
TJ_NOTE = f"《2026年下半年天津市高等教育自学考试专业一览表》（附件原件，自考本科网托管 {TJ_PDF}；第三方级，使用者裁决可信）"

p = CONTENT / "provinces" / "tianjin.json"
d = provlib._load(p)
listed = {"080901", "080902", "080701"}
for o in d["offerings"]:
    if o["major"] == "080901":
        o["status"], o["hosts"] = "open", ["天津工业大学", "天津师范大学"]
        o["verify"] = V(TJ_PAGE, TJ_NOTE + "：天津工业大学（开考）、天津师范大学（开考）；主考院校与招考资讯网非笔试课程主考院校表一致", level="report")
    elif o["major"] == "080902":
        o["status"], o["hosts"] = "open", ["天津理工大学"]
        o["verify"] = V(TJ_PAGE, TJ_NOTE + "：天津理工大学（开考）", level="report")
    elif o["major"] == "080701":
        o["status"], o["hosts"] = "stopped", ["中国民航大学"]
        o["verify"] = V(TJ_PAGE, TJ_NOTE + "：中国民航大学，备注「2025 年 4 月考试报名起不再接收新考生，2027 年起停止安排考试、停办毕业证」", level="report")
d["offerings"] = [o for o in d["offerings"] if o["status"] != "none"] + none_offerings(load_scope(), listed, V(TJ_PAGE, TJ_NOTE + "共 12 所主考学校，全表未列此专业", level="report"))
provlib._save(p, d)
dst = EVI / "tianjin"
shutil.copy2(DL / "0919351964.pdf", dst / "tj_yilanbiao_2026-10.pdf")
save_evidence("tianjin", "tj_yilanbiao_2026-10.pdf.txt", (EX / "0919351964.pdf.txt").read_text(encoding="utf-8"), TJ_PDF, "2026 年下半年天津市高等教育自学考试专业一览表（pymupdf 抽取）；来源页 " + TJ_PAGE, hashlib.sha256((DL / "0919351964.pdf").read_bytes()).hexdigest())

p = CONTENT / "provinces" / "shaanxi.json"
d = provlib._load(p)
for o in d["offerings"]:
    if o["major"] == "080901":
        o["hosts"] = ["西安电子科技大学"]
        o["verify"]["note"] = o["verify"]["note"].replace("主考院校待查（课程安排表不含主考学校；第三方陕西自考网称 080901 主考学校为西安电子科技大学，仅作线索未入库）", "主考院校西安电子科技大学取自第三方（阳光自考网页面截图，使用者 2026-11-03 提供，使用者裁决可信）；课程安排表本身不含主考学校")
        if "西安电子科技大学取自第三方" not in o["verify"]["note"]:
            o["verify"]["note"] += "；主考院校西安电子科技大学取自第三方（阳光自考网页面截图，使用者 2026-11-03 提供，使用者裁决可信）"
provlib._save(p, d)

p = CONTENT / "provinces" / "shanxi.json"
d = provlib._load(p)
for o in d["offerings"]:
    if o["major"] == "080901":
        o["verify"]["note"] += "；山西招生考试网站「山西省2023年高等教育自学考试报考简章」（来源山西省招生考试管理中心，2022-11-04 录入）的开考专业、主考院校一览表同样列太原理工大学 080901 计算机科学与技术（B080702 计算机及应用），该表范围内只有 080901，但为 2023 年版本，不能据此写 2026 年「不开设」"
provlib._save(p, d)
dst = EVI / "shanxi"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "ABUIABA9GAAg5tiEugYo3ryhvgc.pdf", dst / "sx_jianzhang_2023.pdf")
save_evidence("shanxi", "sx_jianzhang_2023.pdf.txt", (EX / "ABUIABA9GAAg5tiEugYo3ryhvgc.pdf.txt").read_text(encoding="utf-8"), "https://25398690.s21i.faiusr.com/61/ABUIABA9GAAg5tiEugYo3ryhvgc.pdf", "山西省 2023 年高等教育自学考试报考简章页打印 PDF（页面来源山西省招生考试管理中心；PDF 托管于第三方站点）", hashlib.sha256((DL / "ABUIABA9GAAg5tiEugYo3ryhvgc.pdf").read_bytes()).hexdigest())
print("followup ok")
