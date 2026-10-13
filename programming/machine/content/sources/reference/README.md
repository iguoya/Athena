# 本地参考资料

公开能查到、写课用得上的教材落到这里，便于离线对照。登记在
`../catalog.json`。下载脚本：`programming/machine/scripts/fetch-sources.py`。

许可一列只是出处记录，不决定存放位置（仓库 ADR 0159、本应用 ADR 0009）；「可否进 git」只看体积。

| 目录 | 材料 | 许可（记录） | 可否进 git |
|---|---|---|---|
| `github/beej-bgc/` | Beej 教程卷指针～malloc 各章源稿 | CC BY-NC-ND；书中 C 示例为公有领域 | 是 |
| `dive-into-systems/` | DIS 第 2 章，及汇编线的第 6、7、9、10 章 HTML（原样） | CC BY-NC-ND | 是，原样保存 |
| `c-faq/` | Steve Summit C FAQ 索引页 | 个人站点 | 是，脚本下载后提交 |
| `c23/` | WG14 公开稿 N3220（C23 对照） | ISO 正式文本另购，公开稿免费 | PDF 体积大，不提交 |
| `modern-c/` | Gustedt *Modern C* | 官网提供免费版 | PDF 需从 HAL 手动下，脚本失败则留 URL |
| `sysv-abi/` | System V x86-64 psABI（PDF） | CC BY 4.0 | PDF 体积大，不提交，脚本重新抓 |
| `ms-x64-abi/` | Microsoft x64 调用约定等 3 页（Markdown 源文件） | CC BY 4.0，示例 MIT | 是 |
| `aapcs64/` | Arm AAPCS64（rst 源文件） | CC BY-SA 4.0 | 是 |
| `gnu-as/` | GNU as 手册 8 页（i386 语法与子页、AArch64） | GFDL | 是 |
| `intel-sdm/` | Intel SDM 合订本（26.7 MB） | Intel 版权 | PDF 体积大，不提交，脚本重新抓 |

Arm 的 A64 ISA 文档（DDI 0602）和架构参考手册（DDI 0487）对脚本返回 403，只在 catalog 里登记网址（`arm-isa`）。
汇编线只抓这一组：`python3 scripts/fetch-sources.py asm`。

写教案和出题前先打开对应文件，核对该节实际讲什么。题目必须带
`source_refs`。题干用中文改写该节事实，是为了学习效果，不是授权限制；Beej 的 C 示例代码可直接用于实验。
