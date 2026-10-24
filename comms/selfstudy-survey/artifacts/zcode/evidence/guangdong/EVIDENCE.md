# 广东证据清单（zcode，T-001 试点采集）

抓取日期均为 2026-10-24。sha256 为文件正文字节。
注意：本目录另有非本人创建的文件（szeb-bkcc-2~6.html、szeb-bkcc-index.json、szeb-post_8949090/8949095.html、szeb-11037846.html、gd-2023-5-fujian14.doc/.docx、gd-fujian14-text.txt），系 leader（claude-code）并行采集所留，未核对、未改动，不在本清单。

| 文件 | url | sha256 | note |
|---|---|---|---|
| 4833531-gd-2026-0410-kaikao-kecheng-jiaocai.pdf | https://eea.gd.gov.cn/attachment/0/602/602026/4833531.pdf | b56662f577e329d22450ebf852830aafbe0d2d162c223ce1e77ac65fa73bad6d | 粤考办〔2025〕20号：2026年4、10月开考课程考试时间安排（附件1/2）+使用教材表（附件3），47页文本 PDF，可全文抽取。pilot 两专业的课程行与教材主源 |
| post-4833531.html | https://eea.gd.gov.cn/zxks/content/post_4833531.html | a68a3a41f44f230e20303f0dc9d23ea5c935cea128a1891da6a8d460484b2127 | 上述文件发布页（2025-12-23，文号粤考办〔2025〕20号） |
| 080901计算机科学与技术（专升本）（原计算机及应用）.jpg | https://www.eeagd.edu.cn/selfec/DownGgfjServlet?ggxh=227&fjxh=00（zip 内条目） | 072002e6558a659e75a65f25f2fef986f9036f0c22f9ffde42d0a5fd196d65d | 新旧计划课程顶替表（图片，无文本层）。学分来源，AI 视觉抄录，凡引用处标 OCR |
| 080901计算机科学与技术（专升本）（原计算机信息管理）.jpg | 同上 | fe3101c377970f3f250dc3b80033aa54cf4e107178c0d8771303252b5538beae | 同上，第二张，交叉验证用 |
| yuekaowei-2024-5-saomiao.pdf | 同上 zip 内条目 3 | a9d45cc28aa8a031d1efca528e28419574e51a67908bf5b80feb499a8c494f4e | 粤考委〔2024〕5号通知正文（5页，扫描件无文本层，未抄录全文） |
| post-4641339-yuekaowei-2024-5.html | https://eea.gd.gov.cn/zxks/content/post_4641339.html | d8a738ceb5b2e2fd9d19c4b95275f84afa919a938ea18803ca33c000a494f253 | 「关于广东省高等教育自学考试专业考试计划调整的通知」发布页（2024-12-30） |
| szeb-post_10869461-yuekaowei-2023-5.html | https://szeb.sz.gov.cn/szzkw/zkgg/zkxx1/content/post_10869461.html | 40fe9886263088a5bd55e09a02e3c8f2cd5438edfca7527c47758fa2ff8fcc0a | 粤考委〔2023〕5号原文（深圳市招生考试办公室网站转载，.gov.cn）：2026 年起执行新计划、过渡期 2023-11-01~2025-12-31、同一专业代码设一个计划、原主考学校全部保留为主考 |
| 4938270-zhukao-tiaozheng.pdf | https://eea.gd.gov.cn/attachment/0/621/621482/4938270.pdf | 97071cd341e30d802494b91cbe4dab8aed7928ccb5782d70ba228cc30dab498d | 「关于调整我省高等教育自学考试部分专业主考学校的通知」（2026-08-05）附件：080701 增加主考电子科技大学中山学院、080901 增加广东工业大学等；附件2 退出主考列表 |
| post-4938270-zhukao-tiaozheng.html | https://eea.gd.gov.cn/zxks/content/post_4938270.html | c6d0dc655cbe8a9525b9ebefc70caf6f4d5879ec0a40b2d6a3fe66f186fa467e | 上述通知发布页 |
| szeb-bkcc-benke-index3.html / index4.html | https://szeb.sz.gov.cn/szzkw/zkcx/zxks/zkzy/bkcc/index_3.html、index_4.html | 137d1375d4296a3e… / f430c8fe68b306a5… | 深圳招考网「自考专业·本科层次」目录：080901 多主考×专业课程组（华南师范大学[深圳大学]、广东财经大学[嵌入式技术/计算机及应用/移动商务技术]、华南理工大学[广东外语外贸大学]）；080701 不在该目录 |
| gd-baokao-202610.pdf（未入证据目录） | https://eea.gd.gov.cn/attachment/0/621/621632/4938897.pdf | — | 2026年10月报考须知附件（18页扫描，仅考务规则，无专业清单；不入证据） |

## 未能获得的官方文件（写进缺口）

- 《广东省高等教育自学考试各专业考试计划简表（2026 年起使用）》与《各专业面向社会主考学校》表：在《2026 年专业调整相关文件及资料.zip》（52,754,598 字节，https://www.eeagd.edu.cn/selfec/DownGgfjServlet?ggxh=227&fjxh=00，公告 227 附件）尾部。该 zip 服务器传输不稳定，多轮下载（curl 续传 8 轮 + python 流式 6 轮）最多获得 27,133,256 字节且不支持 Range 续传（返回 200 无 Content-Range），尾部文件未能获得。**这是广东总学分、选考规则、080701 学分/实践/毕业环节的唯一官方源。**
