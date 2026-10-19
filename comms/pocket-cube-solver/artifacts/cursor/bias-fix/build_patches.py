#!/usr/bin/env python3
"""写出三份选项重写补丁 JSON（只写本目录，不改 programming/）。"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 每条：choices 已按最终顺序排好，answer 是正确项下标。
# 正确项措辞若改写，保持原意；干扰项手写、等长、无中文括号注释。

SNAKE: list[dict] = [
    {
        "id": "snake.window.redraw",
        "choices": [
            "每帧用当前时间算出新位置，从头重画一遍",
            "给方块挂上速度属性，等库在回调里挪它",
            "只擦掉方块动过的那一块脏矩形再补画",
            "注册一个移动回调，到点由库自动触发",
        ],
        "answer": 0,
    },
    {
        "id": "snake.window.fps",
        "choices": [
            "游戏逻辑每秒最多只能推进六十步",
            "输入采样频率被锁死在每秒六十次",
            "渲染循环每秒最多跑满六十帧",
            "计时器寄存器每秒恰好溢出六十次",
        ],
        "answer": 2,
    },
    {
        "id": "snake.window.dt",
        "choices": [
            "开机到现在一共过了多少秒",
            "游戏窗口从创建起累计的秒数",
            "距离下一次垂直同步还剩多久",
            "上一帧从开始到结束花掉的秒数",
        ],
        "answer": 3,
    },
    {
        "id": "snake.window.font",
        "choices": [
            "raylib 的字符串接口只认窄字符编码",
            "C++ 源文件里根本不允许出现中文",
            "默认字体只带 ASCII 字形，中文要另加载 TTF",
            "英文字形的栅格化路径天生比中文更快",
        ],
        "answer": 2,
    },
    {
        "id": "snake.grid.acc",
        "choices": [
            "while 在分支预测上总是比 if 更有利",
            "掉帧时 acc 攒了多个节拍，要一口气补完",
            "某些编译器不允许 if 直接比较浮点数",
            "while 能保证累加器每次都刚好归零",
        ],
        "answer": 1,
    },
    {
        "id": "snake.grid.cell",
        "choices": [
            "像素坐标才是逻辑世界的真正实体",
            "格子是真身，像素只是它每帧的投影",
            "格子与像素各自独立演化、互不从属",
            "真正的主人是屏幕硬件给出的分辨率",
        ],
        "answer": 1,
    },
    {
        "id": "snake.grid.fps",
        "choices": [
            "约 2.5 格，逻辑步长跟着帧率一起减半",
            "还是 5 格，逻辑节拍并不跟着帧率走",
            "会变成 10 格，补偿机制自动翻倍",
            "无法确定，完全取决于显卡当时负载",
        ],
        "answer": 1,
    },
    {
        "id": "snake.grid.hz",
        "choices": [
            "每帧最多只允许更新一次逻辑状态",
            "每 0.2 秒逻辑恰好向前推进一格",
            "逻辑线程每秒只被调度 0.2 次",
            "渲染管线的延迟上限被钉在 0.2 秒",
        ],
        "answer": 1,
    },
    {
        "id": "snake.body.deque",
        "choices": [
            "头进一格、尾出一格，中间各节原地不动",
            "把每一节都向前复制到相邻的格子",
            "先把整条队列反向，再从头到尾遍历",
            "按节号两两交换相邻节的坐标",
        ],
        "answer": 0,
    },
    {
        "id": "snake.body.fold",
        "choices": [
            "渲染阶段把格子坐标换算成像素时算错了",
            "队列容量溢出，尾节被挤出合法范围",
            "两帧内连改两次方向，一步之内掉头叠身",
            "帧率过低丢帧，中间节的坐标没来得及更新",
        ],
        "answer": 2,
    },
    {
        "id": "snake.body.foldnotdead",
        "choices": [
            "死亡判定模块还没有接到工程里",
            "折叠那一步头根本没有成功入队",
            "本章只判出界，折叠碰不到「死」的后果",
            "输入缓冲已经把第二次按键挡在外面",
        ],
        "answer": 2,
    },
    {
        "id": "snake.body.deadstep",
        "choices": [
            "省掉一次可能触发扩容的内存分配",
            "让画面停在撞墙前一刻，死因看得见",
            "避免队列下标越界抛出运行时异常",
            "下一章会拿这颗未入队的头做复活",
        ],
        "answer": 1,
    },
    {
        "id": "snake.input.queue",
        "choices": [
            "缓冲直接吞掉第二次及以后的按键",
            "键盘只排队，逻辑每步只消费队首方向",
            "缓冲让逻辑节拍跑得比原来更快",
            "所有间隔过短的按键一律被丢弃",
        ],
        "answer": 1,
    },
    {
        "id": "snake.input.opposite",
        "choices": [
            "压队时写判断比在消费侧写更短",
            "压队时能对照队尾与朝向，一步掉头挡在入口",
            "消费时再判反向会拖慢整条蛇的速度",
            "两种时机完全等价，选哪边都行",
        ],
        "answer": 1,
    },
    {
        "id": "snake.input.capacity",
        "choices": [
            "内存里放不下比三格更多的方向枚举",
            "缓冲太深，早先的方向很久才生效，手感发飘",
            "标准库 deque 实现本身限制了长度",
            "防止玩家连按出自我循环的方向序列",
        ],
        "answer": 1,
    },
    {
        "id": "snake.input.verify",
        "choices": [
            "随手玩两分钟，没再看见折叠就算过",
            "重放「朝右走、两帧内按上再左」，看先上后左",
            "在源码里搜到 pending 字段就认定修好",
            "把目标帧率调到一百二十再玩一轮",
        ],
        "answer": 1,
    },
    {
        "id": "snake.food.grow",
        "choices": [
            "在队列尾部额外插入一个新的身体格",
            "移动后再把蛇头坐标复制多一份",
            "照常头进，只是这一步尾巴不出队",
            "把食物那一格直接改写成蛇身标记",
        ],
        "answer": 2,
    },
    {
        "id": "snake.food.selfbite",
        "choices": [
            "前面几章作者临时把自吃判定漏掉了",
            "固定长度时折叠也死不了；变长后头撞身才成死法",
            "自吃判定必须读到食物坐标才能编写",
            "第四章的输入缓冲其实已经挡住了自吃",
        ],
        "answer": 1,
    },
    {
        "id": "snake.food.random",
        "choices": [
            "蛇一开始变长就必须立刻换抽样算法",
            "空格稀少、重试暴涨时，才值得改成先收集再抽",
            "无论空格多稀，重试次数都停在常数级",
            "换不换算法完全取决于编译器优化等级",
        ],
        "answer": 1,
    },
    {
        "id": "snake.food.wallbite",
        "choices": [
            "两个独立的死循环分别检测墙和身体",
            "写进同一判定：出界或头落在身体格上都死",
            "撞墙放在 step 里，自吃放到渲染阶段查",
            "自吃完全交给玩家自己留意，代码不判",
        ],
        "answer": 1,
    },
    {
        "id": "snake.state.phase",
        "choices": [
            "主要是为了把源文件的总行数压下去",
            "同一键在不同局面含义不同，需要明确安放处",
            "状态机可以直接把渲染帧率抬上去",
            "有了相位就可以把输入缓冲整段删掉",
        ],
        "answer": 1,
    },
    {
        "id": "snake.state.adopt",
        "choices": [
            "第三章当晚就把那行重构成了 reset",
            "第六章加入开始与暂停后，才收进状态机相位",
            "凑合写法可以一直用，永远不会被收编",
            "输入缓冲一落地，那行重开就被替代了",
        ],
        "answer": 1,
    },
    {
        "id": "snake.state.pause",
        "choices": [
            "浮点累加太久会丢精度，所以必须清零",
            "暂停流逝的时间不是游戏时间，不清会瞬移补步",
            "清零只是为了让下一帧从整数节拍起算",
            "否则 while 补步可能陷入理论上的死循环",
        ],
        "answer": 1,
    },
    {
        "id": "snake.state.over",
        "choices": [
            "布尔被删掉了，死亡不再需要显式表示",
            "升格成 Phase::Over，与开始、暂停同级",
            "拆成 dying 与 dead 两个并列的布尔",
            "挪进渲染层，由画面内容反推是否已死",
        ],
        "answer": 1,
    },
    {
        "id": "snake.score.event",
        "choices": [
            "蛇每向前走完一格就加十分",
            "吃到食物的那一次事件上加分",
            "玩家每成功转向一次就加分",
            "按墙上时钟每隔固定间隔加分",
        ],
        "answer": 1,
    },
    {
        "id": "snake.score.timing",
        "choices": [
            "主要是为了少做几次比较以省电",
            "只有死亡才是终局，终局判定挂在状态转移上",
            "每次得分都写文件会加快磨损磁盘",
            "避免渲染线程与逻辑线程抢着读写纪录",
        ],
        "answer": 1,
    },
    {
        "id": "snake.score.location",
        "choices": [
            "工作目录下的文件读写延迟天生偏高",
            "落点随启动方式漂移，还可能没写权限、互相覆盖",
            "那种文本格式本身就不能跨操作系统使用",
            "raylib 的存盘接口拒绝接受相对路径",
        ],
        "answer": 1,
    },
    {
        "id": "snake.score.const",
        "choices": [
            "TextFormat 给出 const 指针，SaveFileText 要非 const 缓冲",
            "snprintf 路径在性能上总是快过字符串拼接",
            "SaveFileText 只吃格式化浮点，不认整数字面量",
            "先 snprintf 只是为了在文件末尾多垫一个换行",
        ],
        "answer": 0,
    },
    {
        "id": "snake.logic.pure",
        "choices": [
            "raylib 的头文件根本没法和 C++ 一起编",
            "规则不靠窗口；不沾图形库才能被无窗口程序验证",
            "多 include 一层会明显拖慢每一次增量编译",
            "raylib 许可证不允许被静态链接进测试",
        ],
        "answer": 1,
    },
    {
        "id": "snake.logic.move",
        "choices": [
            "一步到位太累，所以这章故意只搬不改",
            "搬家与改行为混做，出错时分不清是谁坏的",
            "raylib 接口禁止同一次改动里同时动两边",
            "这一章只是为了把目录结构凑成对称样子",
        ],
        "answer": 1,
    },
    {
        "id": "snake.logic.stays",
        "choices": [
            "logic.hh 的体量已经装不下更多声明",
            "关掉窗口它们就不成立：呈现与宿命不属于规则",
            "这些代码写起来太短，搬过去不划算",
            "raylib 禁止在非 main 翻译单元里使用它们",
        ],
        "answer": 1,
    },
    {
        "id": "snake.logic.samesight",
        "choices": [
            "画面完全没变，说明这一章其实是多余的",
            "规则第一次有了独立住址——变的是验证途径",
            "游戏在同样输入下会明显跑得更快",
            "工程里的源文件总数被成功削减了",
        ],
        "answer": 1,
    },
    {
        "id": "snake.test.memory",
        "choices": [
            "把当年的 bug 截图永久存进版本库",
            "把触发折叠的操作写成断言，每次构建自动重放",
            "在源码注释里详细记下 bug 的来龙去脉",
            "给 bug 编个号，归档进项目文档目录",
        ],
        "answer": 1,
    },
    {
        "id": "snake.test.pure",
        "choices": [
            "raylib 头与测试框架的宏定义互相冲突",
            "被测规则不靠窗口；不链图形库，测试哪都能跑",
            "测试文件 include raylib 会拖慢链接步骤",
            "raylib 不允许进入任何自动化测试二进制",
        ],
        "answer": 1,
    },
    {
        "id": "snake.test.what",
        "choices": [
            "画面质量对这门课来说根本不重要",
            "「头在哪、死没死」可断言；「看起来对」没有标准答案",
            "画面像素级对比在当前工具链上做不到",
            "raylib 禁止测试代码去读回帧缓冲",
        ],
        "answer": 1,
    },
    {
        "id": "snake.test.ctest",
        "choices": [
            "每次打开游戏窗口时会在后台自动跑",
            "构建后用 ctest 一条命令跑完，check 与 CI 都会调用",
            "必须手动双击测试可执行文件才能看见结果",
            "只有挂上调试器单步时测试才会被执行",
        ],
        "answer": 1,
    },
    {
        "id": "snake.polish.lerp",
        "choices": [
            "acc 是当前帧序号；t 近 1 时蛇会回到起点",
            "acc 是自上一步攒下的时间；t 近 1 时几乎滑进目标格",
            "acc 是蛇的瞬时加速度；t 近 1 表示正在加速",
            "acc 是音频环形缓冲水位；t 近 1 时音高升高",
        ],
        "answer": 1,
    },
    {
        "id": "snake.polish.sound",
        "choices": [
            "整段声音最长只允许持续两万两千个采样",
            "每秒用 22050 个点描述波形；写入与还原须同速",
            "音量被固定成两万两千分贝再除以一千",
            "播放器环形缓冲的字节数被钉死在这个常数",
        ],
        "answer": 1,
    },
    {
        "id": "snake.polish.accel",
        "choices": [
            "渲染层的函数签名里已经塞不下加速参数",
            "关掉窗口「越吃越快」仍成立——它属于规则层",
            "渲染每帧都跑，把加速写那里会过于频繁",
            "加速要随机数，而随机引擎只活在 logic.hh",
        ],
        "answer": 1,
    },
    {
        "id": "snake.polish.observe",
        "choices": [
            "故意晚一帧响，听感上会显得更自然",
            "吃到在规则层，声音属呈现——观察「变长」即可",
            "PlaySound 在 step 函数内部调用会被库拒绝",
            "这样写可以少声明一个专门的布尔标志",
        ],
        "answer": 1,
    },
    {
        "id": "snake.design.asbuilt",
        "choices": [
            "后补文档质量可以低一些，所以特意标明",
            "十章是演化出来的；总览整理终点，不能倒推该教什么",
            "as-built 是国家标准强制要求的章节标题",
            "写明之后就表示代码冻结，不会再改动",
        ],
        "answer": 1,
    },
    {
        "id": "snake.design.invariant",
        "choices": [
            "随机游走测试的墙钟时间会明显更短",
            "无论按键序列怎样局面都合法——能挡住没想到的序列",
            "有了不变式就可以删掉全部手写例子测试",
            "不变式本身就能证明这款游戏一定好玩",
        ],
        "answer": 1,
    },
    {
        "id": "snake.design.trace",
        "choices": [
            "音效需求优先级低，所以不必纳入验证",
            "音效在呈现层、靠设备，不能脱离窗口自动验，故标人工",
            "当前测试框架缺少针对波形的断言接口",
            "只因为 FR-9 排在需求列表的最后一条",
        ],
        "answer": 1,
    },
    {
        "id": "snake.design.tail",
        "choices": [
            "这是待修缺陷，规则上应当允许追尾吃尾",
            "现行决策 D-3：先判定再出尾；要改就连测试一起改",
            "这是 raylib 绘图顺序带来的硬性限制",
            "从未写入文档，属于实现上的未定义行为",
        ],
        "answer": 1,
    },
]

# 上面 snake 答案仍多落在 1——下面用脚本再平衡位置与最长项。
# 真正写出的补丁以 balance() 之后为准。


CHESS: list[dict] = [
    {
        "id": "chess.window.builder",
        "choices": [
            "编译 blp 时窗口会自己创建并弹出来",
            "C++ 仍要建 Application，用 Builder 取出窗口并 present",
            "把 blp 里的控件再在 C++ 里 append 一遍才算数",
            "只要写好 style.css，进程启动后窗口就会出现",
        ],
        "answer": 1,
    },
    {
        "id": "chess.window.identity",
        "choices": [
            "两边必须是同一个字符串，否则窗口开不出来",
            "id 不能含连字符，所以用下划线；标题可以是中文",
            "应用 id 必须写成中文，输入法才能进窗口",
            "标题栏 Label 会覆盖 id，id 写成什么都无所谓",
        ],
        "answer": 1,
    },
    {
        "id": "chess.window.header",
        "choices": [
            "Application 的 id 字符串被画在标题栏中间",
            "窗口 title 属性本身就画在标题栏正中",
            "HeaderBar 的 title-widget，也就是那个 Label",
            "style.css 里用 content 属性写进去的文字",
        ],
        "answer": 2,
    },
    {
        "id": "chess.window.both",
        "choices": [
            "两份程序复用了完全相同的应用 id",
            "都标了 NON_UNIQUE，再启动一次就再开一扇",
            "blp 与 C++ 会在运行时自动合并成一个进程",
            "还没有棋盘，所以单实例限制暂时不生效",
        ],
        "answer": 1,
    },
    {
        "id": "chess.layout.box",
        "choices": [
            "写在 window.blp：board_slot 设 hexpand，侧栏 width-request 260",
            "写在 style.css 的窗口最小宽度规则里",
            "只能在 C++ 里 set_size_request，blp 排不了横盒",
            "由 Wood 涂色逻辑顺便决定，盒子本身不参与",
        ],
        "answer": 0,
    },
    {
        "id": "chess.layout.css",
        "choices": [
            "写在每个 Label 构造时传入的内联属性里",
            "写在 style.css 的 .side 与 .player 选择器上",
            "写在 window.blp 标签旁，直接填十六进制颜色",
            "由 Wood 组件的木色自动传导到侧栏文字",
        ],
        "answer": 1,
    },
    {
        "id": "chess.layout.slot",
        "choices": [
            "因为 Blueprint 语法不允许放置任何盒子",
            "DrawingArea 的绘制在 C++，界面文件只留 board_slot",
            "木色只能靠 CSS 背景图，控件树画不出来",
            "这一章还没有侧栏，所以棋盘无处可挂",
        ],
        "answer": 1,
    },
    {
        "id": "chess.layout.sensitive",
        "choices": [
            "窗口还缺少 HeaderBar，按钮事件到不了",
            "按钮标了 sensitive: false，这一章只占位置",
            "侧栏固定 260 像素，把按钮挤出了可见区",
            "Wood 绘制层盖住了按钮，点击被吃掉",
        ],
        "answer": 1,
    },
    {
        "id": "chess.board.vector",
        "choices": [
            "线是位图资源，放大时由系统做平滑插值",
            "按当前控件像素，用矢量图重新画了一遍",
            "style.css 里写死了图像的设备像素比",
            "界面文件会在拉大窗口时重排九宫网格",
        ],
        "answer": 1,
    },
    {
        "id": "chess.board.cross",
        "choices": [
            "落在格子中心，盘面一共划分成 9×8 格",
            "落在交叉点上，横 9 路、竖 10 行，共 90 点",
            "落在河界那条空白带的几何中心",
            "落在侧栏预留的那 260 像素宽区域内",
        ],
        "answer": 1,
    },
    {
        "id": "chess.board.shared",
        "choices": [
            "blp 里先画线，C++ 再把同样的线抄一份",
            "两程序都编同一份 BoardView，界面只留 board_slot",
            "style.css 的 .side 规则会顺带描出九宫",
            "后一章的构建脚本会回写前一章的棋盘线",
        ],
        "answer": 1,
    },
    {
        "id": "chess.board.nine",
        "choices": [
            "最右边那一路，对应坐标 x = 8",
            "最左边那一路，对应坐标 x = 0",
            "正中间那一路，对应坐标 x = 4",
            "河界右侧，与黑方的数字 9 完全重合",
        ],
        "answer": 1,
    },
    {
        "id": "chess.piece.center",
        "choices": [
            "画在格子中心，边长正好等于一格宽",
            "画在交叉点中心，边长大约是一格的 0.92",
            "画在侧栏列表里，棋盘上只保留线条",
            "叠在河界「楚河汉界」四个字的正上方",
        ],
        "answer": 1,
    },
    {
        "id": "chess.piece.general",
        "choices": [
            "(0, 0)，也就是棋盘的左上角交叉点",
            "(4, 0)，黑方底线正中的交叉点",
            "(4, 9)，红方底线正中的交叉点",
            "(8, 9)，红方底线最右侧的交叉点",
        ],
        "answer": 2,
    },
    {
        "id": "chess.piece.axis",
        "choices": [
            "y 往上增大，并且红方棋子都在 y = 0",
            "y 往下增大；红用帅仕相兵，黑用将士象卒",
            "红黑共用一张「帅」图，只靠 CSS 切换颜色",
            "兵和卒都画在 y = 5 的河界交叉点上",
        ],
        "answer": 1,
    },
    {
        "id": "chess.piece.click",
        "choices": [
            "帅向前走一步，棋谱自动记「帅五进一」",
            "弹出可走点高亮，但这一步还不能真走",
            "什么都不走；棋子这一章只是画上去的",
            "界面文件版能走子，代码版窗口仍不能走",
        ],
        "answer": 2,
    },
    {
        "id": "chess.move.owner",
        "choices": [
            "写在 window.blp 按钮的 on-clicked 属性里",
            "写在 style.css 针对 button.play 的规则里",
            "按钮在界面文件；点击后做什么在 Session，规则在 Position",
            "界面版规则写在 blp，代码版规则写在 Position，两套各算",
        ],
        "answer": 2,
    },
    {
        "id": "chess.move.rook",
        "choices": [
            "车和炮吃子都要求中间恰好隔着一个子",
            "车中间不能有子；炮吃子时中间恰好一个子",
            "车和炮吃子都要求中间一个子都没有",
            "炮根本不能吃子，只允许平移到空交叉点",
        ],
        "answer": 1,
    },
    {
        "id": "chess.move.block",
        "choices": [
            "马腿有子仍可跳，象眼有子才真正卡住",
            "马腿或象眼有子就不能跳；仕象都不能过河",
            "象可以过河，前提只是象眼那一格是空的",
            "仕可以离开九宫，只要每一步都是斜线",
        ],
        "answer": 1,
    },
    {
        "id": "chess.move.step",
        "choices": [
            "走到红方的一路，也就是坐标 x = 8",
            "向前走了一步，这里的「一」是步数不是路名",
            "吃掉了对方棋盘上某个「一」字标记的子",
            "帅平移到了黑方报路里的第 1 路",
        ],
        "answer": 1,
    },
    {
        "id": "chess.move.end",
        "choices": [
            "判和棋，因为帅眼下并没有被将军",
            "判黑胜 · 红方困毙",
            "判黑胜 · 红方被将死",
            "先不判胜负，要等到出现长将再说",
        ],
        "answer": 1,
    },
]


CPP: list[dict] = [
    {
        "id": "cpp.TypeSemantics.initialization#0",
        "choices": [
            "int x{3.14};",
            "int x = 3.14;",
            "int x(3.14);",
            "int x = int(3.14);",
        ],
        "answer": 0,
    },
    {
        "id": "cpp.TypeSemantics.initialization#1",
        "choices": [
            "Tracer a{1};",
            "Tracer b(1);",
            "Tracer c = 1;",
            "Tracer d = Tracer{1};",
        ],
        "answer": 2,
    },
    {
        "id": "cpp.TypeSemantics.object_lifetime#0",
        "choices": [
            "return 执行完、离开作用域时，按构造的逆序析构",
            "等到整个进程退出时再把局部对象一并析构",
            "下一次在堆上执行 new 的时候顺带析构",
            "只有程序员显式调用 delete 才会析构",
        ],
        "answer": 0,
    },
    {
        "id": "cpp.TypeSemantics.object_lifetime#1",
        "choices": [
            "为对象分配好存储空间的那一刻就算开始",
            "初始化全部完成的那一刻生命周期才开始",
            "对象第一次被某条语句读取的那一刻",
            "进入构造函数体、成员初始化之前那一刻",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.TypeSemantics.value_category#0",
        "choices": [
            "立刻把 x 的资源搬进另一个新对象里",
            "把左值表达式变成将亡值，好让重载选中移动",
            "把 x 清空，恢复成类型的默认状态",
            "从此禁止编译器再对 x 做任何拷贝",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.TypeSemantics.value_category#1",
        "choices": [
            "纯右值没有对象身份；将亡值指向即将结束的对象",
            "纯右值一定是字面量；将亡值一定是函数返回值",
            "纯右值可以取地址；将亡值表达式不能取地址",
            "两者只是拼写习惯不同，值类别其实一样",
        ],
        "answer": 0,
    },
    {
        "id": "cpp.Reference.reference_basics#0",
        "choices": [
            "引用可以先声明成空的，稍后再完成绑定",
            "引用声明时必须绑到对象，之后也不能改绑",
            "引用和指针一样，允许处于空的未绑定状态",
            "给引用赋值就会让它改去绑定另一个对象",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.Reference.reference_basics#1",
        "choices": [
            "r 改去绑定对象 b，不再是 a 的别名",
            "a 被赋成 b 的值，r 仍然只是 a 的名字",
            "语句会再造出一个新的引用对象出来",
            "编译失败，因为已绑定的引用不能出现在赋值左边",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.ValueSemantics.copy_control#0",
        "choices": [
            "每个对象都会得到一份彼此独立的资源副本",
            "两对象共享同一指针，析构时会重复释放",
            "编译器发现自定义析构后会拒绝生成拷贝构造",
            "默认拷贝会被静默改写成深拷贝移动构造",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.ValueSemantics.copy_control#1",
        "choices": [
            "默认构造、析构函数与拷贝赋值运算符",
            "析构函数、拷贝构造函数与拷贝赋值运算符",
            "移动构造、移动赋值运算符与成员 swap",
            "默认构造、拷贝构造函数与移动构造函数",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.ValueSemantics.rvalue#0",
        "choices": [
            "一个普通的具名左值变量",
            "临时对象，或经 std::move 得到的将亡值",
            "只有整型字面量 0 这一种实参",
            "任意带 const 限定的对象都可以直接绑",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.ValueSemantics.rvalue#1",
        "choices": [
            "好让函数去改写调用方传来的 const 对象",
            "好让重载区分「还要用」和「可以被掏空」",
            "用来彻底取代形参里的所有 const 引用",
            "用来禁止编译器再做返回值优化",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.ValueSemantics.move_semantics#0",
        "choices": [
            "对象已经结束生命周期，再碰就是未定义行为",
            "有效但未指定：可析构、可再赋值，勿读旧值",
            "与移动之前相比，可观察状态完全不变",
            "自动变成空指针常量，等价于赋了 nullptr",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.ValueSemantics.move_semantics#1",
        "choices": [
            "少了一次对元素内部缓冲区的深拷贝",
            "编译器可以跳过元素类型的全部构造函数",
            "扩容之后容器里的元素个数不再增加",
            "被移走的旧元素再也用不着调用析构",
        ],
        "answer": 0,
    },
    {
        "id": "cpp.RAII.basic#0",
        "choices": [
            "类的析构函数",
            "调用者手写的 finally 清理段",
            "进程退出时注册的全局钩子",
            "下一次构造同类对象时的构造函数",
        ],
        "answer": 0,
    },
    {
        "id": "cpp.RAII.basic#1",
        "choices": [
            "析构被跳过，于是资源顺着异常路径泄漏",
            "栈展开时照常析构，资源仍然被释放掉",
            "必须在 catch 子句里手动再调用一次析构",
            "对象泄漏，但操作系统会立刻收回底层资源",
        ],
        "answer": 1,
    },
    {
        "id": "cpp.RAII.unique#0",
        "choices": [
            "拷贝会让两个指针都以为自己拥有同一资源",
            "标准库这一版还没来得及实现拷贝构造",
            "拷贝路径太慢，所以接口上直接删掉了",
            "unique_ptr 被规定只能放在全局命名空间",
        ],
        "answer": 0,
    },
    {
        "id": "cpp.RAII.unique#1",
        "choices": [
            "p 与 q 析构时都会去释放那块资源",
            "q 负责释放，p 在移动后不再拥有资源",
            "两边都不释放，必须再手动调用一次 reset",
            "仍由 p 释放，q 只是只读观察那块资源",
        ],
        "answer": 1,
    },
]


def rotate_to(choices: list[str], old_answer: int, new_answer: int) -> list[str]:
    """把正确项从 old_answer 挪到 new_answer，其余相对顺序尽量保持。"""
    correct = choices[old_answer]
    others = [c for i, c in enumerate(choices) if i != old_answer]
    out = [""] * len(choices)
    out[new_answer] = correct
    j = 0
    for i in range(len(choices)):
        if i == new_answer:
            continue
        out[i] = others[j]
        j += 1
    return out


def unique_longest(choices: list[str], answer: int) -> bool:
    """正确项独占最长（并列不算）。"""
    L = len(choices[answer])
    return all(len(c) < L for i, c in enumerate(choices) if i != answer)


def balance(items: list[dict], pos_targets: list[int]) -> list[dict]:
    """只轮转答案位置，不改任何选项措辞。"""
    n = len(items)
    assert sum(pos_targets) == n
    schedule: list[int] = []
    for pos, cnt in enumerate(pos_targets):
        schedule.extend([pos] * cnt)
    order = sorted(range(n), key=lambda i: items[i]["id"])
    assigned = [0] * n
    for slot, idx in enumerate(order):
        assigned[idx] = schedule[slot]

    out = []
    for i, item in enumerate(items):
        ch = list(item["choices"])
        ans = item["answer"]
        new_ans = assigned[i]
        if new_ans != ans:
            ch = rotate_to(ch, ans, new_ans)
            ans = new_ans
        out.append({"id": item["id"], "choices": ch, "answer": ans})
    return out


def write(name: str, rows: list[dict]) -> None:
    path = HERE / f"{name}.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.name}: {len(rows)} items")


def load_originals(app: str) -> dict[str, dict]:
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_patch", HERE / "check_patch.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.load_original(app)


# 原文已合格（长度差≤40% 且无中文括号）：补丁里选项原文一字不动，只洗牌。
KEEP_VERBATIM = {
    "snake.window.redraw",
    "snake.window.fps",
    "snake.grid.cell",
    "snake.grid.hz",
    "snake.body.deque",
    "snake.food.grow",
    "chess.window.identity",
    "chess.board.vector",
    "chess.piece.general",
    "chess.piece.axis",
    "chess.piece.click",
    "chess.move.end",
    "cpp.TypeSemantics.object_lifetime#1",
    "cpp.ValueSemantics.copy_control#1",
}

# 仅去中文括号或原文断言过短时的措辞改写（断言不变）。
CORRECT_REWRITES = {
    "snake.input.verify": "把触发它的同一组操作重放一遍：朝右走，两帧内按上再左，看蛇先上后左",
    "snake.design.tail": "现行设计决策 D-3：判定先于尾巴出队；用测试钉住，要改就连 step 顺序和那条测试一起改",
    "snake.score.event": "分数加在吃到食物这一次事件上",
    "cpp.RAII.basic#0": "放在类的析构函数里",
    # 缩短正确项以匹配干扰项长度（断言不变）
    "chess.layout.box": "写在 window.blp：棋盘 hexpand，侧栏 width-request 260",
    "chess.window.builder": "C++ 仍要建 Application，用 Builder 取出窗口并 present",
    "chess.layout.slot": "DrawingArea 绘制在 C++，界面文件只留 board_slot",
    "chess.board.shared": "两程序都编同一份 BoardView，界面只留 board_slot",
    "chess.window.header": "HeaderBar 的 title-widget，也就是那个 Label",
    "chess.board.cross": "落在交叉点上，横 9 路、竖 10 行，共 90 点",
}


def apply_keep_verbatim(items: list[dict], originals: dict[str, dict]) -> None:
    for it in items:
        if it["id"] not in KEEP_VERBATIM:
            continue
        orig = originals[it["id"]]
        it["choices"] = list(orig["choices"])
        it["answer"] = orig["answer"]


def apply_correct_rewrites(items: list[dict]) -> None:
    """在手写/KEEP 结果上覆盖必要的正确项措辞（去括号、缩短断言不变）。"""
    for it in items:
        text = CORRECT_REWRITES.get(it["id"])
        if text is None:
            continue
        it["choices"][it["answer"]] = text


def apply_distractor_overrides(items: list[dict], overrides: dict[str, dict[int, str]]) -> None:
    """按题内下标替换干扰项（手写等长/更长，禁止共享填充尾巴）。"""
    by_id = {it["id"]: it for it in items}
    for qid, repl in overrides.items():
        it = by_id[qid]
        for idx, text in repl.items():
            if idx == it["answer"]:
                raise SystemExit(f"override hits correct answer: {qid}[{idx}]")
            it["choices"][idx] = text


# 降独占最长：把一条干扰项改成更长、有实质内容的错说（每题措辞不同）。
# 同时顺手修 BADLEN（正确项相对过长时加长干扰项；过短时见 CORRECT_REWRITES）。
SNAKE_DISTRACTOR_OVERRIDES: dict[str, dict[int, str]] = {
    # —— 降 UL（干扰项写得比正确项更长）——
    "snake.window.dt": {
        0: "从开机那一刻起累计到现在的全部秒数，跟当前这一帧无关",
        1: "游戏窗口创建之后一直在累加的存活秒数，用来算总时长",
    },
    "snake.window.font": {
        0: "raylib 的字符串绘制接口底层只认窄字符编码，中文一进来就会乱码",
        1: "C++ 源文件的字符集规则本身就不允许出现非 ASCII 的中文面字",
        3: "英文字形走的是更短的栅格化路径，所以天生比中文绘制更快更省",
    },
    "snake.body.foldnotdead": {
        0: "死亡判定模块此时还根本没有接到工程里，所以折叠不会被判死",
        1: "折叠发生的那一步里，新头其实没有成功写进队列，碰撞无从谈起",
        3: "输入缓冲已经把第二次反向按键挡在外面，折叠状态根本不会出现",
    },
    "snake.body.deadstep": {
        0: "省掉一次可能触发扩容的堆分配，让死亡路径的内存轨迹更干净",
        2: "避免队列在非法下标上继续生长，从而抛出难以复现的运行时异常",
        3: "下一章打算拿这颗尚未入队的头做复活演出，所以必须先留在外面",
    },
    "snake.input.queue": {
        0: "缓冲策略是直接吞掉第二次及以后的按键，只保留第一次转向意图",
        2: "缓冲会让逻辑节拍比原来跑得更快，从而把折叠窗口挤出时间轴",
        3: "所有间隔短于一帧的按键一律丢弃，只留下稀疏且离散的方向采样",
    },
    "snake.input.capacity": {
        0: "内存里放不下比三格更多的方向枚举值，再深就会踩到实现上限",
        2: "标准库 deque 的节点分配策略本身就限制了可排队的方向个数",
        3: "防止玩家连按拼出自我循环的方向序列，把蛇锁进原地打转",
    },
    "snake.food.random": {
        0: "蛇一开始变长就必须立刻换抽样算法，否则早期也会卡在重试上",
        2: "无论空格多稀，拒绝采样的期望重试次数都停在常数级，不必换",
        3: "换不换算法完全取决于编译器优化等级，跟空格密度没有关系",
    },
    "snake.state.phase": {
        0: "引入相位主要是为了把源文件总行数压下去，让阅读负担更轻",
        2: "有了显式状态机就可以直接抬高渲染帧率，跟输入语义无关",
        3: "一旦相位落地，输入缓冲整段都可以删掉，由相位兼任排队职责",
    },
    "snake.state.adopt": {
        0: "第三章当晚就把那行散装判断重构成了 reset，不必等到第六章",
        2: "凑合写法可以一直用下去，状态机相位永远不会真正收编它",
        3: "输入缓冲一落地，那行重开逻辑就被替代，相位只是事后命名",
    },
    "snake.score.timing": {
        0: "主要是为了少做几次比较以省电，跟终局语义其实没有直接关系",
        2: "每次得分都同步写文件会加快磨损磁盘，所以才推迟到终局再写",
        3: "避免渲染线程与逻辑线程抢着读写纪录，把写入点收拢到一处",
    },
    "snake.score.location": {
        0: "工作目录下的文件读写延迟天生偏高，不适合存放需要频繁更新的纪录",
        2: "那种纯文本格式本身就不能跨操作系统使用，换目录也救不了",
        3: "raylib 的存盘接口拒绝接受相对路径，所以工作目录方案根本编译不过",
    },
    "snake.logic.samesight": {
        0: "画面完全没变，说明这一章其实是多余的重构，没有可观察收益",
        2: "游戏在同样输入下会明显跑得更快，因为规则文件更靠近 CPU 缓存",
        3: "工程里的源文件总数被成功削减了，这才是这一章真正要交付的变化",
    },
    "snake.test.memory": {
        0: "把当年的 bug 截图永久存进版本库，后人对照像素就能认出同款故障",
        2: "在源码注释里详细记下 bug 的来龙去脉，让阅读代码的人自行警惕",
        3: "给 bug 编个号归档进项目文档目录，需要时再翻手册人工复现",
    },
    "snake.polish.sound": {
        0: "整段声音最长只允许持续两万两千个采样，超出就会被播放器直接截断",
        2: "音量被固定成两万两千分贝再除以一千，用来换算成库接受的线性增益",
        3: "播放器环形缓冲的字节数被钉死在这个常数，跟采样率完全无关",
    },
    "snake.input.verify": {
        0: "随手玩两分钟，没再看见折叠就算过，不必准备可重复的操作序列",
        2: "在源码里搜到 pending 字段就认定修好，不必上机观察蛇的轨迹",
        3: "把目标帧率调到一百二十再玩一轮，高帧率下折叠自然不会出现",
    },
    "snake.score.event": {
        0: "蛇每向前走完一格就加十分，与有没有吃到食物没有关系",
        2: "玩家每成功转向一次就加分，鼓励频繁变向而不是吃食物",
        3: "按墙上时钟每隔固定间隔加分，哪怕蛇停着不动也会涨分",
    },
    "snake.food.selfbite": {
        0: "前面几章作者临时把自吃判定漏掉了，变长之后才不得不补回来",
        2: "自吃判定必须先读到食物坐标才能编写，所以只能排在食物章之后",
        3: "第四章的输入缓冲其实已经挡住了自吃路径，不必再写显式判定",
    },
    # —— 修 BADLEN：加长过短干扰项（各写各的）；这两题仍保留正确项独占最长 ——
    "snake.score.const": {
        1: "snprintf 路径在性能上总是快过字符串拼接，所以必须先格式化再交给存盘",
        2: "SaveFileText 只吃已经格式化好的浮点文本，不认整数字面量或 const 指针",
        3: "先 snprintf 只是为了在文件末尾多垫一个换行，跟指针常量属性无关",
    },
    "snake.test.ctest": {
        0: "每次打开游戏窗口时会在后台自动跑一遍，玩家无感但结果写进日志",
        2: "必须手动双击测试可执行文件才能看见结果，构建系统不会代劳",
        3: "只有挂上调试器单步时测试才会被执行，否则二进制里根本不含断言",
    },
}

CHESS_DISTRACTOR_OVERRIDES: dict[str, dict[int, str]] = {
    # 保留 UL：builder / box / css / sensitive / owner —— 只把干扰项补到≤40% 差，仍短于正确项
    "chess.window.builder": {
        0: "编译 blp 时窗口会自己创建并弹出来，C++ 不必再写启动代码",
        2: "把 blp 里的控件再在 C++ 里 append 一遍才算数",
        3: "只要写好 style.css，进程启动后窗口就会出现",
    },
    "chess.layout.box": {
        1: "写在 style.css 的窗口最小宽度规则里，跟 blp 无关",
        2: "只能在 C++ 里 set_size_request，blp 排不了横盒",
        3: "由 Wood 涂色逻辑顺便决定，盒子本身不参与",
    },
    "chess.layout.css": {
        0: "写在每个 Label 构造时传入的内联属性里",
        3: "由 Wood 组件的木色自动传导到侧栏文字",
    },
    # 降 UL
    "chess.window.header": {
        0: "Application 的 id 字符串会被直接画在标题栏正中间当作标题",
        1: "窗口 title 属性本身就会画在标题栏正中，不必再挂 title-widget",
        3: "style.css 里用 content 属性写进去的文字会覆盖标题栏原有内容",
    },
    "chess.window.both": {
        0: "两份程序复用了完全相同的应用 id，所以第二次启动必然再开一扇",
        2: "blp 与 C++ 会在运行时自动合并成一个进程，单实例限制因此失效",
        3: "还没有棋盘，所以单实例限制暂时不生效，两扇窗口可以并存",
    },
    "chess.layout.slot": {
        0: "因为 Blueprint 语法不允许在窗口里放置任何盒子或占位控件，所以只能空着",
        2: "木色只能靠 CSS 背景图铺出来，控件树本身画不出可供挂载的棋盘区域",
        3: "这一章还没有侧栏，所以棋盘无处可挂，只能先空着那个 board_slot 占位",
    },

    "chess.board.cross": {
        0: "棋子落在格子中心，盘面一共划分成 9×8 个可站立的方格",
        2: "棋子落在河界那条空白带的几何中心，而不是交叉点网格上",
        3: "棋子落在侧栏预留的那 260 像素宽区域内，棋盘只负责画线",
    },
    "chess.board.shared": {
        0: "blp 里先画线，C++ 再把同样的线抄一份，两套描边叠在一起",
        2: "style.css 的 .side 规则会顺带描出九宫，不必共享 BoardView",
        3: "后一章的构建脚本会回写前一章的棋盘线，所以看起来像共享",
    },
    "chess.piece.center": {
        0: "画在格子中心，边长正好等于一格宽，交叉点只用来对齐线条",
        2: "画在侧栏列表里，棋盘上只保留线条，子力用文字列表表示",
        3: "叠在河界「楚河汉界」四个字的正上方，用来强调楚河分界",
    },
    "chess.move.rook": {
        0: "车和炮吃子都要求中间恰好隔着一个子，走法在这一点上完全对称",
        2: "车和炮吃子都要求中间一个子都没有，隔子就不能吃，只能平移",
        3: "炮根本不能吃子，只允许平移到空交叉点，隔子吃是后世规则引申",
    },
    "chess.move.block": {
        0: "马腿有子仍可跳，象眼有子才真正卡住；仕象过不过河另说",
        2: "象可以过河，前提只是象眼那一格是空的，九宫限制对它无效",
        3: "仕可以离开九宫，只要每一步都是斜线，河界对它也不构成障碍",
    },
    "chess.move.step": {
        0: "走到红方的一路，也就是坐标 x = 8，这里的「一」是路名不是步数",
        2: "吃掉了对方棋盘上某个「一」字标记的子，记谱习惯借了这个字",
        3: "帅平移到了黑方报路里的第 1 路，数字来自对方视角的编号",
    },
}

# C++ 手写表本身独占最长已在 20%~35%；这里只修个别过短干扰项，且不压过正确项。
CPP_DISTRACTOR_OVERRIDES: dict[str, dict[int, str]] = {
    "cpp.ValueSemantics.rvalue#0": {
        0: "一个普通的具名左值变量",
        2: "只有整型字面量 0 这一种实参",
        3: "任意带 const 限定的对象",
    },
}


def clone_items(items: list[dict]) -> list[dict]:
    return [
        {"id": it["id"], "choices": list(it["choices"]), "answer": it["answer"]}
        for it in items
    ]


def main() -> None:
    snake = clone_items(SNAKE)
    chess = clone_items(CHESS)
    cpp = clone_items(CPP)

    snake_orig = load_originals("snake")
    chess_orig = load_originals("chinese-chess")
    cpp_orig = load_originals("c-plus-plus")

    # 1) 合格原文整题覆盖（一字不动）
    apply_keep_verbatim(snake, snake_orig)
    apply_keep_verbatim(chess, chess_orig)
    apply_keep_verbatim(cpp, cpp_orig)

    # 2) 手写干扰项覆盖（等长 / 降独占最长 / 修 BADLEN）
    apply_distractor_overrides(snake, SNAKE_DISTRACTOR_OVERRIDES)
    apply_distractor_overrides(chess, CHESS_DISTRACTOR_OVERRIDES)
    apply_distractor_overrides(cpp, CPP_DISTRACTOR_OVERRIDES)

    # 3) 正确项必要措辞改写（去括号 / 缩短等）
    apply_correct_rewrites(snake)
    apply_correct_rewrites(chess)
    apply_correct_rewrites(cpp)

    # 4) 只洗牌位置
    snake = balance(snake, [11, 11, 11, 11])
    chess = balance(chess, [5, 5, 6, 5])
    cpp = balance(cpp, [5, 4, 5, 4])

    ul_s = sum(1 for r in snake if unique_longest(r["choices"], r["answer"]))
    ul_c = sum(1 for r in chess if unique_longest(r["choices"], r["answer"]))
    ul_p = sum(1 for r in cpp if unique_longest(r["choices"], r["answer"]))
    print(f"unique-longest: snake {ul_s}/44 chess {ul_c}/21 cpp {ul_p}/18")

    write("snake", snake)
    write("chinese-chess", chess)
    write("c-plus-plus", cpp)


if __name__ == "__main__":
    main()

