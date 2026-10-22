# Qt 领域清单摘要（T-101）

- 生成时间：2026-10-21T15:43:44
- 目标应用：`programming/qt`（新建，ADR 0176）
- JSON：`comms/legacy-archive/artifacts/cursor/manifest-qt.json`
- 覆盖校验：`verify-qt.txt`（scoped 全覆盖）
- 编译实测日志：`build-test-qt.txt`

## 统计

| 项 | 数量 |
|---|---:|
| 单元总计 | 208 |
| keep | 122 |
| drop-third-party | 49 |
| drop-junk | 37 |
| 含 duplicates 字段的规范版 | 152 |
| build_checked | 25（通过 18 / 失败 7） |

### keep 建议子分组（topic_hint）

| topic_hint | keep 数 |
|---|---:|
| `archive.qt.qml-quick` | 44 |
| `archive.qt.basics` | 22 |
| `archive.qt.layout` | 13 |
| `archive.qt.other` | 12 |
| `archive.qt.windows-dialogs` | 9 |
| `archive.qt.pyqt` | 8 |
| `archive.qt.network` | 5 |
| `archive.qt.charts` | 2 |
| `archive.qt.designer` | 2 |
| `archive.qt.model-view` | 2 |
| `archive.qt.signals-slots` | 2 |
| `archive.qt.misc-app` | 1 |

## 范围与去重结论

- `Qt5/` 与 `Linux/QT/` 下同名编号工程（如 `01-SignalSlot`、`20-SignalAndSlot`）内容哈希一致，规范版取 `Qt5/...`，`Linux/QT/...` 记入 `duplicates`。
- `Qt5/Sample/**` 与 `Linux/Sample/**` 同为 `chapNN…/sampN_M…` 树；对照文件内容一致，判定为教材随书样例整套拷贝（布局同王英《Qt5.9 C++开发指南》一类配套），**未见个人改动痕迹** → `drop-third-party`（47 个样例单元 + meta）。
- `Linux/QT/QtApp/qdarkstyle`（481 文件）→ `drop-third-party`（[QDarkStyleSheet](https://github.com/ColinDuquesnoy/QDarkStyleSheet)）；宿主小应用 `Linux/QT/QtApp/app` 单独 keep。
- `29-QtAwesome` → `drop-third-party`（QtAwesome/Font Awesome）。
- `.pro.user*`、构建产物 → `drop-junk`。
- `Practice/CGI/**` → `drop-junk`（与 Qt 无关，显式记入以满足零遗漏）。
- `Practice/QT/QmlBook/*`、`Practice/QT/Qt5开发及实例/*`：按子工程拆分；无版权头，形态像跟练笔记，暂 **keep**，见待裁决。
- `Practice/untitled`：CMake 最小窗口，keep（basics）。

## 编译实测（本机 Qt 6.8.1 MSVC）

规则：每主题抽 2–3 个样本；其余 `build_checked: false`。只在临时目录拷贝源码编译，**未改** `.cache/legacy-src`。

详见 `build-test-qt.txt`。摘要：

- [通过] `qt5-1-hello` ← `Qt5/1-Hello` — 实测通过
- [通过] `qt5-11-helloworld` ← `Qt5/11-HelloWorld` — 实测通过
- [失败] `qt5-11-testwidget` ← `Qt5/11-TestWidget` — 实测失败: NMAKE : fatal error U1073:
- [失败] `qt5-91-qtchartsbasic` ← `Qt5/91-QtChartsBasic` — 实测失败: C:\Users\tiger\AppData\Local\Temp\athena-qt-build-7aokql82\qt5-91-qtchartsbasic\91-QtChartsBasic\mainwindow.h(5): fatal error C1083: �޷��򿪰����ļ�: ��QtChar
- [失败] `qt5-examples-chart` ← `Qt5/Examples/chart` — 实测失败: .\mainwindow.cpp(137): error C2039: "SkipEmptyParts": ���� "QString" �ĳ�Ա
- [通过] `qt5-38-designer` ← `Qt5/38-Designer` — 实测通过
- [通过] `qt5-20-layout` ← `Qt5/20-Layout` — 实测通过
- [通过] `qt5-21-layoutbinding` ← `Qt5/21-LayoutBinding` — 实测通过
- [通过] `qt5-23-layoutcolumn` ← `Qt5/23-LayoutColumn` — 实测通过
- [通过] `qt5-54-studentinfo` ← `Qt5/54-StudentInfo` — 实测通过
- [通过] `qt5-95-qprocesslist` ← `Qt5/95-QProcessList` — 实测通过
- [通过] `qt5-51-imageprocessor` ← `Qt5/51-ImageProcessor` — 实测通过
- [通过] `qt5-81-networkinformation` ← `Qt5/81-NetWorkInformation` — 实测通过
- [通过] `qt5-82-networkinformation` ← `Qt5/82-NetworkInformation` — 实测通过
- [失败] `pyqt-a1-hello` ← `Linux/PyQt/A1-Hello` — 实测失败: PyQt5/PySide6 not importable on this machine
- [失败] `pyqt-a2-hello` ← `Linux/PyQt/A2-Hello` — 实测失败: PyQt5/PySide6 not importable on this machine
- [失败] `pyqt-a3-hello` ← `Linux/PyQt/A3-Hello` — 实测失败: PyQt5/PySide6 not importable on this machine
- [通过] `prac-qt-qmlbook-1-2meetqt5` ← `Practice/QT/QmlBook/1-2MeetQt5` — 实测通过
- [通过] `prac-qt-qmlbook-2-2helloworldqml` ← `Practice/QT/QmlBook/2-2HelloWorldQML` — 实测通过
- [失败] `prac-qt-qmlbook-2-3-1consoleapplication` ← `Practice/QT/QmlBook/2-3-1ConsoleApplication` — 实测失败: .\main.cpp(12): error C2065: ��endl��: δ�����ı�ʶ��
- [通过] `qt5-01-signalslot` ← `Qt5/01-SignalSlot` — 实测通过
- [通过] `qt5-20-signalandslot` ← `Qt5/20-SignalAndSlot` — 实测通过
- [通过] `qt5-13-embedwidget` ← `Qt5/13-EmbedWidget` — 实测通过
- [通过] `qt5-2-muitiwindow` ← `Qt5/2-MuitiWindow` — 实测通过
- [通过] `qt5-21-twowindow` ← `Qt5/21-TwoWindow` — 实测通过

## 待裁决（已发消息给 claude-code）

1. **Sample 教材样例**：是否整套坚持 `drop-third-party`，还是挑几章「跟练痕迹明显」的改 keep？
2. **Practice/QT/QmlBook**：跟练工程 keep 还是按书名视为第三方样例 drop？
3. **Practice/QT/Qt5开发及实例**：目录名即书名，是否一律 drop-third-party？
4. **Qt Charts / 旧 API**：`91-QtChartsBasic` 缺 QtCharts 模块组件；`Examples/chart` 触碰 Qt6 API 变更（`QString::SkipEmptyParts`）——归档时是否允许 `// [ARCHIVE]` 最小补丁？
5. **PyQt**：本机无 PyQt5/PySide，一律 `toolchain` + `build_checked` 记录「解释器侧缺库」是否够用？

## keep 单元一览（按 topic）

### `archive.qt.basics`

- `qt5-0-commandcompile` — 0-CommandCompile ← `Qt5/0-CommandCompile` files=3 first=2021-04-16（重复 1）
- `qt5-0-commandcompile2` — 0-CommandCompile2 ← `Qt5/0-CommandCompile2` files=2 first=2021-04-16（重复 1）
- `qt5-0-commandcompile3` — 0-CommandCompile3 ← `Qt5/0-CommandCompile3` files=4 first=2021-04-16（重复 1）
- `qt5-0-commandcompile3-pro` — 0-CommandCompile3.pro ← `Qt5/0-CommandCompile3.pro` files=1 first=2021-04-26（重复 1）
- `qt5-1-hello` ✓ — 1-Hello ← `Qt5/1-Hello` files=9 first=2021-03-25（重复 1）
- `qt5-10-js` — 10-JS ← `Qt5/10-JS` files=5 first=2021-12-24（重复 1）
- `qt5-11-helloworld` ✓ — 11-HelloWorld ← `Qt5/11-HelloWorld` files=12 first=2021-12-24（重复 1）
- `qt5-11-testwidget` ✓ — 11-TestWidget ← `Qt5/11-TestWidget` files=1 first=2021-05-23（重复 1）
- `qt5-12-syntax` — 12-Syntax ← `Qt5/12-Syntax` files=4 first=2021-12-28（重复 1）
- `qt5-12-test-widget2` — 12-test_widget2 ← `Qt5/12-test_widget2` files=6 first=2021-05-23（重复 1）
- `qt5-16-js` — 16-JS ← `Qt5/16-JS` files=4 first=2022-01-08（重复 1）
- `qt5-17-datetime` — 17-DateTime ← `Qt5/17-DateTime` files=4 first=2022-01-18（重复 1）
- `qt5-28-textinput` — 28-TextInput ← `Qt5/28-TextInput` files=4 first=2022-03-06（重复 1）
- `qt5-3-qtwidgets` — 3-QtWidgets ← `Qt5/3-QtWidgets` files=5 first=2021-04-10（重复 1）
- `qt5-30-cmake` — 30-cmake ← `Qt5/30-cmake` files=6 first=2022-03-06（重复 1）
- `qt5-30-log` — 30-Log ← `Qt5/30-Log` files=3 first=2022-05-25（重复 1）
- `qt5-4-qmenu` — 4-QMenu ← `Qt5/4-QMenu` files=5 first=2021-03-25（重复 1）
- `qt5-4-qwidget` — 4-QWidget ← `Qt5/4-QWidget` files=5 first=2021-04-10（重复 1）
- `qt5-5-qwidget` — 5-QWidget ← `Qt5/5-QWidget` files=4 first=2021-04-10（重复 1）
- `qt5-5-texteditor` — 5-TextEditor ← `Qt5/5-TextEditor` files=5 first=2021-04-10（重复 1）
- `qt5-81-hello` — 81-Hello ← `Qt5/81-Hello` files=2 first=2021-04-27（重复 1）
- `qt5-91-debugrelease` — 91-DebugRelease ← `Qt5/91-DebugRelease` files=5 first=2021-04-10（重复 1）

### `archive.qt.charts`

- `qt5-91-qtchartsbasic` ✓ — 91-QtChartsBasic ← `Qt5/91-QtChartsBasic` files=5 first=2021-03-24（重复 1）
- `qt5-examples-chart` ✓ — chart ← `Qt5/Examples/chart` files=8 first=2021-04-29

### `archive.qt.designer`

- `qt5-38-designer` ✓ — 38-Designer ← `Qt5/38-Designer` files=5 first=2022-05-25（重复 1）
- `qt5-49-umldesigner` — 49-UMLDesigner ← `Qt5/49-UMLDesigner` files=3 first=2022-06-13（重复 1）

### `archive.qt.layout`

- `qt5-20-layout` ✓ — 20-Layout ← `Qt5/20-Layout` files=4 first=2022-01-18（重复 1）
- `qt5-21-layoutbinding` ✓ — 21-LayoutBinding ← `Qt5/21-LayoutBinding` files=4 first=2022-01-18（重复 1）
- `qt5-23-layoutcolumn` ✓ — 23-LayoutColumn ← `Qt5/23-LayoutColumn` files=4 first=2022-01-18（重复 1）
- `qt5-24-layoutgrid` — 24-LayoutGrid ← `Qt5/24-LayoutGrid` files=4 first=2022-01-18（重复 1）
- `qt5-25-layoutflow` — 25-LayoutFlow ← `Qt5/25-LayoutFlow` files=4 first=2022-01-18（重复 1）
- `qt5-26-layoutcolumn` — 26-LayoutColumn ← `Qt5/26-LayoutColumn` files=4 first=2022-03-06（重复 1）
- `qt5-27-layoutstack` — 27-LayoutStack ← `Qt5/27-LayoutStack` files=4 first=2022-03-06（重复 1）
- `qt5-31-splitter` — 31-Splitter ← `Qt5/31-Splitter` files=4 first=2021-04-10（重复 1）
- `qt5-43-checkbox` — 43-CheckBox ← `Qt5/43-CheckBox` files=4 first=2022-06-11（重复 1）
- `qt5-54-layout` — 54-Layout ← `Qt5/54-Layout` files=4 first=2022-06-13（重复 1）
- `qt5-55-layout` — 55-Layout ← `Qt5/55-Layout` files=4 first=2022-06-13（重复 1）
- `qt5-59-stackwidget` — 59-StackWidget ← `Qt5/59-StackWidget` files=4 first=2022-06-26（重复 1）
- `qt5-60-stackwidget` — 60-StackWidget ← `Qt5/60-StackWidget` files=8 first=2022-06-26（重复 1）

### `archive.qt.misc-app`

- `qt-qtapp-app` — app ← `Linux/QT/QtApp/app` files=39 first=2023-01-28

### `archive.qt.model-view`

- `qt5-54-studentinfo` ✓ — 54-StudentInfo ← `Qt5/54-StudentInfo` files=4 first=2022-06-13（重复 1）
- `qt5-95-qprocesslist` ✓ — 95-QProcessList ← `Qt5/95-QProcessList` files=2 first=2021-04-23（重复 1）

### `archive.qt.network`

- `qt5-51-imageprocessor` ✓ — 51-ImageProcessor ← `Qt5/51-ImageProcessor` files=6 first=2021-04-13（重复 1）
- `qt5-81-networkinformation` ✓ — 81-NetWorkInformation ← `Qt5/81-NetWorkInformation` files=5 first=2021-04-29（重复 1）
- `qt5-82-networkinformation` ✓ — 82-NetworkInformation ← `Qt5/82-NetworkInformation` files=4 first=2021-04-29（重复 1）
- `qt5-83-networkinterface` — 83-NetworkInterface ← `Qt5/83-NetworkInterface` files=5 first=2021-04-30（重复 1）
- `qt5-94-qprocess` — 94-QProcess ← `Qt5/94-QProcess` files=5 first=2021-04-15（重复 1）

### `archive.qt.other`

- `prac-untitled` — untitled ← `Practice/untitled` files=3 first=2023-05-09
- `qt5-02-normalui` — 02-NormalUI ← `Qt5/02-NormalUI` files=6 first=2021-12-08（重复 1）
- `qt5-48-backend` — 48-Backend ← `Qt5/48-Backend` files=6 first=2022-06-11（重复 1）
- `qt5-51-circle` — 51-circle ← `Qt5/51-circle` files=7 first=2021-04-10（重复 1）
- `qt5-52-qtdatetype` — 52-QtDateType ← `Qt5/52-QtDateType` files=2 first=2021-04-10（重复 1）
- `qt5-63-calculatorarea` — 63-CalculatorArea ← `Qt5/63-CalculatorArea` files=11 first=2022-06-26（重复 1）
- `qt5-64-circlearea` — 64-CircleArea ← `Qt5/64-CircleArea` files=11 first=2022-06-26（重复 1）
- `qt5-7-background` — 7-background ← `Qt5/7-background` files=5 first=2021-12-08（重复 1）
- `qt5-82-ui` — 82-UI ← `Qt5/82-UI` files=3 first=2021-04-27（重复 1）
- `qt5-9-autolarge` — 9-AutoLarge ← `Qt5/9-AutoLarge` files=4 first=2021-12-24（重复 1）
- `qt5-examples-clocks` — clocks ← `Qt5/Examples/clocks` files=14 first=2021-04-29
- `qt5-examples-examples-pro` — Examples.pro ← `Qt5/Examples/Examples.pro` files=1 first=2021-04-29

### `archive.qt.pyqt`

- `pyqt-a1-hello` ✓ — A1-Hello ← `Linux/PyQt/A1-Hello` files=1 first=2022-07-23
- `pyqt-a2-hello` ✓ — A2-Hello ← `Linux/PyQt/A2-Hello` files=4 first=2022-07-23
- `pyqt-a3-hello` ✓ — A3-Hello ← `Linux/PyQt/A3-Hello` files=5 first=2022-07-23
- `pyqt-a4-signal` — A4-Signal ← `Linux/PyQt/A4-Signal` files=6 first=2022-07-23
- `pyqt-a6-dialog` — A6-Dialog ← `Linux/PyQt/A6-Dialog` files=8 first=2022-07-23
- `qt5-14-hellopyqt` — 14-HelloPyQt ← `Qt5/14-HelloPyQt` files=3 first=2021-12-28（重复 1）
- `qt5-16-pythonui` — 16-PythonUI ← `Qt5/16-PythonUI` files=4 first=2021-12-28（重复 1）
- `qt5-pyqt5` — PyQt5 ← `Qt5/PyQt5` files=1 first=2021-04-26

### `archive.qt.qml-quick`

- `prac-qt-qmlbook-1-2meetqt5` ✓ — 1-2MeetQt5 ← `Practice/QT/QmlBook/1-2MeetQt5` files=8 first=2020-02-22
- `prac-qt-qmlbook-2-2helloworldqml` ✓ — 2-2HelloWorldQML ← `Practice/QT/QmlBook/2-2HelloWorldQML` files=5 first=2020-02-22
- `prac-qt-qmlbook-2-3-1consoleapplication` ✓ — 2-3-1ConsoleApplication ← `Practice/QT/QmlBook/2-3-1ConsoleApplication` files=3 first=2020-02-22
- `prac-qt-qmlbook-2-3-2basicwidgets` — 2-3-2BasicWidgets ← `Practice/QT/QmlBook/2-3-2BasicWidgets` files=5 first=2020-02-22（重复 1）
- `prac-qt-qmlbook-4-1qmlsyntax` — 4-1QMLSyntax ← `Practice/QT/QmlBook/4-1QMLSyntax` files=6 first=2020-02-22
- `prac-qt-qmlbook-4-2-2rectangle` — 4-2-2Rectangle ← `Practice/QT/QmlBook/4-2-2Rectangle` files=12 first=2020-02-22
- `prac-qt-qmlbook-4-2-3textinput` — 4-2-3TextInput ← `Practice/QT/QmlBook/4-2-3TextInput` files=9 first=2020-02-22
- `prac-qt-qmlbook-4-5positioningelements` — 4-5PositioningElements ← `Practice/QT/QmlBook/4-5PositioningElements` files=9 first=2020-02-22
- `prac-qt-qt5-1-consoleapplication` — 1_ConsoleApplication ← `Practice/QT/Qt5开发及实例/1_ConsoleApplication` files=2 first=2020-02-22
- `qml-1-layout` — 1-Layout ← `Linux/QML/1-Layout` files=6 first=2023-01-28
- `qml-1-material` — 1-material ← `Linux/QML/1-material` files=3 first=2023-01-28
- `qt5-14-quick` — 14-Quick ← `Qt5/14-Quick` files=4 first=2022-01-08（重复 1）
- `qt5-14-quickhello` — 14-QuickHello ← `Qt5/14-QuickHello` files=4 first=2022-01-08（重复 1）
- `qt5-15-helloqtquick` — 15-HelloQtQuick ← `Qt5/15-HelloQtQuick` files=4 first=2021-12-28（重复 1）
- `qt5-15-quick` — 15-Quick ← `Qt5/15-Quick` files=6 first=2022-01-08（重复 1）
- `qt5-18-item` — 18-Item ← `Qt5/18-Item` files=4 first=2022-01-18（重复 1）
- `qt5-19-qml` — 19-QML ← `Qt5/19-QML` files=5 first=2022-01-18（重复 1）
- `qt5-22-layoutarchors` — 22-LayoutArchors ← `Qt5/22-LayoutArchors` files=4 first=2022-01-18（重复 1）
- `qt5-32-helloquick` — 32-HelloQuick ← `Qt5/32-HelloQuick` files=5 first=2022-05-25（重复 1）
- `qt5-33-quickstack` — 33-QuickStack ← `Qt5/33-QuickStack` files=8 first=2022-05-25（重复 1）
- `qt5-34-helloqtquick` — 34-HelloQtQuick ← `Qt5/34-HelloQtQuick` files=4 first=2022-05-25（重复 1）
- `qt5-35-qml` — 35-QML ← `Qt5/35-QML` files=5 first=2022-05-25（重复 1）
- `qt5-36-button` — 36-Button ← `Qt5/36-Button` files=4 first=2022-05-25（重复 1）
- `qt5-37-quick` — 37-Quick ← `Qt5/37-Quick` files=8 first=2022-05-25（重复 1）
- `qt5-39-rectangle` — 39-Rectangle ← `Qt5/39-Rectangle` files=4 first=2022-05-25（重复 1）
- `qt5-41-quickcontrols` — 41-QuickControls ← `Qt5/41-QuickControls` files=5 first=2022-06-11（重复 1）
- `qt5-42-controlbutton` — 42-ControlButton ← `Qt5/42-ControlButton` files=4 first=2022-06-11（重复 1）
- `qt5-44-label` — 44-Label ← `Qt5/44-Label` files=4 first=2022-06-11（重复 1）
- `qt5-45-panel` — 45-Panel ← `Qt5/45-Panel` files=4 first=2022-06-11（重复 1）
- `qt5-46-frame` — 46-Frame ← `Qt5/46-Frame` files=4 first=2022-06-11（重复 1）
- `qt5-47-page` — 47-Page ← `Qt5/47-Page` files=4 first=2022-06-11（重复 1）
- `qt5-50-quickpi` — 50-QuickPi ← `Qt5/50-QuickPi` files=7 first=2022-06-26（重复 1）
- `qt5-52-slider` — 52-slider ← `Qt5/52-slider` files=4 first=2022-06-13（重复 1）
- `qt5-53-canvas` — 53-Canvas ← `Qt5/53-Canvas` files=4 first=2022-06-13（重复 1）
- `qt5-57-materialstyle` — 57-MaterialStyle ← `Qt5/57-MaterialStyle` files=7 first=2022-06-13（重复 1）
- `qt5-58-material` — 58-Material ← `Qt5/58-Material` files=7 first=2022-06-13（重复 1）
- `qt5-6-helloqml` — 6-HelloQML ← `Qt5/6-HelloQML` files=4 first=2021-12-08（重复 1）
- `qt5-61-helloworldqml` — 61-HelloWorldQML ← `Qt5/61-HelloWorldQML` files=4 first=2021-04-27（重复 1）
- `qt5-62-quickpi` — 62-QuickPi ← `Qt5/62-QuickPi` files=8 first=2022-06-26（重复 1）
- `qt5-62-quickui` — 62-QuickUI ← `Qt5/62-QuickUI` files=3 first=2021-04-27（重复 1）
- `qt5-65-gridquick` — 65-GridQuick ← `Qt5/65-GridQuick` files=9 first=2022-06-26（重复 1）
- `qt5-8-qmlsignal` — 8-QMLSignal ← `Qt5/8-QMLSignal` files=4 first=2021-12-24（重复 1）
- `qt5-qml-1-quickui` — 1-QuickUI ← `Qt5/QML/1-QuickUI` files=3 first=2021-04-29（重复 1）
- `qt5-qml-qml-pro` — QML.pro ← `Qt5/QML/QML.pro` files=1 first=2021-04-29（重复 1）

### `archive.qt.signals-slots`

- `qt5-01-signalslot` ✓ — 01-SignalSlot ← `Qt5/01-SignalSlot` files=5 first=2021-12-08（重复 1）
- `qt5-20-signalandslot` ✓ — 20-SignalAndSlot ← `Qt5/20-SignalAndSlot` files=13 first=2021-09-14（重复 1）

### `archive.qt.windows-dialogs`

- `qt5-13-embedwidget` ✓ — 13-EmbedWidget ← `Qt5/13-EmbedWidget` files=16 first=2021-05-23（重复 1）
- `qt5-2-muitiwindow` ✓ — 2-MuitiWindow ← `Qt5/2-MuitiWindow` files=8 first=2021-03-25（重复 1）
- `qt5-21-twowindow` ✓ — 21-TwoWindow ← `Qt5/21-TwoWindow` files=8 first=2021-09-14（重复 1）
- `qt5-3-login` — 3-Login ← `Qt5/3-Login` files=8 first=2021-03-25（重复 1）
- `qt5-40-multifile` — 40-MultiFile ← `Qt5/40-MultiFile` files=5 first=2022-05-25（重复 1）
- `qt5-56-multipage` — 56-MultiPage ← `Qt5/56-MultiPage` files=7 first=2022-06-13（重复 1）
- `qt5-92-callapp` — 92-CallApp ← `Qt5/92-CallApp` files=5 first=2021-04-13（重复 1）
- `qt5-93-qsystemtray` — 93-QSystemTray ← `Qt5/93-QSystemTray` files=13 first=2021-04-14（重复 1）
- `qt5-96-dropfile` — 96-DropFile ← `Qt5/96-DropFile` files=5 first=2021-04-23（重复 1）


## 补录（2026-10-21T15:47:14）

- 按 claude-code FYI：并入 `Practice/XNode` 为 keep 单元 `prac-xnode`（files=54，topic=`archive.qt.network`，first=2023-05-09）。
- 覆盖校验需把 XNode 54 个文件算进 scoped（见 verify-qt-xnode.txt）。
