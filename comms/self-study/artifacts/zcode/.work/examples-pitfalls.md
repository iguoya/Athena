===== ch1-sec2 =====

[SRC] advmath.ret.0102: [{'relation': 'authored', 'note': '预测题：先猜向量模的公式，不判掌握度，如实标自造'}]

[PITFALL] 错: $|\boldsymbol a+\boldsymbol b|=|\boldsymbol a|+|\boldsymbol b|$。
  为何错: 和向量的模一般**小于**两个模之和（三角形两边之和大于第三边）。例：$\boldsymbol a=(1,0,0),\ \boldsymbol b=(0,1,0)$，$|\boldsymbol a+\boldsymbol b|=\sqrt2\approx1.41$，而 $|\boldsymbol a|+|\boldsymbol b|=2$。只有 $\boldsymbol a,\boldsymbol b$ **同向**时等号才成立。
  对: $|\boldsymbol a+\boldsymbol b|\le|\boldsymbol a|+|\boldsymbol b|$（三角不等式）。求和向量的模，要先按分量相加，再求模。

[EXAMPLE] 例 1（由两点求向量、模、方向余弦）
问题: 已知 $A(1,2,3)$，$B(4,6,3)$，求 $\overrightarrow{AB}$、$|\overrightarrow{AB}|$ 及同方向的单位向量。
  步1: {'text': '$\\overrightarrow{AB}=(4-1,\\ 6-2,\\ 3-3)=(3,4,0)$。', 'why': '终点减起点；$z$ 分量为 0 说明 $AB$ 平行于 $xOy$ 平面。'}
  步2: {'text': '$|\\overrightarrow{AB}|=\\sqrt{3^2+4^2+0^2}=5$。', 'why': '与预测题同一组数。'}
  步3: {'text': '单位向量 $\\overrightarrow{AB}^0=\\left(\\dfrac35,\\dfrac45,0\\right)$，即方向余弦 $\\cos\\alpha=\\frac35,\\ \\cos\\beta=\\frac45,\\ \\cos\\gamma=0$（$\\gamma=90^\\circ$）。', 'why': '检验：$\\frac9{25}+\\frac{16}{25}+0=1$。'}
  source: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[EXAMPLE] 例 2（向量的线性运算与方向余弦）
问题: 设 $\boldsymbol a=(1,2,3),\ \boldsymbol b=(-2,1,0)$，求 $2\boldsymbol a-3\boldsymbol b$；再求 $\boldsymbol c=(2,-1,2)$ 的方向余弦。
  步1: {'text': '$2\\boldsymbol a-3\\boldsymbol b=(2+6,\\ 4-3,\\ 6-0)=(8,1,6)$。', 'why': '数乘每个分量；减去 $3\\boldsymbol b$ 即减去 $(-6,3,0)$，第一个分量 $2-(-6)=8$。'}
  步2: {'text': '$|\\boldsymbol c|=\\sqrt{4+1+4}=3$，方向余弦 $\\left(\\dfrac23,-\\dfrac13,\\dfrac23\\right)$。', 'why': '检验：$\\frac49+\\frac19+\\frac49=1$。$\\beta$ 是钝角，因为 $\\cos\\beta<0$。'}
  source: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0102a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0102b: [{'relation': 'authored', 'note': '自造数值，已复算（与例 2 同题，只问一个分量）'}]

[SRC] advmath.ex.0102c: [{'relation': 'authored', 'note': '自造数值：用分量成比例判断平行'}]

[SRC] advmath.ex.0102d: [{'relation': 'authored', 'note': '自造辨析题：方向余弦的平方和'}]

[SRC] advmath.ex.0102e: [{'relation': 'authored', 'note': '自造；投影与坐标分量的关系'}]
===== ch1-sec3 =====

[SRC] advmath.ret.0103: [{'relation': 'authored', 'note': '预测题：先猜数量积为零的含义，不判掌握度，如实标自造'}]

[PITFALL] 错: $\boldsymbol a\cdot\boldsymbol b=0$，所以 $\boldsymbol a=\boldsymbol0$ 或 $\boldsymbol b=\boldsymbol0$。
  为何错: 数量积为 0 的另一种可能是两个向量**垂直**。例：$\boldsymbol a=(1,0,0),\ \boldsymbol b=(0,1,0)$，$\boldsymbol a\cdot\boldsymbol b=0$，两个向量都不是零向量。
  对: $\boldsymbol a\cdot\boldsymbol b=0\iff\boldsymbol a=\boldsymbol0$ 或 $\boldsymbol b=\boldsymbol0$ 或 $\boldsymbol a\perp\boldsymbol b$。两个非零向量，数量积为 0 就是垂直。

[EXAMPLE] 例 1（夹角与投影）
问题: 设 $\boldsymbol a=(1,2,3),\ \boldsymbol b=(2,-1,2)$，求 $\boldsymbol a\cdot\boldsymbol b$、夹角余弦、以及 $\boldsymbol a$ 在 $\boldsymbol b$ 上的投影。
  步1: {'text': '$\\boldsymbol a\\cdot\\boldsymbol b=1\\cdot2+2\\cdot(-1)+3\\cdot2=6$。', 'why': '对应分量相乘再相加。'}
  步2: {'text': '$|\\boldsymbol a|=\\sqrt{14},\\ |\\boldsymbol b|=3$，$\\cos\\theta=\\dfrac{6}{3\\sqrt{14}}=\\dfrac{2}{\\sqrt{14}}=\\dfrac{\\sqrt{14}}7$。', 'why': '$\\cos\\theta>0$，夹角为锐角。'}
  步3: {'text': '$\\operatorname{Prj}_{\\boldsymbol b}\\boldsymbol a=\\dfrac{\\boldsymbol a\\cdot\\boldsymbol b}{|\\boldsymbol b|}=\\dfrac63=2$。', 'why': '投影是数。除以的是 $|\\boldsymbol b|$ 而不是 $|\\boldsymbol a|$。'}
  source: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[EXAMPLE] 例 2（向量积与法向量）
问题: 求同时垂直于 $\boldsymbol a=(1,2,3)$ 和 $\boldsymbol b=(2,-1,2)$ 的向量。
  步1: {'text': '$\\boldsymbol a\\times\\boldsymbol b=\\begin{vmatrix}\\boldsymbol i&\\boldsymbol j&\\boldsymbol k\\\\1&2&3\\\\2&-1&2\\end{vmatrix}=(2\\cdot2-3\\cdot(-1),\\ 3\\cdot2-1\\cdot2,\\ 1\\cdot(-1)-2\\cdot2)=(7,4,-5)$。', 'why': '按第 1 行展开，$\\boldsymbol j$ 的系数带负号：$-(1\\cdot2-3\\cdot2)=4$，与公式 $z_1x_2-x_1z_2=6-2$ 一致。'}
  步2: {'text': '检验：$(7,4,-5)\\cdot(1,2,3)=7+8-15=0$，$(7,4,-5)\\cdot(2,-1,2)=14-4-10=0$。', 'why': '叉乘结果必须与两个因子都垂直，用数量积一验就知道有没有算错。'}
  source: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[EXAMPLE] 例 3（用向量积求三角形面积）
问题: 求以 $A(1,0,0),\ B(0,2,0),\ C(0,0,3)$ 为顶点的三角形面积。
  步1: {'text': '$\\overrightarrow{AB}=(-1,2,0),\\ \\overrightarrow{AC}=(-1,0,3)$。', 'why': '取两条从 $A$ 出发的边。'}
  步2: {'text': '$\\overrightarrow{AB}\\times\\overrightarrow{AC}=(2\\cdot3-0\\cdot0,\\ 0\\cdot(-1)-(-1)\\cdot3,\\ (-1)\\cdot0-2\\cdot(-1))=(6,3,2)$，模 $\\sqrt{36+9+4}=7$。', 'why': '$(6,3,2)$ 也是这个三角形所在平面的法向量（§5 例 1 会用到）。'}
  步3: {'text': '面积 $S=\\dfrac12\\times7=\\dfrac72$。', 'why': '三角形面积是平行四边形的一半。'}
  source: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0103a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0103b: [{'relation': 'authored', 'note': '自造数值：用数量积为 0 判断垂直'}]

[SRC] advmath.ex.0103c: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0103d: [{'relation': 'authored', 'note': '自造辨析题：向量积的性质'}]
===== ch1-sec4 =====

[SRC] advmath.ret.0104: [{'relation': 'authored', 'note': '预测题：先猜缺一个变量的方程的含义，不判掌握度，如实标自造'}]

[PITFALL] 错: 空间中 $x^2+y^2=4$ 表示一个圆。
  为何错: 在平面 $xOy$ 里才是圆。空间里它缺 $z$，$z$ 可以取任意值，图形是圆柱面。一条**空间曲线**需要**两个**方程：圆写成 $\begin{cases}x^2+y^2=4\\z=0\end{cases}$。
  对: 一个方程对应一张**曲面**，两个方程联立才是**曲线**。看方程时先问：在哪个空间里？

[EXAMPLE] 例 1（配方求球心与半径）
问题: 方程 $x^2+y^2+z^2-2x+4y-6z=11$ 表示什么曲面？
  步1: {'text': '按 $x,y,z$ 分别配方：$(x-1)^2+(y+2)^2+(z-3)^2=11+1+4+9=25$。', 'why': '$x^2-2x$ 补 $1$，$y^2+4y$ 补 $4$，$z^2-6z$ 补 $9$，右边同时加上。'}
  步2: {'text': '这是球心 $(1,-2,3)$、半径 $5$ 的球面。', 'why': '标准式右边是 $R^2=25$，所以 $R=5$，而不是 25。'}
  source: [{'relation': 'authored', 'note': '自造数值，配方已复算'}]

[EXAMPLE] 例 2（旋转曲面）
问题: $yOz$ 面上的抛物线 $z=y^2$（$x=0$）绕 $z$ 轴旋转，求旋转曲面的方程。
  步1: {'text': '绕 $z$ 轴旋转，$z$ 不变，$y$ 换成 $\\pm\\sqrt{x^2+y^2}$：$z=\\left(\\pm\\sqrt{x^2+y^2}\\right)^2=x^2+y^2$。', 'why': '曲面上任一点到 $z$ 轴的距离是 $\\sqrt{x^2+y^2}$，它在原来曲线上对应的是 $|y|$。'}
  步2: {'text': '旋转曲面方程 $z=x^2+y^2$（旋转抛物面）。', 'why': '同样的方法，$yOz$ 面上的直线 $z=y$ 绕 $z$ 轴旋转得 $z^2=x^2+y^2$（圆锥面）。'}
  source: [{'relation': 'authored', 'note': '自造；旋转曲面的标准算法'}]

[EXAMPLE] 例 3（空间曲线在坐标面上的投影）
问题: 求曲线 $\begin{cases}x^2+y^2+z^2=1\\x+z=1\end{cases}$ 在 $xOy$ 面上的投影曲线方程。
  步1: {'text': '由第二式 $z=1-x$，代入第一式消去 $z$：$x^2+y^2+(1-x)^2=1$，整理得 $2x^2-2x+y^2=0$。', 'why': '这是投影柱面方程，母线平行于 $z$ 轴。'}
  步2: {'text': '投影曲线 $\\begin{cases}2x^2-2x+y^2=0\\\\z=0\\end{cases}$。', 'why': '柱面与 $xOy$ 面（$z=0$）的交线。别漏掉 $z=0$，否则只是柱面。'}
  source: [{'relation': 'authored', 'note': '自造；消元法求投影曲线，展开已复算'}]

[SRC] advmath.ex.0104a: [{'relation': 'authored', 'note': '自造数值，配方已复算'}]

[SRC] advmath.ex.0104b: [{'relation': 'authored', 'note': '自造辨析题：绕哪个轴，哪个变量不动'}]

[SRC] advmath.ex.0104c: [{'relation': 'authored', 'note': '自造辨析题：投影曲线 = 投影柱面 + 坐标面'}]
===== ch1-sec5 =====

[SRC] advmath.ret.0105: [{'relation': 'authored', 'note': '预测题：先猜确定平面的条件，不判掌握度，如实标自造'}]

[PITFALL] 错: 直线与平面平行，所以直线的方向向量 $\boldsymbol s$ 与平面的法向量 $\boldsymbol n$ 平行。
  为何错: 弄反了。$\boldsymbol n$ 垂直于平面；直线**平行于平面**时，$\boldsymbol s$ 与平面内的方向一致，所以 $\boldsymbol s\perp\boldsymbol n$。$\boldsymbol s\parallel\boldsymbol n$ 说明直线**垂直于**平面。
  对: 线面**平行**：$\boldsymbol s\cdot\boldsymbol n=0$；线面**垂直**：$\boldsymbol s\parallel\boldsymbol n$。面面平行才是 $\boldsymbol n_1\parallel\boldsymbol n_2$。

[EXAMPLE] 例 1（三点定平面，截距式）
问题: 求过 $A(1,0,0),\ B(0,2,0),\ C(0,0,3)$ 的平面方程。
  步1: {'text': '三个点正好落在三条坐标轴上，截距 $a=1,\\ b=2,\\ c=3$：$\\dfrac x1+\\dfrac y2+\\dfrac z3=1$。', 'why': '截距式直接可用。'}
  步2: {'text': '两边乘 6：$6x+3y+2z=6$。法向量 $(6,3,2)$。', 'why': '与 §3 例 3 用 $\\overrightarrow{AB}\\times\\overrightarrow{AC}=(6,3,2)$ 算出的法向量一致。'}
  source: [{'relation': 'authored', 'note': '自造数值，截距与法向量已复算'}]

[EXAMPLE] 例 2（过点垂直于平面的直线）
问题: 求过点 $(1,2,3)$ 且垂直于平面 $2x-y+z=5$ 的直线方程。
  步1: {'text': '直线垂直于平面，方向向量取平面的法向量：$\\boldsymbol s=(2,-1,1)$。', 'why': '线面垂直 $\\iff\\boldsymbol s\\parallel\\boldsymbol n$。'}
  步2: {'text': '对称式 $\\dfrac{x-1}{2}=\\dfrac{y-2}{-1}=\\dfrac{z-3}{1}$；参数式 $x=1+2t,\\ y=2-t,\\ z=3+t$。', 'why': '分母中的 $-1$ 是允许的，不要去掉负号。'}
  source: [{'relation': 'authored', 'note': '自造；法向量作方向向量'}]

[EXAMPLE] 例 3（直线与平面的交点）
问题: 求直线 $x=1+t,\ y=2-t,\ z=3+2t$ 与平面 $x+y+z=10$ 的交点。
  步1: {'text': '把参数式代入平面方程：$(1+t)+(2-t)+(3+2t)=6+2t=10$，$t=2$。', 'why': '交点在直线上（满足参数式）也在平面上（满足方程），所以参数 $t$ 要满足代入后的方程。'}
  步2: {'text': '$t=2$ 代回：交点 $(3,0,7)$。', 'why': '检验：$3+0+7=10$。'}
  source: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0105a: [{'relation': 'authored', 'note': '自造辨析题：点法式展开'}]

[SRC] advmath.ex.0105b: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0105c: [{'relation': 'authored', 'note': '自造数值，已复算（与例 3 同题，只问一个坐标）'}]

[SRC] advmath.ex.0105d: [{'relation': 'authored', 'note': '自造数值，叉乘已复算'}]

[SRC] advmath.ex.0105e: [{'relation': 'authored', 'note': '自造数值，已复算'}]
===== ch1-sec6 =====

[SRC] advmath.ret.0106: [{'relation': 'authored', 'note': '预测题：先猜截痕形状，不判掌握度，如实标自造'}]

[PITFALL] 错: $x^2+y^2-z^2=1$ 和 $x^2+y^2-z^2=-1$ 是同一类曲面，都叫双曲面，形状一样。
  为何错: 右边常数的符号决定了形状。$x^2+y^2-z^2=1$ 用 $z=h$ 去截得到 $x^2+y^2=1+h^2$，**每个 $h$** 都有圆，曲面连成一片（单叶）。$x^2+y^2-z^2=-1$ 得到 $x^2+y^2=h^2-1$，只有 $|h|\ge1$ 才有截痕，$|h|<1$ 时无交点，曲面分成上下两叶（双叶）。
  对: 两正一负的二次曲面：右边 $+1$ 是单叶，$-1$ 是双叶，$0$ 是锥面。

[EXAMPLE] 例 1（识别曲面类型）
问题: 指出 (1) $\dfrac{x^2}{4}+\dfrac{y^2}{9}-\dfrac{z^2}{16}=1$；(2) $4x^2+y^2+z^2=4$；(3) $z=x^2+y^2$ 各是什么曲面。
  步1: {'text': '(1) 两正一负、右边 $+1$：**单叶双曲面**。', 'why': '右边是 +1，不是 −1。'}
  步2: {'text': '(2) 两边除以 4：$x^2+\\dfrac{y^2}{4}+\\dfrac{z^2}{4}=1$，三个平方项都为正，右边 1：**椭球面**（$y,z$ 方向半轴都是 2，所以是绕 $x$ 轴的旋转椭球面）。', 'why': '系数不是 1 时先化成标准形，再看半轴。'}
  步3: {'text': '(3) $z$ 是一次的，$x^2,y^2$ 同号：**椭圆抛物面**（这里 $a=b=1$，是旋转抛物面，§4 例 2）。', 'why': '一次变量决定抛物面的轴。'}
  source: [{'relation': 'authored', 'note': '自造；二次曲面的类型辨识'}]

[EXAMPLE] 例 2（截痕法）
问题: 用平面 $z=h$ 与 $y=0$ 分别截单叶双曲面 $x^2+y^2-z^2=1$，各得什么截痕？
  步1: {'text': '$z=h$：$x^2+y^2=1+h^2$，圆，半径 $\\sqrt{1+h^2}\\ge1$，$h=0$ 时最小（「腰」）。', 'why': '$1+h^2$ 恒为正，所以每个 $h$ 都有截痕，曲面连成一片。'}
  步2: {'text': '$y=0$：$x^2-z^2=1$，$xOz$ 面上的双曲线。', 'why': '沿坐标面的截痕给出曲面的轮廓，这也是它名字里「双曲」的来源。'}
  source: [{'relation': 'authored', 'note': '自造；截痕法'}]

[SRC] advmath.ex.0106a: [{'relation': 'authored', 'note': '自造辨析题：右边常数的符号'}]

[SRC] advmath.ex.0106b: [{'relation': 'authored', 'note': '自造辨析题：四个相似的方程'}]

[SRC] advmath.ex.0106c: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0106d: [{'relation': 'authored', 'note': '自造数值，已复算'}]
===== ch2-sec1 =====

[SRC] advmath.ret.0201: [{'relation': 'authored', 'note': '预测题：先猜二元函数定义域的形状，不判掌握度，如实标自造'}]

[PITFALL] 错: 沿每一条直线 $y=kx$ 趋近原点时，$f$ 的极限都存在且相等，所以二重极限存在。
  为何错: 二重极限要求**任何方式**趋近都一样，直线只是其中一族。例：$f(x,y)=\dfrac{x^2y}{x^4+y^2}$。沿 $y=kx$：$\dfrac{kx^3}{x^4+k^2x^2}=\dfrac{kx}{x^2+k^2}\to0$（对所有 $k$）；但沿抛物线 $y=x^2$：$\dfrac{x^4}{x^4+x^4}=\dfrac12$。两条路径极限不同，二重极限**不存在**。
  对: 证明极限**存在**要对一切路径都成立（用夹逼、替换）；证明**不存在**只需找出两条结果不同的路径。

[EXAMPLE] 例 1（求定义域）
问题: 求 $z=\dfrac{\ln(x+y)}{\sqrt{x-y}}$ 的定义域。
  步1: {'text': '对数要求 $x+y>0$；根号在分母，要求 $x-y>0$（根号下非负，且分母不为零）。', 'why': '两个条件同时成立。'}
  步2: {'text': '即 $y>-x$ 且 $y<x$，也就是 $x>|y|$。图形是以原点为顶点、开口向右、夹在直线 $y=x$ 与 $y=-x$ 之间的开区域（不含边界直线）。', 'why': '两条边界直线都取不到，所以是开区域。'}
  source: [{'relation': 'authored', 'note': '自造；定义域的标准写法'}]

[EXAMPLE] 例 2（极限存在与不存在）
问题: 讨论 (1) $\displaystyle\lim_{(x,y)\to(0,0)}\frac{x^2-y^2}{x^2+y^2}$；(2) $\displaystyle\lim_{(x,y)\to(0,0)}\frac{\sin(x^2+y^2)}{x^2+y^2}$ 是否存在。
  步1: {'text': '(1) 沿 $y=kx$：$\\dfrac{x^2-k^2x^2}{x^2+k^2x^2}=\\dfrac{1-k^2}{1+k^2}$，随 $k$ 变化（$k=0$ 得 1，$k=1$ 得 0）。极限**不存在**。', 'why': '沿不同直线趋近，值不同。'}
  步2: {'text': '(2) 令 $u=x^2+y^2\\to0$，原式 $=\\dfrac{\\sin u}{u}\\to1$。极限**存在**，等于 1。', 'why': '不管点怎样趋近原点，$u=x^2+y^2$ 总趋于 0，所以化成一元的重要极限。'}
  source: [{'relation': 'authored', 'note': '自造；极限的两类典型'}]

[SRC] advmath.ex.0201a: [{'relation': 'authored', 'note': '自造辨析题：对数的真数必须大于 0'}]

[SRC] advmath.ex.0201b: [{'relation': 'authored', 'note': '自造；化为一元重要极限'}]

[SRC] advmath.ex.0201c: [{'relation': 'authored', 'note': '自造辨析题：路径法'}]

[SRC] advmath.ex.0201d: [{'relation': 'authored', 'note': '自造辨析题：连续的定义'}]
===== ch2-sec2 =====

[SRC] advmath.ret.0202: [{'relation': 'authored', 'note': '预测题：先猜偏导数中其余变量的处理，不判掌握度，如实标自造'}]

[PITFALL] 错: 函数在某点的两个偏导数都存在，所以它在该点连续（可微）。
  为何错: 偏导数只描述沿两个坐标方向的变化，不保证沿其他方向也好。例：$f(x,y)=\dfrac{xy}{x^2+y^2}$（$f(0,0)=0$），在原点 $f_x(0,0)=\lim\dfrac{f(\Delta x,0)-0}{\Delta x}=0$，$f_y(0,0)=0$，两个偏导数都存在，但 $f$ 在原点**不连续**（上节），更不可微。
  对: 偏导数存在**推不出**连续。需要的是「偏导数在该点**连续**」这个更强的条件，才能推出可微。

[EXAMPLE] 例 1（求一阶偏导数）
问题: 求 $z=x^2y+\mathrm e^{xy}$ 的 $\dfrac{\partial z}{\partial x},\ \dfrac{\partial z}{\partial y}$。
  步1: {'text': '对 $x$ 求偏导（$y$ 视为常数）：$\\dfrac{\\partial z}{\\partial x}=2xy+y\\,\\mathrm e^{xy}$。', 'why': "$(\\mathrm e^{xy})'_x=\\mathrm e^{xy}\\cdot y$，复合函数求导，内层 $xy$ 对 $x$ 求导得 $y$。"}
  步2: {'text': '对 $y$ 求偏导（$x$ 视为常数）：$\\dfrac{\\partial z}{\\partial y}=x^2+x\\,\\mathrm e^{xy}$。', 'why': '$x^2y$ 对 $y$ 是常数 $x^2$ 乘 $y$，导数 $x^2$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 2（二阶偏导数）
问题: 求 $z=x^3y^2-3xy+y$ 的 $z_{xx},\ z_{xy},\ z_{yx}$。
  步1: {'text': '$z_x=3x^2y^2-3y$，$z_y=2x^3y-3x+1$。', 'why': '先求一阶，再继续求导。'}
  步2: {'text': '$z_{xx}=6xy^2$；$z_{xy}=(z_x)_y=6x^2y-3$；$z_{yx}=(z_y)_x=6x^2y-3$。', 'why': '两个混合偏导数相等（它们连续）；验算时用这一点互相检验。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 3（全微分与近似）
问题: 求 $z=x^2y^3$ 在点 $(1,2)$ 的全微分，并用它估计 $x$ 由 1 增加到 1.01、$y$ 由 2 增加到 2.02 时 $z$ 的改变量。
  步1: {'text': '$z_x=2xy^3,\\ z_y=3x^2y^2$，在 $(1,2)$：$z_x=16,\\ z_y=12$。所以 $\\mathrm dz=16\\,\\mathrm dx+12\\,\\mathrm dy$。', 'why': '偏导数的值代入点的坐标。'}
  步2: {'text': '$\\mathrm dx=0.01,\\ \\mathrm dy=0.02$：$\\mathrm dz=16\\times0.01+12\\times0.02=0.16+0.24=0.40$。', 'why': '精确值 $1.01^2\\cdot2.02^3-1^2\\cdot2^3\\approx0.408$，近似值 0.40 很接近。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[SRC] advmath.ex.0202a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0202b: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0202c: [{'relation': 'authored', 'note': '自造数值，已复算（与例 3 同题）'}]

[SRC] advmath.ex.0202d: [{'relation': 'authored', 'note': '自造辨析题：连续、偏导数、可微的关系'}]
===== ch2-sec3 =====

[SRC] advmath.ret.0203: [{'relation': 'authored', 'note': '预测题：先猜链式法则的项数，不判掌握度，如实标自造'}]

[PITFALL] 错: 由 $F(x,y,z)=0$ 确定的隐函数，$\dfrac{\partial z}{\partial x}=\dfrac{F_x}{F_z}$。
  为何错: 漏了负号。验证：$x+y+z=0$ 即 $z=-x-y$，直接求导 $\dfrac{\partial z}{\partial x}=-1$。公式里 $F=x+y+z,\ F_x=1,\ F_z=1$，$F_x/F_z=1$，符号反了；$-F_x/F_z=-1$ 才对。
  对: $\dfrac{\partial z}{\partial x}=-\dfrac{F_x}{F_z}$。负号来自对 $F(x,y,z(x,y))=0$ 两边求导：$F_x+F_z\cdot z_x=0$。

[EXAMPLE] 例 1（两个中间变量）
问题: 设 $z=\mathrm e^u\sin v$，$u=xy$，$v=x+y$，求 $\dfrac{\partial z}{\partial x}$。
  步1: {'text': '$\\dfrac{\\partial z}{\\partial u}=\\mathrm e^u\\sin v,\\ \\dfrac{\\partial z}{\\partial v}=\\mathrm e^u\\cos v$；$\\dfrac{\\partial u}{\\partial x}=y,\\ \\dfrac{\\partial v}{\\partial x}=1$。', 'why': '先把四个基本的偏导数各自求出来。'}
  步2: {'text': '$\\dfrac{\\partial z}{\\partial x}=\\mathrm e^u\\sin v\\cdot y+\\mathrm e^u\\cos v\\cdot1=\\mathrm e^{xy}\\left[y\\sin(x+y)+\\cos(x+y)\\right]$。', 'why': '最后把 $u,v$ 换回 $x,y$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 2（全导数）
问题: 设 $z=u^2+v$，$u=\sin t$，$v=\cos t$，求 $\dfrac{\mathrm dz}{\mathrm dt}$。
  步1: {'text': '$\\dfrac{\\mathrm dz}{\\mathrm dt}=2u\\cdot\\cos t+1\\cdot(-\\sin t)=2\\sin t\\cos t-\\sin t$。', 'why': "$\\partial z/\\partial u=2u,\\ \\partial z/\\partial v=1$；$u'=\\cos t,\\ v'=-\\sin t$。"}
  步2: {'text': '验证：先代入 $z=\\sin^2t+\\cos t$，直接求导得 $2\\sin t\\cos t-\\sin t$，一致。', 'why': '能直接代入时用来自查。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 3（隐函数求导）
问题: (1) 由 $\mathrm e^y+xy=\mathrm e$ 确定 $y=y(x)$，求 $\dfrac{\mathrm dy}{\mathrm dx}\Big|_{x=0}$（此时 $y=1$）；(2) 由 $x^2+y^2+z^2=14$ 确定 $z=z(x,y)$，写出 $\dfrac{\partial z}{\partial x}$。
  步1: {'text': '(1) $F=\\mathrm e^y+xy-\\mathrm e$，$F_x=y,\\ F_y=\\mathrm e^y+x$。$\\dfrac{\\mathrm dy}{\\mathrm dx}=-\\dfrac{y}{\\mathrm e^y+x}$，在 $(0,1)$：$-\\dfrac1{\\mathrm e}$。', 'why': '代入点 $x=0,y=1$。'}
  步2: {'text': '(2) $F=x^2+y^2+z^2-14$，$F_x=2x,\\ F_z=2z$，$\\dfrac{\\partial z}{\\partial x}=-\\dfrac{x}{z}$。', 'why': '检验：球面上半部分 $z=\\sqrt{14-x^2-y^2}$，直接求导 $z_x=-x/\\sqrt{14-x^2-y^2}=-x/z$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[SRC] advmath.ex.0203a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0203b: [{'relation': 'authored', 'note': '自造辨析题：隐函数公式的负号'}]

[SRC] advmath.ex.0203c: [{'relation': 'authored', 'note': '自造数值，已复算'}]
===== ch2-sec4 =====

[SRC] advmath.ret.0204: [{'relation': 'authored', 'note': '预测题：先猜驻点的类型，不判掌握度，如实标自造'}]

[PITFALL] 错: 驻点一定是极值点。
  为何错: 驻点只是极值的**必要**条件。$z=xy$：$z_x=y,\ z_y=x$，驻点 $(0,0)$；$A=z_{xx}=0,\ B=z_{xy}=1,\ C=z_{yy}=0$，$\Delta=AC-B^2=-1<0$，所以不是极值点（在原点附近既有 $z>0$ 又有 $z<0$）。
  对: 求出驻点后必须用 $\Delta=AC-B^2$ 判别；$\Delta<0$ 的驻点不是极值点。

[EXAMPLE] 例 1（无条件极值）
问题: 求 $f(x,y)=x^3-3x+y^2$ 的极值。
  步1: {'text': '$f_x=3x^2-3=0\\Rightarrow x=\\pm1$；$f_y=2y=0\\Rightarrow y=0$。驻点 $(1,0),\\ (-1,0)$。', 'why': '两个偏导数同时为 0，解联立方程。'}
  步2: {'text': '二阶偏导数：$A=f_{xx}=6x,\\ B=f_{xy}=0,\\ C=f_{yy}=2$。', 'why': '在每个驻点分别代入。'}
  步3: {'text': '$(1,0)$：$A=6>0,\\ \\Delta=6\\cdot2-0=12>0$，**极小值** $f(1,0)=1-3=-2$。$(-1,0)$：$\\Delta=(-6)\\cdot2=-12<0$，**不是极值点**。', 'why': '两个驻点结论不同，要分别判断。'}
  source: [{'relation': 'authored', 'note': '自造，驻点与极值已复算'}]

[EXAMPLE] 例 2（拉格朗日乘数法）
问题: 在直线 $x+y=2$ 上求 $f=xy$ 的最大值。
  步1: {'text': '$L=xy+\\lambda(x+y-2)$。$L_x=y+\\lambda=0,\\ L_y=x+\\lambda=0,\\ x+y=2$。', 'why': '把约束写成 $\\varphi=x+y-2=0$。'}
  步2: {'text': '由前两式 $x=y=-\\lambda$，代入第三式 $x=y=1$，$f=1$。这是唯一的可能极值点；由 $xy\\le\\left(\\frac{x+y}{2}\\right)^2=1$ 知它是**最大值** 1。', 'why': '拉格朗日法给出候选点，是不是最大还要结合问题本身判断。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 3（切平面与法线）
问题: 求曲面 $z=x^2+y^2$ 在点 $(1,2,5)$ 处的切平面方程和法线方程。
  步1: {'text': '令 $F=x^2+y^2-z$，$F_x=2x,\\ F_y=2y,\\ F_z=-1$，在 $(1,2,5)$：法向量 $\\boldsymbol n=(2,4,-1)$。', 'why': '代入点的坐标，注意 $F_z$ 是 $-1$。'}
  步2: {'text': '切平面：$2(x-1)+4(y-2)-(z-5)=0$，即 $2x+4y-z-5=0$。法线：$\\dfrac{x-1}{2}=\\dfrac{y-2}{4}=\\dfrac{z-5}{-1}$。', 'why': '检验切点在平面上：$2+8-5-5=0$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 4（方向导数与梯度）
问题: 设 $f=x^2y$，求在点 $(1,2)$ 处沿方向 $\boldsymbol l=(3,4)$ 的方向导数，以及方向导数的最大值。
  步1: {'text': '$\\nabla f=(2xy,\\ x^2)$，在 $(1,2)$：$(4,1)$。', 'why': '先求梯度。'}
  步2: {'text': '$\\boldsymbol l$ 的单位向量 $\\boldsymbol e_l=\\left(\\dfrac35,\\dfrac45\\right)$。$\\dfrac{\\partial f}{\\partial l}=4\\cdot\\dfrac35+1\\cdot\\dfrac45=\\dfrac{16}5$。', 'why': '方向导数是梯度与**单位**方向向量的数量积，别忘了把 $(3,4)$ 单位化。'}
  步3: {'text': '最大方向导数 $=|\\nabla f|=\\sqrt{16+1}=\\sqrt{17}$，方向是梯度方向 $(4,1)$。', 'why': '$\\sqrt{17}\\approx4.12>3.2$，符合「梯度方向增加最快」。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[SRC] advmath.ex.0204a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0204b: [{'relation': 'authored', 'note': '自造辨析题：驻点不一定是极值点'}]

[SRC] advmath.ex.0204c: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0204d: [{'relation': 'authored', 'note': '自造辨析题：只验证过切点不够，法向量也要对'}]

[SRC] advmath.ex.0204e: [{'relation': 'authored', 'note': '自造数值，已复算（与例 4 同题）'}]
===== ch3-sec1 =====

[SRC] advmath.ret.0301: [{'relation': 'authored', 'note': '预测题：先猜二重积分的几何意义，不判掌握度，如实标自造'}]

[PITFALL] 错: 极坐标下 $\displaystyle\iint_Df\,\mathrm dx\,\mathrm dy=\iint_Df(r\cos\theta,r\sin\theta)\,\mathrm dr\,\mathrm d\theta$。
  为何错: 漏了雅可比因子 $r$。检验面积：单位圆盘的面积是 $\pi$。正确做法 $\int_0^{2\pi}\mathrm d\theta\int_0^1r\,\mathrm dr=2\pi\cdot\frac12=\pi$。漏掉 $r$ 得 $\int_0^{2\pi}\mathrm d\theta\int_0^1\mathrm dr=2\pi$，是错的。
  对: $\mathrm d\sigma=r\,\mathrm dr\,\mathrm d\theta$。换元后遇到 $f\equiv1$，用已知面积核对一遍。

[EXAMPLE] 例 1（X 型区域的累次积分）
问题: 计算 $\displaystyle\iint_Dxy\,\mathrm d\sigma$，$D$ 由 $y=x$ 与 $y=x^2$ 围成。
  步1: {'text': '两曲线交点 $(0,0),(1,1)$；$0\\le x\\le1$ 时 $x^2\\le y\\le x$。', 'why': '解 $x=x^2$ 得交点；画图确定上下边界哪条在上。'}
  步2: {'text': '$\\displaystyle\\iint_Dxy\\,\\mathrm d\\sigma=\\int_0^1x\\,\\mathrm dx\\int_{x^2}^{x}y\\,\\mathrm dy=\\int_0^1x\\cdot\\frac{x^2-x^4}{2}\\,\\mathrm dx$。', 'why': '内层对 $y$ 积分，$x$ 是常数：$\\int y\\,\\mathrm dy=\\frac{y^2}{2}$，代入上下限 $x,\\ x^2$。'}
  步3: {'text': '$=\\dfrac12\\displaystyle\\int_0^1(x^3-x^5)\\,\\mathrm dx=\\dfrac12\\left(\\dfrac14-\\dfrac16\\right)=\\dfrac1{24}$。', 'why': '外层对 $x$ 积分。'}
  source: [{'relation': 'authored', 'note': '自造，积分已复算'}]

[EXAMPLE] 例 2（交换积分次序）
问题: 计算 $\displaystyle\int_0^1\mathrm dx\int_x^1\mathrm e^{y^2}\,\mathrm dy$。
  步1: {'text': '$\\mathrm e^{y^2}$ 的原函数不是初等函数，**不能**先对 $y$ 积分。区域：$0\\le x\\le1,\\ x\\le y\\le1$，即 $0\\le y\\le1,\\ 0\\le x\\le y$（三角形）。', 'why': '画图：直线 $y=x$ 上方、$y=1$ 下方、$x\\ge0$ 的三角形；换成 Y 型描述。'}
  步2: {'text': '交换：$\\displaystyle\\int_0^1\\mathrm dy\\int_0^y\\mathrm e^{y^2}\\,\\mathrm dx=\\int_0^1y\\,\\mathrm e^{y^2}\\,\\mathrm dy=\\left.\\frac12\\mathrm e^{y^2}\\right|_0^1=\\frac{\\mathrm e-1}{2}$。', 'why': '内层对 $x$ 积分，被积函数里没有 $x$，就是乘以区间长度 $y$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算；交换次序的经典例子'}]

[EXAMPLE] 例 3（极坐标）
问题: 计算 $\displaystyle\iint_{x^2+y^2\le1}(x^2+y^2)\,\mathrm d\sigma$。
  步1: {'text': '圆域，且被积函数是 $x^2+y^2=r^2$：用极坐标，$0\\le\\theta\\le2\\pi,\\ 0\\le r\\le1$。', 'why': '判断标志：圆域 + 被积函数含 $x^2+y^2$。'}
  步2: {'text': '$\\displaystyle\\int_0^{2\\pi}\\mathrm d\\theta\\int_0^1r^2\\cdot r\\,\\mathrm dr=2\\pi\\cdot\\frac14=\\frac\\pi2$。', 'why': '别漏 $r\\,\\mathrm dr\\,\\mathrm d\\theta$ 里的那个 $r$：被积函数 $r^2$ 乘面积元素的 $r$ 得 $r^3$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[SRC] advmath.ex.0301a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0301b: [{'relation': 'authored', 'note': '自造数值：常数被积函数的几何意义'}]

[SRC] advmath.ex.0301c: [{'relation': 'authored', 'note': '自造辨析题：交换次序要先画区域'}]

[SRC] advmath.ex.0301d: [{'relation': 'authored', 'note': '自造辨析题：圆域的极坐标上下限与 r 因子'}]

[SRC] advmath.ex.0301e: [{'relation': 'authored', 'note': '自造辨析题：用已知面积核对极坐标因子'}]
===== ch3-sec2 =====

[SRC] advmath.ret.0302: [{'relation': 'authored', 'note': '预测题：先猜三重积分的几何意义，不判掌握度，如实标自造'}]

[PITFALL] 错: 柱面坐标下 $\mathrm dv=\mathrm dr\,\mathrm d\theta\,\mathrm dz$。
  为何错: 柱面坐标的底面部分就是平面极坐标，面积元素 $r\,\mathrm dr\,\mathrm d\theta$，所以 $\mathrm dv=r\,\mathrm dr\,\mathrm d\theta\,\mathrm dz$。检验体积：$r\le1,\ 0\le z\le3$ 的圆柱体积 $\pi\cdot1^2\cdot3=3\pi$。正确：$\int_0^{2\pi}\mathrm d\theta\int_0^1r\,\mathrm dr\int_0^3\mathrm dz=3\pi$。
  对: 柱面坐标 $\mathrm dv=r\,\mathrm dr\,\mathrm d\theta\,\mathrm dz$；球面坐标 $\mathrm dv=\rho^2\sin\varphi\,\mathrm d\rho\,\mathrm d\varphi\,\mathrm d\theta$。每换一种坐标都要带上对应的因子。

[EXAMPLE] 例 1（直角坐标，体积）
问题: 求由平面 $x=0,\ y=0,\ z=0$ 和 $x+y+z=1$ 围成的四面体的体积。
  步1: {'text': '投影 $D_{xy}$：$x\\ge0,\\ y\\ge0,\\ x+y\\le1$；$z$ 从 $0$ 到 $1-x-y$。', 'why': '下底是 $z=0$，上顶是斜平面。'}
  步2: {'text': '$V=\\displaystyle\\int_0^1\\mathrm dx\\int_0^{1-x}\\mathrm dy\\int_0^{1-x-y}\\mathrm dz=\\int_0^1\\mathrm dx\\int_0^{1-x}(1-x-y)\\,\\mathrm dy=\\int_0^1\\frac{(1-x)^2}{2}\\,\\mathrm dx=\\frac16$。', 'why': '检验：棱锥体积 $=\\frac13\\times$ 底面积 $\\frac12\\times$ 高 1 $=\\frac16$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 2（柱面坐标）
问题: 计算 $\displaystyle\iiint_\Omega z\,\mathrm dv$，$\Omega$ 由 $z=x^2+y^2$ 与 $z=4$ 围成。
  步1: {'text': '投影是圆域 $x^2+y^2\\le4$，柱面坐标：$0\\le\\theta\\le2\\pi,\\ 0\\le r\\le2,\\ r^2\\le z\\le4$。', 'why': '$z=x^2+y^2$ 在柱面坐标下是 $z=r^2$。'}
  步2: {'text': '$\\displaystyle\\iiint_\\Omega z\\,\\mathrm dv=\\int_0^{2\\pi}\\mathrm d\\theta\\int_0^2r\\,\\mathrm dr\\int_{r^2}^4z\\,\\mathrm dz=2\\pi\\int_0^2r\\cdot\\frac{16-r^4}{2}\\,\\mathrm dr$。', 'why': '内层对 $z$ 积分得 $\\frac{16-r^4}{2}$；被积函数 $z$ 再乘体积元素里的 $r$。'}
  步3: {'text': '$=\\pi\\displaystyle\\int_0^2(16r-r^5)\\,\\mathrm dr=\\pi\\left(32-\\frac{64}{6}\\right)=\\dfrac{64\\pi}{3}$。', 'why': '$\\int_0^216r\\,\\mathrm dr=32$，$\\int_0^2r^5\\,\\mathrm dr=\\frac{64}{6}=\\frac{32}{3}$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 3（球面坐标，选学）
问题: 计算 $\displaystyle\iiint_{x^2+y^2+z^2\le1}(x^2+y^2+z^2)\,\mathrm dv$。
  步1: {'text': '单位球，被积函数 $=\\rho^2$：球面坐标 $0\\le\\rho\\le1,\\ 0\\le\\varphi\\le\\pi,\\ 0\\le\\theta\\le2\\pi$。', 'why': '球域加 $x^2+y^2+z^2$ 的标志。'}
  步2: {'text': '$\\displaystyle\\int_0^{2\\pi}\\mathrm d\\theta\\int_0^{\\pi}\\sin\\varphi\\,\\mathrm d\\varphi\\int_0^1\\rho^2\\cdot\\rho^2\\,\\mathrm d\\rho=2\\pi\\cdot2\\cdot\\frac15=\\dfrac{4\\pi}5$。', 'why': '三个积分变量互不牵连，可以分开算：$\\int\\sin\\varphi=2$，$\\int_0^1\\rho^4=\\frac15$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[SRC] advmath.ex.0302a: [{'relation': 'authored', 'note': '自造数值：长方体的体积'}]

[SRC] advmath.ex.0302b: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0302c: [{'relation': 'authored', 'note': '自造辨析题：体积与例 2 的区别在于被积函数'}]

[SRC] advmath.ex.0302d: [{'relation': 'authored', 'note': '自造；球面坐标体积元素（选学内容）'}]
===== ch3-sec3 =====

[SRC] advmath.ret.0303: [{'relation': 'authored', 'note': '预测题：先猜曲面面积与投影面积的关系，不判掌握度，如实标自造'}]

[PITFALL] 错: 曲面 $z=f(x,y)$ 在区域 $D$ 上的面积就是 $D$ 的面积 $\iint_D\mathrm d\sigma$。
  为何错: 这是曲面在底面上**投影**的面积。曲面倾斜时真实面积更大。例：平面 $z=x+y$ 在单位正方形上方，投影面积 1，真实面积 $\sqrt3$（$\sqrt{1+1+1}$ 倍）。
  对: $A=\iint_D\sqrt{1+f_x^2+f_y^2}\,\mathrm d\sigma$，被积函数是 1 的投影面积乘上倾斜系数。

[EXAMPLE] 例 1（平面的面积）
问题: 求平面 $z=x+y$ 在 $0\le x\le1,\ 0\le y\le1$ 上方部分的面积。
  步1: {'text': '$f_x=1,\\ f_y=1$，$\\sqrt{1+1+1}=\\sqrt3$（常数）。', 'why': '平面倾斜程度处处相同。'}
  步2: {'text': '$A=\\sqrt3\\displaystyle\\iint_D\\mathrm d\\sigma=\\sqrt3\\times1=\\sqrt3$。', 'why': '投影面积 1 乘放大系数。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 2（旋转抛物面的面积）
问题: 求抛物面 $z=x^2+y^2$ 在 $z\le1$ 部分的面积。
  步1: {'text': '$f_x=2x,\\ f_y=2y$，$\\sqrt{1+4x^2+4y^2}$；投影 $D:\\ x^2+y^2\\le1$。', 'why': '曲面 $z\\le1$ 对应 $x^2+y^2\\le1$。'}
  步2: {'text': '极坐标：$A=\\displaystyle\\int_0^{2\\pi}\\mathrm d\\theta\\int_0^1\\sqrt{1+4r^2}\\,r\\,\\mathrm dr=2\\pi\\left[\\frac{(1+4r^2)^{3/2}}{12}\\right]_0^1$。', 'why': '$\\frac{\\mathrm d}{\\mathrm dr}(1+4r^2)^{3/2}=12r\\sqrt{1+4r^2}$，所以原函数是 $\\frac{(1+4r^2)^{3/2}}{12}$。'}
  步3: {'text': '$A=2\\pi\\cdot\\dfrac{5\\sqrt5-1}{12}=\\dfrac{\\pi(5\\sqrt5-1)}{6}$。', 'why': '代入上限 $r=1$：$5^{3/2}=5\\sqrt5$，下限 $r=0$：1。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 3（质心，选学）
问题: 求均匀半圆盘 $x^2+y^2\le R^2,\ y\ge0$ 的质心。
  步1: {'text': '关于 $y$ 轴对称，$\\bar x=0$。', 'why': '对称性省去一半计算。'}
  步2: {'text': '$\\displaystyle\\iint_Dy\\,\\mathrm d\\sigma=\\int_0^\\pi\\sin\\theta\\,\\mathrm d\\theta\\int_0^Rr^2\\,\\mathrm dr=2\\cdot\\frac{R^3}{3}=\\frac{2R^3}{3}$，面积 $A=\\frac{\\pi R^2}{2}$。', 'why': '极坐标：$y=r\\sin\\theta$，面积元素 $r\\,\\mathrm dr\\,\\mathrm d\\theta$，故 $y\\,\\mathrm d\\sigma=r^2\\sin\\theta\\,\\mathrm dr\\,\\mathrm d\\theta$。'}
  步3: {'text': '$\\bar y=\\dfrac{2R^3/3}{\\pi R^2/2}=\\dfrac{4R}{3\\pi}$。质心 $\\left(0,\\dfrac{4R}{3\\pi}\\right)$。', 'why': '$\\frac{4}{3\\pi}\\approx0.42$，质心在圆心上方约 $0.42R$，比半径的一半低，合理。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[EXAMPLE] 例 4（转动惯量，选学）
问题: 求均匀圆盘 $x^2+y^2\le R^2$（面密度 1）对圆心 $O$ 的转动惯量。
  步1: {'text': '$I_O=\\displaystyle\\iint_D(x^2+y^2)\\,\\mathrm d\\sigma=\\int_0^{2\\pi}\\mathrm d\\theta\\int_0^Rr^2\\cdot r\\,\\mathrm dr=2\\pi\\cdot\\frac{R^4}{4}=\\dfrac{\\pi R^4}{2}$。', 'why': '与 §1 例 3 同类。质量 $M=\\pi R^2$，所以 $I_O=\\frac12MR^2$。'}
  source: [{'relation': 'authored', 'note': '自造，已复算'}]

[SRC] advmath.ex.0303a: [{'relation': 'authored', 'note': '自造数值，已复算'}]

[SRC] advmath.ex.0303b: [{'relation': 'authored', 'note': '自造辨析题：面积公式'}]

[SRC] advmath.ex.0303c: [{'relation': 'authored', 'note': '自造数值：对称性与公式互相检验'}]

[SRC] advmath.ex.0303d: [{'relation': 'authored', 'note': '自造辨析题：对哪条轴就用到那条轴的距离'}]