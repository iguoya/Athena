# -*- coding: utf-8 -*-
"""T-103 返工：呈现统一（分组/outline/lead/筛薄/排序/核实猜测批注）。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "qt"
CONTENT = ROOT / "content"
ARCHIVE = CONTENT / "archive.json"
DROPPED = CONTENT / "archive-dropped.md"
CASES = CONTENT / "cases"

# id -> (group, guide_tail)  guide_line = f"[{group}] {guide_tail}"
META: dict[str, tuple[str, str]] = {
    "qt.arc.signalslot": ("入门与信号槽", "Designer 自动连接与 C++ 死代码并存的入门窗体。"),
    "qt.arc.signalandslot": ("入门与信号槽", "新式 connect 与注释掉的经典示例、泄漏式 receiver。"),
    "qt.arc.cmake": ("入门与信号槽", "CMake 构建 Qt 的模板工程，看构建脚本比看业务更有用。"),
    "qt.arc.qmenu": ("入门与信号槽", "菜单已在 .ui 画好，C++ 侧尚未接上槽。"),
    "qt.arc.texteditor": ("入门与信号槽", "文本编辑器壳完整，打开/保存等逻辑仍空着。"),
    "qt.arc.splitter": ("Widgets 布局与交互", "在 main 里嵌套 QSplitter 的分割窗演示。"),
    "qt.arc.stackwidget": ("Widgets 布局与交互", "QStackedWidget 与自定义 signal 返回主页。"),
    "qt.arc.embedwidget": ("Widgets 布局与交互", "QHBoxLayout 嵌入子窗体但未接线的骨架。"),
    "qt.arc.dropfile": ("Widgets 布局与交互", "鼠标跟踪与拖放读文件的组合窗体。"),
    "qt.arc.qsystemtray": ("Widgets 布局与交互", "QSystemTrayIcon 与旧式 SIGNAL/SLOT 宏连接。"),
    "qt.arc.login": ("多窗口与对话框", "硬编码账号密码的模态 LoginDialog。"),
    "qt.arc.muitiwindow": ("多窗口与对话框", "模态登录与主窗动态 new QDialog 的子窗。"),
    "qt.arc.twowindow": ("多窗口与对话框", "登录对话框文件齐全但未接入 main 的断链示例。"),
    "qt.arc.qprocesslist": ("Model/View 与数据", "名义上的进程列表，实际是无 GUI 的 QProcess 调用。"),
    "qt.arc.studentinfo": ("Model/View 与数据", "学生信息表目录与 QML 内容严重错位。"),
    "qt.arc.networkinformation": ("网络与进程", "网络信息查询界面在，查询逻辑被注释掉。"),
    "qt.arc.imageprocessor": ("网络与进程", "网络图片处理只剩控件布局骨架。"),
    "qt.arc.qprocess": ("网络与进程", "QProcess 混用 detached 与 start，平台命令也写错。"),
    "qt.arc.xnode": ("网络与进程", "多工程 UDP 与 Qt 控制台耦合：所有权、阻塞与硬编码路径。"),
    "qt.arc.qtchartsbasic": ("Qt Charts", "基础课未链接 charts 模块，实现也还是空的。"),
    "qt.arc.chart": ("Qt Charts", "官方表格驱动饼图示例，含 Qt6 字符串 API 迁移点。"),
    "qt.arc.layout": ("QML 与 Qt Quick", "绝对坐标叠放矩形的最小 QML 示例。"),
    "qt.arc.layoutanchors": ("QML 与 Qt Quick", "Anchors 链式定位与注释对照。"),
    "qt.arc.layoutgrid": ("QML 与 Qt Quick", "Grid 多单元格重复声明的静态网格。"),
    "qt.arc.layoutstack": ("QML 与 Qt Quick", "StackLayout 与全屏 MouseArea 切页。"),
    "qt.arc.qmlpositioning": ("QML 与 Qt Quick", "Column/Row/Grid/Flow 定位跟练。"),
    "qt.arc.canvas": ("QML 与 Qt Quick", "Canvas 2D 静态 onPaint 示例。"),
    "qt.arc.multifile": ("QML 与 Qt Quick", "多 QML 文件组件化与 Button 内嵌 MouseArea。"),
    "qt.arc.designer": ("QML 与 Qt Quick", "条目写 Designer，实际是 QML 绝对布局。"),
    "qt.arc.qmlsyntax": ("QML 与 Qt Quick", "QML Book 语法片段合辑。"),
    "qt.arc.multipage": ("QML 与 Qt Quick", "SwipeView/TabBar 多页与断裂的 Circle 调用。"),
    "qt.arc.quickpi": ("QML 与 Qt Quick", "π 计算页：表单控件在，计算逻辑缺失。"),
    "qt.arc.gridquick": ("QML 与 Qt Quick", "清单写 Grid，主 QML 却是 StackView 壳。"),
    "qt.arc.quickstack": ("QML 与 Qt Quick", "StackView + Drawer 页面栈导航。"),
    "qt.arc.backend": ("QML 与 Qt Quick", "QML/C++ Backend 属性绑定最小例。"),
    "qt.arc.calculatorarea": ("QML 与 Qt Quick", "面积计算器：StackView 壳加 Circle 后端。"),
    "qt.arc.pyqtsignal": ("PyQt", "加载 .ui 却未 connect，且 PySide2/PyQt5 混用。"),
    "qt.arc.dpshell": ("综合小项目", "设计模式 Qt 壳：按钮驱动演示并切换 UML 图。"),
    "qt.arc.qtapp": ("综合小项目", "多主题子页宿主：切换、资源与模型问题。"),
}

ORDER = list(META.keys())

DROP = {
    "qt.arc.datetime": (
        "Qt5/17-DateTime",
        "drop-trivial：仅 Item + console.log 打印 Date/数组，无窗口无控件，批注只能凑根类型与 API 缺失",
    ),
    "qt.arc.qmllayout": (
        "Qt5/QML/1-Layout",
        "drop-trivial：名为 QML Layout，实为空白 Widgets MainWindow，无可教的布局代码",
    ),
    "qt.arc.pyqtdialog": (
        "Linux/PyQt/A6-Dialog",
        "drop-trivial：对话框案例只剩空 QMainWindow.show()，无 QDialog/无逻辑",
    ),
    "qt.arc.qmlsignal": (
        "Qt5/8-QMLSignal",
        "drop-trivial：Engine 模板 + onClicked 改色，无跨对象信号/C++ 桥接，批注只能写名实不符",
    ),
    "qt.arc.materialstyle": (
        "Qt5/57-MaterialStyle",
        "drop-trivial：conf 未设 Material Style，UI 与 Quick 多页模板同构，无独立主题内容",
    ),
    "qt.arc.quick": (
        "Qt5/37-Quick",
        "drop-trivial：与已收 qt.arc.quickstack（33-QuickStack）main.qml/main.cpp/qml.qrc 字节相同的重复变体",
    ),
}

# 每条：outline 六项 + lead（完整句子，写给没看过代码的人）
TEXT: dict[str, dict[str, str]] = {
    "qt.arc.signalslot": {
        "promise": "看清 Qt Designer 如何用图形化方式把按钮的 clicked() 接到窗口槽上，并对照 C++ 里写了却从未执行的代码。",
        "pain": "读者很容易以为 mainwindow.cpp 里的 say() 会在点击时运行，实际行为完全由 .ui 里的 <connections> 决定，调试时会对不上。",
        "model": "信号发送者在 .ui 里声明，接收者是 MainWindow 的内建槽 close()；C++ 侧没有再写 connect。",
        "scope": "单窗口、单按钮，没有业务逻辑，只覆盖 Designer 自动连接这一条路径。",
        "judgment": "适合用来读懂 Designer 生成的连接 XML；不要把它当成现代函数指针式 connect 的范例。",
        "landing": "若要改成调用 say()，需要把槽放进 slots，并在 Designer 或代码里重新 connect，同时去掉误导性的 close 连接。",
        "lead": "这是一份 Designer 入门窗体：界面上有一个按钮，点击后窗口会立刻关闭，而不是打印调试信息。对照 .ui 的 <connections> 与 C++ 里未使用的 say()，可以看出自动连线和手写连线各自管哪一段。",
    },
    "qt.arc.signalandslot": {
        "promise": "读懂函数指针式 connect 如何把按钮点击接到自定义 QObject 槽，并对照被注释掉的一整套师生信号示例。",
        "pain": "有效示例往往只剩一行 connect，课堂用的 Teacher/Student 类还在工程里却没接到 UI；receiver 用 new 出来却不设 parent，容易留下所有权坑。",
        "model": "QPushButton::clicked 连接到 Tiger::testHello；默认在同一线程直连，控制台应打印 hello world。",
        "scope": "一个按钮加上若干未接入界面的 QObject 类文件，不涉及布局或多窗口。",
        "judgment": "保留作「新式连接写法 + 注释掉的完整课」对照即可，不宜当成最终工程骨架。",
        "landing": "receiver 应做成成员指针或带 parent 的堆对象；要么恢复 Teacher/Student 演示，要么删掉多余类文件以免误导。",
        "lead": "点按钮时控制台应出现 hello world !!!。同时打开被注释的师生示例，对比函数指针 connect 与旧式写法，并留意 new Tiger() 作 receiver 时谁负责释放。",
    },
    "qt.arc.cmake": {
        "promise": "弄清一份最小 CMakeLists 如何找到 Qt、生成可执行文件，以及 Qt5/Qt6 分支在脚本里怎么写。",
        "pain": "业务窗口几乎是空的，本机若没配好 Qt CMake 包，configure 就会失败，容易误以为是代码写错。",
        "model": "find_package(Qt…) 之后用 qt_add_executable 或 add_executable，再 target_link_libraries 连 Widgets。",
        "scope": "CMakeLists 加空 MainWindow 模板，没有信号槽或业务演示。",
        "judgment": "归档价值主要在构建脚本与 AUTOUIC 等开关，而不是应用逻辑。",
        "landing": "在本机跑一遍 configure，对照批注里的 Qt6 分支与失败点，再决定要不要往空窗口里加内容。",
        "lead": "这是一份几乎没有业务的 Qt CMake 模板。阅读重点放在 CMake 版本、qt_add_executable 分支和 AUTOUIC，而不是 MainWindow 里有什么功能。",
    },
    "qt.arc.qmenu": {
        "promise": "看菜单栏与 QAction 如何在 .ui 里搭好，并找出 C++ 侧还缺哪些槽才能驱动编辑器行为。",
        "pain": "mainwindow.cpp 往往只剩 setupUi，新建/保存等动作点了没反应，读者会以为是控件坏了。",
        "model": "菜单与动作在 .ui，预期槽写在 MainWindow；QTextEdit 已就位，等待 QAction 触发。",
        "scope": "Widgets + .ui 的编辑器壳，不含真实文件读写实现。",
        "judgment": "很适合当作「列出待补 connect」的半成品练习，而不是成品编辑器。",
        "landing": "为 action_new、action_save 等补上槽，并操作 textEdit；需要时再加文档修改标志。",
        "lead": "运行后能看到菜单栏和中央的 QTextEdit，但菜单项大多还没接到逻辑。阅读时对照 .ui 里的 QAction 与空着的 mainwindow.cpp，想清楚还缺哪些槽。",
    },
    "qt.arc.texteditor": {
        "promise": "认出一个「界面像编辑器、逻辑还没写」的典型半成品，并列出打开/保存/查找至少缺哪几步。",
        "pain": "QAction 未连接、没有 QFileDialog 读写，界面完整会给人「已经能用」的错觉。",
        "model": "标准 MainWindow + QTextEdit + 菜单动作；完整版还应管文档脏标记与路径。",
        "scope": "向导生成的编辑器壳，不含真正的文件 IO 与查找实现。",
        "judgment": "典型的「先画 UI 后补逻辑」阶段快照，批注重点在缺口而不是控件选型。",
        "landing": "实现 new/open/save，并在关闭前根据 document()->isModified() 提示保存。",
        "lead": "窗口看起来像简易文本编辑器，但打开、保存、查找等动作都还没接上。把它当成待补全的壳来读：哪些 QAction 空着、缺哪段文件 IO。",
    },
    "qt.arc.splitter": {
        "promise": "亲手拖分割条，理解嵌套 QSplitter 与 setStretchFactor 如何分配空间。",
        "pain": "全部 UI 写在 main 里，既难维护也不便用 Designer；字体名绑中文 Windows，换环境会 silent fallback。",
        "model": "顶层水平 splitter：左侧文本，右侧再嵌垂直 splitter 上下两块文本。",
        "scope": "单窗口演示，没有菜单、状态栏或文档逻辑。",
        "judgment": "适合弄清 splitter API；结构本身应迁回 Widget 类或 .ui。",
        "landing": "用应用默认字体或样式表，并把构建 UI 的代码移出 main。",
        "lead": "运行后拖动分割条，观察水平与垂直嵌套如何联动。若本机没有代码里写死的中文字体，留意文本是否落到系统 fallback 字体。",
    },
    "qt.arc.stackwidget": {
        "promise": "走通 Widgets 多页切换：主页进子页、子页用自定义 signal 回到 index 0。",
        "pain": "子页在代码里 new 出来再塞进 stacked，索引顺序依赖添加顺序，和 Designer 预置页不是同一套路。",
        "model": "主页按钮改 currentIndex；子页发出自定义 signal，主窗槽把它切回 0。",
        "scope": "两页加一个自定义返回信号，覆盖自动连接与手写 connect 的混用。",
        "judgment": "比纯 Designer 连接多一步 C++，适合练 stacked 导航，但硬编码 index 要当心。",
        "landing": "子页可改为 Designer 预加载或工厂注册，避免写死 index 1。",
        "lead": "从主界面按钮进入子页，子页上的「返回」应回到首页。对照手写 connect 与 on_pushButton_clicked 自动连接，看两种接线如何并存。",
    },
    "qt.arc.embedwidget": {
        "promise": "弄清如何把自定义 QWidget 塞进主窗已有 layout，并看出演示调用缺了哪一行。",
        "pain": "嵌入 API 写了却没人调用，打开窗口只见空 layout，读者会以为布局坏了。",
        "model": "MainWindow::putwidget 把子窗 addWidget 到 ui 里的水平 layout。",
        "scope": "一个 layout 槽位加三个独立 form 类，默认都不挂上。",
        "judgment": "API 意图清楚，缺的是构造函数或示例槽里的那次演示调用。",
        "landing": "在构造或示例槽里 putwidget 三个 form，并把 ui 指针的访问控制收回 private。",
        "lead": "默认运行往往只看到空的水平布局。要看见嵌入效果，需要在代码里手动 putwidget(new Form…)；阅读重点是这条未接线的 API，而不是三个 form 各自长什么样。",
    },
    "qt.arc.dropfile": {
        "promise": "观察拖放路径是否进 lineEdit、文件内容是否进 textEdit，并定位 mime 校验与 open 遗漏。",
        "pain": "dragEnter 未校验 mime，任意拖入都可能进 dropEvent；文件未 open 时内容为空，看起来像「拖放无效」。",
        "model": "主窗开鼠标跟踪，子控件 acceptDrops 并重写 drag/drop 事件读 URL。",
        "scope": "状态栏 + lineEdit + textEdit 的组合窗体，不做完整文档编辑器。",
        "judgment": "适合讲事件重写；读文件那一段必须以批注里的修正为准，不能照抄。",
        "landing": "dragEnter 检查 hasUrls()；drop 里 QFile::open(ReadOnly) 并处理多个 URL。",
        "lead": "把文件拖到文本区，看路径有没有进 lineEdit、内容有没有进 textEdit。若内容为空，先核对是否真的 open 成功，再对照批注里的 mime 校验问题。",
    },
    "qt.arc.qsystemtray": {
        "promise": "跑通最小系统托盘：图标出现后单击恢复主窗，并对照宏连接与退出策略。",
        "pain": "旧式 SIGNAL/SLOT 宏在重构时不如函数指针安全；未设置 QuitOnLastWindowClosed 时，关主窗应用仍可能驻留托盘。",
        "model": "托盘 activated(Trigger) 后 setWindowState 并 activateWindow；托盘对象通常以主窗为 parent。",
        "scope": "单主窗 + 托盘图标，没有托盘菜单。",
        "judgment": "适合对照 Qt6 新式 connect 与 QSystemTrayIcon 文档，体量保持最小即可。",
        "landing": "改成函数指针 connect，并按产品需求设置 setQuitOnLastWindowClosed。",
        "lead": "运行后任务栏托盘应出现图标，单击宜把主窗唤回前台。关闭主窗时留意进程是否还在托盘里驻留，这和退出策略设置有关。",
    },
    "qt.arc.login": {
        "promise": "走一遍模态登录对话框的 accept/reject 路径，并看清硬编码比对有多脆弱。",
        "pain": "账号密码写死在源码，无哈希无后端；退出按钮若连 close 而非 reject，main 里很难区分「取消」与「成功」。",
        "model": "on_loginBtn_clicked 内联字符串比对，成功 accept，失败弹 warning。",
        "scope": "单对话框门闸加空主窗，不涉及会话或网络鉴权。",
        "judgment": "只适合讲对话框返回值语义，绝不能当安全登录参考。",
        "landing": "凭证外置或走后端；exitBtn 应 reject，让 exec() 返回值可区分取消。",
        "lead": "用正确和错误凭证各试一次，观察 exec 返回值与主窗是否出现。再点退出类按钮，看它是否等价于「取消登录」——语义不对时批注里有具体行号。",
    },
    "qt.arc.muitiwindow": {
        "promise": "理清「模态登录门闸 → 主窗 → 再开子对话框」这条多窗口流程。",
        "pain": "登录几乎没有凭证逻辑，比 arc_qt_login 更像流程壳；子对话框动态 new 后若不设删除策略，关窗后容易泄漏。",
        "model": "LoginDialog::exec 门闸通过后显示 MainWindow；主窗再非模态 show 一个空 QDialog。",
        "scope": "登录框 + 主窗 + 空子窗，子窗没有业务内容。",
        "judgment": "适合讲 exec/accept 与窗口父子关系，不要当完整应用骨架。",
        "landing": "子对话框设 WA_DeleteOnClose 或由智能指针管理；登录要么复用校验，要么标明「演示用直接 accept」。",
        "lead": "取消登录应直接退出进程；登录成功后进入主窗，点「新窗口」会再弹出一个空对话框。阅读时抓住模态与非模态、谁拥有谁这两条线。",
    },
    "qt.arc.twowindow": {
        "promise": "看清「登录对话框源文件齐全、入口却没串起来」时，运行表现会怎样误导人。",
        "pain": "main 未接入 LoginDlg，主按钮无逻辑，文件看起来完整、流程实际断裂。",
        "model": "预期是 LoginDlg 模态通过后再进主窗；现状停在空主窗。",
        "scope": "MainWindow 与 LoginDlg 源文件都在，断点在入口接线。",
        "judgment": "归档价值在半成品与 .ui 里标准按钮盒连接，运行预期要按批注降级理解。",
        "landing": "对齐 login/muitiwindow 的 main 流程，或删除未使用的登录类以免误导。",
        "lead": "当前运行多半只见空主窗、按钮无反应。对照 logindlg.ui 里 QDialogButtonBox 的 accept/reject 连接，可以判断「文件在、流程断」卡在哪一步。",
    },
    "qt.arc.qprocesslist": {
        "promise": "认清这份「进程列表」实际只是同步跑一条外部命令并打印，并不是 Model/View 表格。",
        "pain": "目录名像要做 QAbstractTableModel，源码却停在 QProcess + 字符串 split + qDebug，换到 Windows 命令也会直接失效。",
        "model": "用 QProcess 读 stdout，再拆行；完整练习还应把结果填进模型交给视图。",
        "scope": "控制台工程单文件，无 GUI、无模型类。",
        "judgment": "可保留为 QProcess 最小示例，标题应按「读 ps 输出」理解，别当表格课。",
        "landing": "若要表格 UI，另建 Widgets 工程并封装模型；命令与参数要按平台分支。",
        "lead": "运行后终端会刷出进程相关命令行输出，窗口里不会出现表格。阅读时抓住三点：Unix 命令硬编码、同步阻塞，以及名实不符的「进程列表模型」。",
    },
    "qt.arc.studentinfo": {
        "promise": "对照「学生信息表」这个名字，找出实际 QML 里缺了哪些 Model/View 零件。",
        "pain": "main.qml 往往是一排重复 Button，没有模型、角色与 delegate，目录名会把学习目标带偏。",
        "model": "正经做法应是 C++ QAbstractItemModel 或 ListModel 驱动 ListView/TableView。",
        "scope": "main.cpp 只加载 qrc 里的 QML，没有注册后端类型。",
        "judgment": "价值在提醒「目录名与 UI 必须一致」，否则连批注都无处落笔。",
        "landing": "要么补上真正的 Model/View，要么把归档标题改成「QML 按钮网格占位」。",
        "lead": "按条目名你会期待 ListView/TableView 和数据模型；打开后多半是 Designer 式按钮网格。把它当作「名实不符」的反面教材来读。",
    },
    "qt.arc.networkinformation": {
        "promise": "看本机主机名与网卡地址本该如何查询，并定位被注释掉的逻辑与魔法下标。",
        "pain": "界面控件在，getHostInformation 等槽却空着或注释掉，点按钮没有有效反馈。",
        "model": "QHostInfo::localHostName / addresses，再配合 QNetworkInterface 枚举。",
        "scope": "Widgets + .ui，查询结果应写回界面控件。",
        "judgment": "半成品归档：重点是把注释里的正确 API 接回去，并去掉写死的 addresses 下标。",
        "landing": "恢复查询槽，把结果填进线编辑框或列表，遍历地址时不要假定下标 0 永远存在。",
        "lead": "界面控件多半还在 .ui 里，但查询逻辑可能整段被注释。阅读时对照「曾写对的 API」与仍留在代码里的魔法下标，想清楚恢复时要改哪几处。",
    },
    "qt.arc.imageprocessor": {
        "promise": "看清「网络图片处理」目录下实际只剩布局骨架时，UI 与业务如何断链。",
        "pain": "ShowWidget 等类未真正挂上主窗，编译运行往往只见空窗，处理链完全缺失。",
        "model": "预期是下载/解码/显示一条链；现状停在控件声明与空类。",
        "scope": "若干 Widgets 源文件，没有完整的网络请求与图像管线。",
        "judgment": "批注应集中在空类、未接线与控件所有权，而不是假装功能已完成。",
        "landing": "要么补网络与显示链，要么在标题里标明「仅布局骨架」。",
        "lead": "编译后多半看到空主窗，或找不到真正被使用的 ShowWidget。阅读重点是 UI 与业务如何断开，以及控件所有权写法有没有把对象挂到 parent 树上。",
    },
    "qt.arc.qprocess": {
        "promise": "对比 start 与 startDetached 的差异，并指出平台命令、参数类型上的具体错误。",
        "pain": "shutdown/killall 一类命令绑死 Linux 语义，cheese 等参数类型也不对；在生产机上乱点有风险。",
        "model": "三个槽分别演示拉起外部程序；成员 QProcess 与 detached 启动的关系要分清。",
        "scope": "单 MainWindow 三个危险示例槽，不做通用启动器。",
        "judgment": "教学价值在「API 误用对照」，不是可交付的系统工具。",
        "landing": "改用 start 加错误处理，并按 Windows/Linux 分支命令；切勿在生产环境直接点这些按钮。",
        "lead": "这是危险的演示代码：按钮会去拉外部命令。阅读时分清 startDetached 与成员 process 是否真有关系，并核对 Linux 命令与参数表写错了哪些。",
    },
    "qt.arc.xnode": {
        "promise": "分看 UDP 节点服务端/客户端与 Qt 监控窗，理清阻塞 IO、线程与进程拉起各自卡在哪。",
        "pain": "server.run 死循环阻塞；GUI 写死本机绝对路径；Client 首次 recv 可能用到未初始化的源地址字段。",
        "model": "POSIX socket 阻塞收发，GUI 用 QProcess 拉起节点进程，配置与启动参数却未统一。",
        "scope": "Practice 多 CMake 目标加根目录 xnode 封装，跨平台不能开箱即用。",
        "judgment": "适合批注并发、路径与所有权，不宜直接当生产多节点框架。",
        "landing": "阻塞 recv 放工作线程；端口与路径读配置；进程用相对路径或 QStandardPaths，并用 start 接管标准输出。",
        "lead": "从 StandAloneNode 与 Application 两处对照：一边是阻塞式 UDP 循环，一边是写死路径的 QProcess 启动器。阅读时盯住线程模型、端口常量和「detached 之后 readyRead 会不会响」。",
    },
    "qt.arc.qtchartsbasic": {
        "promise": "弄清要用 Qt Charts 画基础图时，工程文件必须声明什么，以及空实现还缺哪些类。",
        "pain": "缺 QT += charts（或 CMake 组件）时，包含 QtCharts 头文件的翻译单元根本过不了编译；窗口类也可能仍是空壳。",
        "model": "QChart + QChartView + 系列（如 QLineSeries）挂到视图上。",
        "scope": "Widgets 模板加空头/源，尚未画出真实曲线。",
        "judgment": "把「缺模块」写进批注比偷偷补丁工程更有教益；代码保持原样。",
        "landing": "补上 charts 依赖并实现 createChart；Qt6 需确认是否单独安装 Charts 组件。",
        "lead": "按当前 .pro 去编译含 QtCharts 头文件的代码通常会失败。阅读重点是模块依赖与 Qt6 字符串/模块迁移清单，而不是期待窗口里已经有图。",
    },
    "qt.arc.chart": {
        "promise": "看官方示例如何用同一份表格模型驱动自定义饼图视图，并标出 Qt6 下会炸的字符串 API。",
        "pain": "Qt::SkipEmptyParts 一类枚举在 Qt6 位置变化会导致编译失败；部分视图细节（如 rubberBand）属于示例实现取舍。",
        "model": "QStandardItemModel 同时喂给 QTableView 与 PieView，选中联动高亮。",
        "scope": "mainwindow + 较大的 pieview 实现；是否链接 Qt Charts 要以工程为准。",
        "judgment": "官方示例质量高，归档批注应聚焦 API 迁移点与工程声明是否一致。",
        "landing": "按 Qt6 改 split 标志；确认本例是纯 QWidget 绘制还是依赖 Charts 模块。",
        "lead": "运行后应看到表格与饼图联动。阅读时对照 Qt6 字符串 split 枚举，以及 .pro 有没有声明 charts——有的示例其实只用 Widgets 自绘。",
    },
    "qt.arc.layout": {
        "promise": "用最少的 QML 画出两块色块，体会没有布局容器时靠 x/y 手工排布的限制。",
        "pain": "改窗口大小不会自动重排，重叠区域完全依赖手写坐标，换分辨率就错位。",
        "model": "顶层 Window 加子项绝对定位，没有 Row/Column/anchors 布局。",
        "scope": "纯 QML 视觉，无 C++ 业务。",
        "judgment": "适合引出 anchors 或布局容器；不宜当产品 UI 结构照搬。",
        "landing": "下一课应换成锚点或布局管理器，去掉魔法数字坐标。",
        "lead": "运行可见绿色与黄色色块部分重叠。拖拽改变窗口大小时注意它们不会自动让位——这就是绝对坐标布局的边界。",
    },
    "qt.arc.layoutanchors": {
        "promise": "读懂 anchors.top/left/bottom 等相对定位，并分清哪些注释行是实验残留。",
        "pain": "有效锚点与注释掉的实验行混在一起，初学者删错一行就会整页塌掉。",
        "model": "外层 Rectangle fill + margins，子项锚到 sibling 或父项。",
        "scope": "纯 QML，不引入 Controls。",
        "judgment": "把锚点冲突与工程名拼写写清楚即可，不必扩成完整应用。",
        "landing": "运行应见黄底、居中问候文字，以及绿/金方块的相对排列；对照注释理解每种 anchor 组合。",
        "lead": "打开 main.qml，顺着 anchors 相对关系与旁边的注释走一遍。重点理解相对 sibling 与相对父项、baseline 与 center 的差别。",
    },
    "qt.arc.layoutgrid": {
        "promise": "看 Grid 的列数与 spacing 如何自动换行，并意识到重复声明单元格的维护成本。",
        "pain": "二十多段几乎相同的 Rectangle 手写堆叠，改颜色或尺寸要改很多处。",
        "model": "Grid 加 anchors.centerIn 把整个网格居中。",
        "scope": "纯展示，没有交互与模型。",
        "judgment": "理解 Grid 够用；生产界面应 Repeater 或模型驱动。",
        "landing": "用数据模型加 Repeater 去掉重复 QML，并统一配色。",
        "lead": "运行看网格居中与列间距；试着改 columns 或 spacing，观察换行规则。同时留意源码里大量重复的 Rectangle 声明。",
    },
    "qt.arc.layoutstack": {
        "promise": "理解 StackLayout 一次只显示一页，以及 currentIndex 如何切换。",
        "pain": "全屏 MouseArea 会吃掉点击，以后在子页里再放按钮会很难命中。",
        "model": "布局管可见页，鼠标区域管切换逻辑。",
        "scope": "两页纯色块，没有文字或表单。",
        "judgment": "适合弄清 currentIndex；这种全屏点击切页不宜照搬到复杂界面。",
        "landing": "把切换放到可见控件或状态机上，并缩小 MouseArea 的命中范围。",
        "lead": "点击窗口应在 teal 与 plum 两页间切换。注意 MouseArea 盖在整页上时，和布局子项的层级谁先收到事件。",
    },
    "qt.arc.qmlpositioning": {
        "promise": "对照 Red/Green/BlueSquare 组件，看 Column/Row/Grid/Flow 各自如何排子项。",
        "pain": "手动 x/y 与 anchors 混用时，某一侧改尺寸另一侧不会跟着走；随机色也让截图对比变难。",
        "model": "多个 Item 分区，各自用一种定位容器排方块。",
        "scope": "QmlBook 定位章节跟练，附带若干彩色方块组件。",
        "judgment": "批注版本混用与布局一致性即可，它是跟练不是产品壳。",
        "landing": "多色方块应按四种容器分区排列；阅读时统一一种定位策略再改尺寸做实验。",
        "lead": "对照 Red/Green/BlueSquare 组件与 main.qml 各分区，看 Column、Row、Grid、Flow 排出来的节奏有何不同。",
    },
    "qt.arc.canvas": {
        "promise": "读 onPaint 里的 2D 路径 API，并判断缩放后是否需要 requestPaint。",
        "pain": "fill 与 centerIn 等锚点若冲突会布局怪异；只在 onPaint 画、尺寸变化不请求重绘时，缩放后画面可能停在旧尺寸。",
        "model": "Window 内单个 Canvas，绘制逻辑集中在 onPaint。",
        "scope": "静态图形演示，无动画循环。",
        "judgment": "把锚点误用与重绘时机写清即可。",
        "landing": "启动应见灰色区域与形状；改窗口大小后若图案不刷新，按批注补 requestPaint。",
        "lead": "关注 onPaint 里怎么建路径、怎么填充，以及 anchors 是否互相打架。缩放窗口后若图案不跟着变，说明缺了重绘触发。",
    },
    "qt.arc.multifile": {
        "promise": "看多 QML 文件如何通过组件名拼界面，并找出 Button 与 MouseArea 双重点击的问题。",
        "pain": "Button 里再嵌 MouseArea 时事件重复；某些 anchors 写法可疑，换控件尺寸会错位。",
        "model": "main.qml 根 Window 引用自定义 Hello 等组件，经 qrc 一起加载。",
        "scope": "两个（或少量）QML 文件加标准 engine 启动。",
        "judgment": "适合讲 qrc 多文件组织；交互写法需要按现代 Controls 习惯收一收。",
        "landing": "Button 用 onClicked；Hello 用合法 anchor 或包一层 Item 再定位。",
        "lead": "运行看中心按钮与底部 Hello 条；点任一可点区域应退出应用。阅读时分清多文件怎么拼起来，以及为什么不宜在 Button 里再嵌一层 MouseArea。",
    },
    "qt.arc.designer": {
        "promise": "核对条目名「Designer」与仓库内容是否一致，并指出绝对坐标 QML 的维护成本。",
        "pain": "没有 .ui，却挂着 Designer 标题；绝对 x/y 在换分辨率时立刻穿帮。",
        "model": "正经 Designer 路径应是 .ui + uic/QUiLoader；这里却是手写 QML。",
        "scope": "main.cpp 加载 main.qml，无 Widgets .ui。",
        "judgment": "若保留归档，应按 QML 布局练习来读，不要找 Designer 工作流。",
        "landing": "要么引入真正的 .ui，要么去掉绝对坐标改用 Layout/anchors，并改标题。",
        "lead": "窗口标题可能写着 Scroll 之类，和「Designer」条目名对不上。把它当 QML 绝对布局反例来读：哪些坐标写死、为什么难维护。",
    },
    "qt.arc.qmlsyntax": {
        "promise": "在一份合辑里过一遍 id、属性绑定、attached property 与 Keys 等语法点。",
        "pain": "大段注释打断树结构，属性顺序混乱时，引擎报错行号会对不上直觉。",
        "model": "单 Window 内多段教学片段共用一份 qrc 资源。",
        "scope": "语法演示，不追求完整应用导航。",
        "judgment": "批注结构合法性与 Qt5 DPI 开关即可。",
        "landing": "空格计数、ESC 清零、三角形图显示等行为应按片段注释逐项对照。",
        "lead": "逐段阅读 property、alias、Keys 与信号处理器，同时检查 QML 树层级是否合法。这是语法合辑，不是单一功能的小应用。",
    },
    "qt.arc.multipage": {
        "promise": "走通 SwipeView/TabBar 多页导航，并在 Page1 上复现那次断裂的 Circle 调用。",
        "pain": "导航双向绑定可用，但 Page1 点击处理器引用了不存在的 Circle，一点就脚本错误。",
        "model": "tabBar.currentIndex 与 swipeView.currentIndex 互相同步。",
        "scope": "两页 Form + footer TabBar，面积计算未完成。",
        "judgment": "导航结构可学，Page1 逻辑按未完成片段处理。",
        "landing": "补 C++/QML 单例暴露计算，或删掉错误的 handler。",
        "lead": "切换 Tab 应正常。到 Page1 点按钮若弹出脚本错误，那就是本条批注的核心：导航壳在，业务对象没接上。",
    },
    "qt.arc.quickpi": {
        "promise": "看 π 计算页的表单控件如何摆好，并指出按钮逻辑与 Qt6 不兼容 import。",
        "pain": "计算按钮没有 handler；Styles.Desktop 一类 import 在 Qt6 已移除，换环境直接加载失败。",
        "model": "SwipeView 与 TabBar 同步；Page1Form 里堆表单控件。",
        "scope": "UI 骨架为主，计算未实现。",
        "judgment": "半成品 + 可移植性清单，适合对照 Controls 版本差异。",
        "landing": "补上点击计算；把 Desktop Style import 换成 Qt6 仍支持的写法。",
        "lead": "可以切换 Tab，点「计算」往往没有效果。Page1Form 混用绝对坐标与部分 anchors，再加上可能不兼容的 Style import，是阅读时的两条主线。",
    },
    "qt.arc.gridquick": {
        "promise": "核对「Grid」清单意图与仓库主 QML 是否一致，并评估固定大屏尺寸在笔记本上的后果。",
        "pain": "主界面是 Stack 模板而不是 Grid；Page1 写死大分辨率时，小屏只能看到局部。",
        "model": "当前更像 StackView + 多个 Form，而不是 Grid 演示。",
        "scope": "Quick Controls 多页壳，缺真正的 Grid 教学内容。",
        "judgment": "优先写清 manifest/目录名与文件不一致，再谈布局细节。",
        "landing": "行为按 Stack 应用理解；若要教 Grid，应换主 QML 或改条目标题。",
        "lead": "别被目录名里的 Grid 带偏：打开 main 多半是 StackView 导航壳。再看 Page1Form 的固定尺寸，在笔记本上是否只能看到一角。",
    },
    "qt.arc.quickstack": {
        "promise": "用 StackView 管理页面深度与返回，并用 Drawer 选择要 push 的页。",
        "pain": "页面用字符串 URL push，没有类型检查，重构改名时容易推到不存在的文件。",
        "model": "initialItem 为 HomeForm，Drawer 再推 Page1/Page2；ToolBar 标题绑 currentItem.title。",
        "scope": "Controls 2.x + 三个 ui.qml 页的标准导航壳。",
        "judgment": "批注字符串路由与 title 依赖即可；与已删除的 37-Quick 重复变体对照见 origin.duplicates。",
        "landing": "菜单打开 Drawer，选页后栈加深，返回键或 ← 可 pop。",
        "lead": "关注 StackView 的 push/pop、Drawer 选页，以及 ToolBar 标题如何依赖 currentItem.title。这是多页 Quick 应用最常见的导航骨架。",
    },
    "qt.arc.backend": {
        "promise": "看 Q_PROPERTY + NOTIFY 如何把 C++ 属性暴露给 QML，并用 qmlRegisterType 注册类型。",
        "pain": "信号名大小写不规范、类名带多余空格时，QML 侧绑定会 silently 对不上或报警难读。",
        "model": "C++ 类型注册进 QML，输入框改属性，Label 显示同步。",
        "scope": "单 backend 类型加很短的 QML，无导航壳。",
        "judgment": "最小可用 backend 示范，批注命名与注册宏拼写即可。",
        "landing": "信号改为规范的 userNameChanged 形式，去掉类名多余空格后再看绑定是否干净。",
        "lead": "在输入框打字，Label 应跟着变。阅读重点是 Q_PROPERTY 命名、NOTIFY 信号，以及 qmlRegisterType 有没有把类型名注册对。",
    },
    "qt.arc.calculatorarea": {
        "promise": "从 Drawer 进入面积页，输入半径后触发 C++ Circle 计算，并评估精度与 QML 布局。",
        "pain": "圆周率写死 3.14；Page 大量绝对坐标，换窗体尺寸控件会漂。",
        "model": "C++ QObject 注册给 QML，StackView 负责多页导航。",
        "scope": "main.qml + Page1Form + circle 后端，覆盖导航与一次计算。",
        "judgment": "导航结构完整，计算层与页面布局都有明显改进点。",
        "landing": "改用 M_PI 或更高精度常量；Page 改 Layout/anchors。",
        "lead": "从 Drawer 进 Page1，输入半径再点按钮看面积。对照批注看 3.14 精度、绝对坐标布局，以及 setArea 一类信号是否按预期刷新界面。",
    },
    "qt.arc.pyqtsignal": {
        "promise": "对照 .ui 与 main.py，看信号槽教学停在哪一步，以及绑定库为什么不一致。",
        "pain": "加载了界面却没有 connect；工程注释或导入在 PySide2 与 PyQt5 之间摇摆，换环境即导入失败。",
        "model": "应用 QUiLoader 或 pyuic 生成的 Ui 类，再显式 connect 按钮。",
        "scope": "MainWindow.ui + 精简 main.py，槽逻辑未完成。",
        "judgment": "半成品：把依赖统一和补 connect 写进阅读目标即可。",
        "landing": "选定 PyQt5 或 PySide2 之一，加载 UI 后为按钮补上槽。",
        "lead": "打开后可能只见空窗或静止 UI，按钮没有业务反应。对照 .ui 与 main.py，分清「加载界面」和「接上信号槽」各自做到哪一步，并留意 PySide2/PyQt5 混用。",
    },
    "qt.arc.dpshell": {
        "promise": "用三个按钮分别跑 Strategy/Facade/TemplateMethod 演示，并切换对应的 UML 图资源。",
        "pain": "窗口类直接 new 模式上下文，UI 与模式代码紧耦合；部分路径上对象只 new 不 delete。",
        "model": "MainWindow 槽里驱动 Context::run，qrc 里的 svg 作 UML 背景。",
        "scope": "依赖 DesignPattern 下若干模式子目录源码，属于综合壳而非单一模式精讲。",
        "judgment": "批注耦合、所有权与 qrc 路径；模式本身的对错另见设计模式应用主线。",
        "landing": "点按钮应在 textEdit 看到字符串输出，frame 背景换成对应 UML。",
        "lead": "这是把三种设计模式演示塞进一个 Qt 主窗的壳。读 mainwindow 的按钮槽、resource.qrc 里的 UML svg，以及 StrategyContext::run 一类调用里的对象所有权。",
    },
    "qt.arc.qtapp": {
        "promise": "看多主题子页如何在主窗里 replaceWidget 切换，并核对资源与表格模型的生命周期。",
        "pain": "外部 qss/暗色主题资源可能缺失；部分菜单槽未实现；模型 new 出后未明确归属时会泄漏。",
        "model": "QMainWindow 持有 System/Thread 等子页成员，按动作替换中央控件。",
        "scope": "含大量 svg 的 qrc 宿主工程，子页完成度不一。",
        "judgment": "批注切换路径、缺失资源与模型所有权，不要期待每个菜单都可用。",
        "landing": "可切换的 system/thread 页应能显示；空的 process 菜单按批注视为未完成。",
        "lead": "关注 mainwindow 里如何 replaceWidget 切子页、system 表格模型谁拥有，以及 CMake/qrc 是否引用了本机不存在的 qss。能打开的页先走通，空菜单按半成品理解。",
    },
}


def main() -> None:
    data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    topics = data["chapters"][0]["topics"]
    by_id = {t["id"]: t for t in topics}

    missing_meta = [i for i in ORDER if i not in by_id]
    missing_text = [i for i in ORDER if i not in TEXT]
    if missing_meta or missing_text:
        raise SystemExit(f"missing meta={missing_meta} text={missing_text}")

    # drop cases + json topics
    dropped_ids = []
    for tid, (path, reason) in DROP.items():
        if tid not in by_id:
            print("skip already absent", tid)
            continue
        case = None
        for b in by_id[tid]["lesson"]["blocks"]:
            if b.get("type") == "archive":
                case = b.get("case")
                break
        if case:
            cdir = CASES / case
            if cdir.exists():
                shutil.rmtree(cdir)
                print("removed case", cdir.name)
        dropped_ids.append((tid, path, reason))
        del by_id[tid]

    # merge quick into quickstack duplicates
    qs = by_id["qt.arc.quickstack"]
    arc = next(b for b in qs["lesson"]["blocks"] if b["type"] == "archive")
    dups = list(arc.get("origin", {}).get("duplicates") or [])
    if "Qt5/37-Quick" not in dups:
        dups.append("Qt5/37-Quick")
        arc["origin"]["duplicates"] = dups

    # rewrite kept topics
    for tid, (group, tail) in META.items():
        t = by_id[tid]
        t["guide_line"] = f"[{group}] {tail}"
        tx = TEXT[tid]
        t["outline"] = {k: tx[k] for k in ("promise", "pain", "model", "scope", "judgment", "landing")}
        lead = next(b for b in t["lesson"]["blocks"] if b["type"] == "lead")
        lead["text"] = tx["lead"]

    # fix xnode readyRead note: verifiable from Qt docs — channels not connected
    xnode = by_id["qt.arc.xnode"]
    xarc = next(b for b in xnode["lesson"]["blocks"] if b["type"] == "archive")
    for n in xarc["notes"]:
        if "readyRead" in n.get("text", "") or (
            n.get("file") == "Application/mainwindow.h" and n.get("line") == 26
        ):
            n["file"] = "Application/mainwindow.cpp"
            n["line"] = 9
            n["end"] = 41
            n["kind"] = "ownership"
            n["text"] = (
                "成员 `QProcess process` 在构造函数里连接了 `readyRead`，"
                "但 `on_pushButton_3_clicked` 连续四次调用的是 `startDetached`："
                "按 Qt 文档，detached 进程不会接到该 `QProcess` 的通道上，"
                "因此 `readStatus`/`readyRead` 不会收到这些子进程的输出"
                "（应改用 `start` 并处理 `readyReadStandardOutput`）。"
            )

    # also soften/clarify other speculative notes that we can verify
    for n in xarc["notes"]:
        if n.get("file") == "client.cpp" and "可能来自" in n.get("text", ""):
            n["text"] = (
                "`recvfrom` 把对端地址写入 `server_address`，而 `connect()` 只初始化了 `m_address`；"
                "若在赋值前就依赖 `server_address` 回信，源地址字段仍是未定义内容"
                "（条件：第一次回复前没有其它路径写入该结构体）。"
            )

    # reorder
    new_topics = [by_id[i] for i in ORDER]
    assert len(new_topics) == len(ORDER)
    data["chapters"][0]["topics"] = new_topics

    ARCHIVE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("archive.json topics:", len(new_topics))

    # append dropped md
    lines = DROPPED.read_text(encoding="utf-8").splitlines()
    # avoid duplicate append
    existing = "\n".join(lines)
    additions = []
    for tid, path, reason in dropped_ids:
        marker = f"`{path}`"
        if marker in existing and "返工复筛" in existing and tid.split(".")[-1] in existing:
            continue
        additions.append(f"- `{path}` — {reason}（返工复筛，原条目 {tid}）")
    if additions:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("## 返工复筛（T-103 呈现统一）")
        lines.extend(additions)
        lines.append("")
        DROPPED.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("dropped.md +", len(additions))
    else:
        print("dropped.md unchanged or already recorded")


if __name__ == "__main__":
    main()
