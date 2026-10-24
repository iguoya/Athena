"""海南：海南省考试局官网「自学考试报考须知」（2026-07-04）生成 provinces/hainan.json 的机构与政策部分。
海南「自学考试开考计划（面向社会考生）」页为动态内容，curl 取得空页，开考专业与计划本轮未取得，如实留待查。
用法：python -X utf8 build_hainan.py <下载目录>
"""
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
N = "https://ea.hainan.gov.cn/ywdt/zxks/202607/t20260704_4105042.html"  # 海南省高等教育自学考试报考须知（2026-07-04）
write_province("hainan", {
    "authority": {"name": "海南省考试局", "url": "https://ea.hainan.gov.cn/ywdt/zxks/index.html", "verify": V(N)},
    "selfstudy_portal": {"name": "海南省高等教育自学考试考生服务平台（自学考试信息系统）", "url": "https://ea.hainan.gov.cn/ywdt/zxks/index.html", "verify": V(N, "报考须知称通过考试局网站主页「自学考试信息系统」登录考生服务平台；平台独立网址须知未给出，此处暂填考试局自考栏目页")},
    "calendar": [],
    "policy": {
        "entry": {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制均可报名，有特殊要求的专业除外；申请本科毕业须提供专科（及以上）前置学历材料并经审核。", "verify": V(N, "报考须知一、七（三）")},
        "graduate": {"text": "完成专业计划所有课程考试合格、总学分达到毕业学分要求、思想品德经鉴定符合要求后可提出毕业申请，由省自考办审核，主考学校副署；申请毕业时间为上半年 6 月、下半年 12 月；毕业论文（设计）须在全部课程考试合格后方可报考，实践环节与毕业论文的报考和考核时间由主考学校安排。", "verify": V(N, "报考须知二、七")},
        "degree": {"text": "本科毕业生符合学位条例等规定的，由有学位授予权的主考学校授予学位；报考前须向主考学校咨询学位授予条件。", "verify": V(N, "报考须知九")},
        "exemption": {"text": "国家承认学历的各类高等教育毕业生、肄业生、退学生可按《海南省高等教育自学考试课程免考实施细则（2024）》申请免考已学过并取得合格成绩的课程，考生本人在平台线上申请，统考报考时同时提交；已有合格成绩的课程不得申请免考。转入考生须在海南取得本科不少于 4 门合格成绩方可申请毕业。", "verify": V(N, "报考须知五、六")},
    },
    "offerings": [], "plans": [], "events": [],
})
sha = hashlib.sha256((DL / "hn0704.html").read_bytes()).hexdigest()
import re
x = (DL / "hn0704.txt").read_text(encoding="utf-8")
body = re.sub(r"\s+", " ", x[x.find("海南省高等教育自学考试报考须知 发布日期") if "海南省高等教育自学考试报考须知 发布日期" in x else 0:])
i = body.find("海南省高等教育自学考试(以下简称")
save_evidence("hainan", "hi_zkxz2026.txt", body[i:i + 12000] if i >= 0 else body[:12000], N, "海南省高等教育自学考试报考须知正文；HTML 去标签", sha)
print("hainan ok")
