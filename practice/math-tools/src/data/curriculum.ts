/** 练习纲要数据:章节 → 练习项(要点 + 验收要求 + 工具标签)。 */

export type Tool = 'GeoGebra' | 'Octave' | 'Math Tools' | '理论'

export interface Exercise {
  /** 练习要点:练什么 */
  point: string
  /** 验收要求:做到什么程度算过 */
  req: string
  tools: Tool[]
}

export interface Chapter {
  id: string
  title: string
  en: string
  /** 本章目标:一句话说清这一章把什么变成你的手 */
  goal: string
  items: Exercise[]
}

export const chapters: Chapter[] = [
  {
    id: 'ch0',
    title: '工具就绪',
    en: 'Tools Ready',
    goal: '把三件兵器用顺:GeoGebra 负责拖,Octave 负责算,math-tools 负责改。',
    items: [
      {
        point: 'Octave 首次会话:算 exp(i·π),定义向量 v = 1:5,求 mean(v) 与 sum(v)。',
        req: '不查资料完成三步,并能说出分号省略分号在输出上的区别。',
        tools: ['Octave'],
      },
      {
        point: '在 Octave 里执行 plot(sin(linspace(0, 2·π, 100))) 画出正弦。',
        req: '能解释 linspace 三个参数各是什么,以及第三个参数改变时曲线有何变化。',
        tools: ['Octave'],
      },
      {
        point: 'GeoGebra 画 f(x)=x²,再建滑块 a,改成 a·x²。',
        req: '拖动滑块时图像实时变化;把文件保存为 .ggb 并能重新打开。',
        tools: ['GeoGebra'],
      },
      {
        point: 'math-tools 本地跑起来:npm install → npm run tauri:dev,改一处界面文字。',
        req: '在应用窗口里看到自己改的文字(热更生效)。',
        tools: ['Math Tools'],
      },
    ],
  },
  {
    id: 'ch1',
    title: '函数与图像',
    en: 'Functions & Graphs',
    goal: '看见函数——常用函数的形状与参数效应,要长在脑子里而不是公式表上。',
    items: [
      {
        point: '六类基本初等函数(幂、指数、对数、三角、反三角、双曲)各画一遍。',
        req: '合上资料徒手画出 sin(x)、ln(x)、eˣ、1/x 的形状并标出关键点与渐近线。',
        tools: ['GeoGebra', 'Octave'],
      },
      {
        point: '参数实验:y = A·sin(ωx + φ),建 A、ω、φ 三个滑块。',
        req: '先预测每个参数改变图像的什么,再拖动验证;预测错了要写出错在哪。',
        tools: ['GeoGebra'],
      },
      {
        point: '函数变换:f(x) 平移、伸缩、翻转、复合(如 f(x+1) − 2)。',
        req: '任给一个变换组合,先说出图像怎么动,再用本应用函数绘图验证。',
        tools: ['理论', 'Math Tools'],
      },
      {
        point: 'Octave subplot 一页画 2×2 四张图,配 title、legend、grid on。',
        req: '能不看示例独立写出版面命令,并说明 hold on 的作用。',
        tools: ['Octave'],
      },
    ],
  },
  {
    id: 'ch2',
    title: '矩阵实验室',
    en: 'Matrix Lab',
    goal: '矩阵 = 变换;行列式 = 面积缩放倍数;特征向量 = 变换下不变的方向。',
    items: [
      {
        point: '在矩阵实验室里对同一矩阵算转置、逆、行列式、秩,再用 Octave 的 transpose、inv、rref 验证。',
        req: '亲手构造一个不可逆矩阵,并用「变换压扁」解释行列式为什么是 0。',
        tools: ['Math Tools', 'Octave'],
      },
      {
        point: 'GeoGebra 里用 ApplyMatrix({{2,1},{1,3}}, 多边形) 对一个四边形做变换。',
        req: '能解释 det 为什么等于图形面积放大的倍数(数一数格子验证)。',
        tools: ['GeoGebra'],
      },
      {
        point: '2×2 特征值:手算 [2,1;1,3] 的特征多项式与特征值。',
        req: '手算结果 2±√5 与软件输出(1.38197…,3.61803…)对上,误差说明来源。',
        tools: ['理论', 'Math Tools', 'Octave'],
      },
      {
        point: '特征向量方向:GeoGebra 里画向量 v 与 Av,拖动 v 转一圈。',
        req: '记下 Av 与 v 共线时 v 的方向,并说明它们正是特征向量方向。',
        tools: ['GeoGebra'],
      },
    ],
  },
  {
    id: 'ch3',
    title: '导数与极限',
    en: 'Derivatives & Limits',
    goal: '导数不是求导公式,是割线的极限;泰勒展开是多项式对函数的逼近。',
    items: [
      {
        point: '数值极限实验:Octave 里算 (1 + 1/n)^n,n 取 10、100、10⁴、10⁶、10¹⁵。',
        req: '列表观察逼近 e;能解释 n 过大后结果为什么反而离开 e(浮点舍入)。',
        tools: ['Octave'],
      },
      {
        point: '割线逼近切线:GeoGebra 画 f(x)=x³,定点 x=1,滑块 h 控制割线第二点。',
        req: '拖 h→0 演示割线变切线,并复述导数定义中每一步的几何含义。',
        tools: ['GeoGebra'],
      },
      {
        point: 'f 与 f′ 同图:本应用绘图里先后画 x³−3x 与 3x²−3。',
        req: '从 f 的图像指出极大/极小点位置,与 f′ 的零点一一对应并解释原因。',
        tools: ['Math Tools'],
      },
      {
        point: '泰勒实验:画 sin(x) 与它的 1、3、5、7 阶泰勒多项式。',
        req: '能说出「阶数每加二,可靠区间大致延伸多少」的现象,并解释 sin 的偶数阶为何与上一阶相同。',
        tools: ['GeoGebra', 'Octave'],
      },
    ],
  },
  {
    id: 'ch4',
    title: '积分与数值积分',
    en: 'Integration Numerically',
    goal: '积分 = 求和的极限;数值积分 = 聪明的求和,误差阶是它们的段位。',
    items: [
      {
        point: 'Octave 自写左端点黎曼和函数,算 ∫₀¹ x² dx。',
        req: '给出 n = 10、100、1000 三档误差表,并验证误差比约为 100(误差 O(1/n))。',
        tools: ['Octave'],
      },
      {
        point: 'GeoGebra 黎曼和:n 从 4 拖到 100,看矩形和填满曲边梯形。',
        req: '能说出上和与下和夹住的区间如何随 n 收缩到积分值。',
        tools: ['GeoGebra'],
      },
      {
        point: '梯形法:用 trapz 与自写梯形法各算一遍同一积分。',
        req: '对比误差,解释梯形法为什么是 O(h²) 而矩形法是 O(h)。',
        tools: ['Octave'],
      },
      {
        point: '微积分基本定理数值验证:F(b) − F(a) 对比数值积分。',
        req: '三组不同被积函数验证误差小于 1e−6,并指出误差的主要来源。',
        tools: ['Octave', 'Math Tools'],
      },
    ],
  },
  {
    id: 'ch5',
    title: '微分方程与迭代',
    en: 'ODE & Iteration',
    goal: '现实中大多数方程没有解析解——数值解是工程师的母语。',
    items: [
      {
        point: '自写 Euler 法(约 20 行)解 y′ = y,y(0)=1。',
        req: '与解析解 eˣ 比较;步长减半时误差大约减半,列表验证。',
        tools: ['Octave'],
      },
      {
        point: '用 ode45 解 y′ = −y + sin(t),画出解曲线。',
        req: '改变初值 y(0),观察解如何被吸引到同一条稳态曲线上,并解释为什么。',
        tools: ['Octave'],
      },
      {
        point: '迭代可视化:xₙ₊₁ = cos(xₙ),在 GeoGebra 里画 y=x 与 y=cos(x) 做蛛网图。',
        req: '能解释迭代为什么收敛到不动点(斜率绝对值小于 1),并用 Octave 迭代验证极限值。',
        tools: ['GeoGebra', 'Octave'],
      },
    ],
  },
  {
    id: 'ch6',
    title: '综合实践',
    en: 'Capstone',
    goal: '用一次完整的「数据 → 模型 → 图」证明:这些工具已经变成你的手。',
    items: [
      {
        point: '三选一交付:(a) 找一组真实数据(如城市气温),Octave 二次拟合并评价残差;(b) 用 GeoGebra 做一个可用于教学的交互演示(泰勒逼近或矩阵变换);(c) 给 math-tools 新增一个由本纲要催生的工具(高斯消元分步展示、参数曲线动画、数值极限观察器……)。',
        req: '成果可复现,并能向别人讲 10 分钟:数据从哪来、每步为什么这样做、结果说明了什么。',
        tools: ['GeoGebra', 'Octave', 'Math Tools'],
      },
    ],
  },
]
