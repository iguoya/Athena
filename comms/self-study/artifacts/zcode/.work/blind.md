===== ch1-sec2 =====

[RET] advmath.ret.0102
先猜再验：向量 $\boldsymbol a=(3,4,0)$ 的**模**（长度）是多少？
  A. 7
  B. 5
  C. 3
  D. 12

[EX-NUM type=numeric] advmath.ex.0102a (varies=含负分量：平方后与符号无关)
向量 $\boldsymbol a=(-2,3,6)$ 的模 $|\boldsymbol a|=$

[EX-NUM type=numeric] advmath.ex.0102b (varies=$-3\times(-2)$ 的符号：减去负数相当于加)
设 $\boldsymbol a=(1,2,3),\ \boldsymbol b=(-2,1,0)$，则 $2\boldsymbol a-3\boldsymbol b$ 的第 1 个分量为

[EX-NUM type=numeric] advmath.ex.0102c (varies=前两个分量的比 $\frac12$ 是已知条件，用来确定第三个分量)
设 $\boldsymbol a=(1,-2,k)$ 与 $\boldsymbol b=(2,-4,6)$ 平行，则 $k=$

[EX-CHOICE] advmath.ex.0102d (varies=方向角之间没有『和为 $\pi$』这类关系，约束只有余弦的平方和)
设向量的三个方向角为 $\alpha,\beta,\gamma$，则下列等式**恒成立**的是
  A. $\cos\alpha+\cos\beta+\cos\gamma=1$
  B. $\cos^2\alpha+\cos^2\beta+\cos^2\gamma=1$
  C. $\alpha+\beta+\gamma=\pi$
  D. $\sin^2\alpha+\sin^2\beta+\sin^2\gamma=1$

[EX-NUM type=numeric] advmath.ex.0102e (varies=投影是带符号的数，不是向量，也不是长度)
向量 $\boldsymbol a=(2,-3,5)$ 在 $y$ 轴上的投影为
===== ch1-sec3 =====

[RET] advmath.ret.0103
先猜再验：两个**非零**向量 $\boldsymbol a,\boldsymbol b$ 满足 $\boldsymbol a\cdot\boldsymbol b=0$，它们的位置关系是
  A. 平行
  B. 垂直
  C. 相等
  D. 反向

[EX-NUM type=numeric] advmath.ex.0103a (varies=含负分量；负的数量积说明夹角为钝角)
设 $\boldsymbol a=(1,-2,3),\ \boldsymbol b=(2,1,-1)$，则 $\boldsymbol a\cdot\boldsymbol b=$

[EX-NUM type=numeric] advmath.ex.0103b (varies=垂直用数量积，平行用分量成比例（§2），不要混用)
设 $\boldsymbol a=(k,2,-1)$ 与 $\boldsymbol b=(3,1,-4)$ 垂直，则 $k=$

[EX-NUM type=numeric] advmath.ex.0103c (varies=三角形面积是叉乘模的一半，别忘了除以 2)
以 $A(1,1,1),\ B(2,3,1),\ C(3,1,1)$ 为顶点的三角形面积为

[EX-CHOICE] advmath.ex.0103d (varies=向量积与数量积的区别：前者是向量、反交换，后者是数、可交换)
下列关于向量积的说法**正确**的是
  A. $\boldsymbol a\times\boldsymbol b=\boldsymbol b\times\boldsymbol a$
  B. $\boldsymbol a\times\boldsymbol b=-\boldsymbol b\times\boldsymbol a$
  C. $\boldsymbol a\times\boldsymbol b$ 是一个数
  D. $\boldsymbol a\times\boldsymbol b$ 与 $\boldsymbol a$ 平行
===== ch1-sec4 =====

[RET] advmath.ret.0104
先猜再验：方程 $x^2+y^2=4$ 在**空间直角坐标系**里表示什么图形？
  A. 一个圆
  B. 一个圆柱面
  C. 一个球面
  D. 一个抛物面

[EX-NUM type=numeric] advmath.ex.0104a (varies=缺少一次项的变量：球心该坐标为 0，不要漏掉右边补的项)
球面 $x^2+y^2+z^2+4x-2y=4$ 的半径为

[EX-CHOICE] advmath.ex.0104b (varies=旋转轴决定哪个变量保持不变)
$xOy$ 面上的椭圆 $\dfrac{x^2}{4}+\dfrac{y^2}{9}=1$ 绕 $y$ 轴旋转，所得旋转曲面方程为
  A. $\dfrac{x^2+z^2}{4}+\dfrac{y^2}{9}=1$
  B. $\dfrac{x^2}{4}+\dfrac{y^2+z^2}{9}=1$
  C. $\dfrac{x^2}{4}+\dfrac{y^2}{9}+z^2=1$
  D. $\dfrac{x^2}{4}+\dfrac{y^2}{9}=1$

[EX-CHOICE] advmath.ex.0104c (varies=两个方程联立的曲线：去掉 $z$ 后还要补上 $z=0$)
曲线 $\begin{cases}x^2+y^2+z^2=1\\x+z=1\end{cases}$ 在 $xOy$ 面上的投影曲线是
  A. $\begin{cases}2x^2-2x+y^2=0\\z=0\end{cases}$
  B. $2x^2-2x+y^2=0$
  C. $\begin{cases}x^2+y^2=1\\z=0\end{cases}$
  D. $\begin{cases}x^2+y^2+(1-x)^2=0\\z=0\end{cases}$
===== ch1-sec5 =====

[RET] advmath.ret.0105
先猜再验：要唯一确定空间中的一个平面，下面哪一组条件**最合适**？
  A. 一个点和一个方向
  B. 一个点和一个法向量
  C. 两个点
  D. 一条直线外的两个点

[EX-CHOICE] advmath.ex.0105a (varies=展开后用已知点代入验证，是最快的自查方法)
过点 $(1,2,3)$ 且以 $\boldsymbol n=(2,-1,1)$ 为法向量的平面方程为
  A. $2x-y+z-3=0$
  B. $2x-y+z+3=0$
  C. $x+2y+3z-3=0$
  D. $2x-y+z=0$

[EX-NUM type=numeric] advmath.ex.0105b (varies=距离公式的分子是把点代入平面方程左边，不是代入右边)
点 $P(1,2,3)$ 到平面 $2x-y+2z-3=0$ 的距离为

[EX-NUM type=numeric] advmath.ex.0105c (varies=把参数代回的是直线的参数式，不是平面方程)
直线 $x=1+t,\ y=2-t,\ z=3+2t$ 与平面 $x+y+z=10$ 的交点的 $z$ 坐标为

[EX-CHOICE] advmath.ex.0105d (varies=交线同时垂直于两个法向量，所以用叉乘)
直线 $\begin{cases}x+y+z=1\\x-y+2z=0\end{cases}$ 的一个方向向量为
  A. $(3,-1,-2)$
  B. $(1,1,1)$
  C. $(1,-1,2)$
  D. $(2,-1,3)$

[EX-NUM type=numeric] advmath.ex.0105e (varies=两平面夹角 = 法向量夹角，取锐角所以加绝对值)
平面 $x+y=1$ 与平面 $x+z=1$ 的夹角的余弦为
===== ch1-sec6 =====

[RET] advmath.ret.0106
先猜再验：用平面 $z=h$（$h>0$）去截曲面 $z=x^2+y^2$，截痕是什么？
  A. 一条直线
  B. 一个圆
  C. 一条抛物线
  D. 一个点

[EX-CHOICE] advmath.ex.0106a (varies=同一个左边，右边 $+1,0,-1$ 对应三类曲面)
曲面 $x^2+y^2-z^2=1$ 属于
  A. 椭球面
  B. 椭圆锥面
  C. 单叶双曲面
  D. 双叶双曲面

[EX-CHOICE] advmath.ex.0106b (varies=一次项、常数项、符号三个特征逐一核对)
下列方程中，表示**椭圆锥面**的是
  A. $z=x^2+y^2$
  B. $z^2=x^2+y^2$
  C. $x^2+y^2+z^2=1$
  D. $x^2-y^2-z^2=1$

[EX-NUM type=numeric] advmath.ex.0106c (varies=把 $z=h$ 代入后，右边是 $1+h^2$，不是 $1-h^2$（那会得到双叶）)
用平面 $z=2$ 截单叶双曲面 $x^2+y^2-z^2=1$，截痕圆的半径平方 $x^2+y^2$ 等于

[EX-NUM type=numeric] advmath.ex.0106d (varies=$z=h$ 的取值范围受曲面限制：抛物面只在 $h\ge0$ 一侧有截痕)
用平面 $z=4$ 截椭圆抛物面 $z=x^2+y^2$，截痕圆的半径为
===== ch2-sec1 =====

[RET] advmath.ret.0201
先猜再验：函数 $f(x,y)=\sqrt{1-x^2-y^2}$ 的**定义域**在平面上是什么图形？
  A. 整个平面
  B. 单位圆的内部和圆周（闭圆盘）
  C. 单位圆的外部
  D. 一条直线

[EX-CHOICE] advmath.ex.0201a (varies=边界取不取：严格不等号与区域的开闭)
函数 $z=\ln(x+y)$ 的定义域是
  A. $x+y>0$ 的半平面（不含直线 $x+y=0$）
  B. $x+y\ge0$ 的半平面
  C. 整个平面
  D. $x>0$ 且 $y>0$ 的第一象限

[EX-NUM type=numeric] advmath.ex.0201b (varies=分母恰是 $\sin$ 的自变量，才能整体替换)
$\displaystyle\lim_{(x,y)\to(0,0)}\frac{\sin(x^2+y^2)}{x^2+y^2}=$

[EX-CHOICE] advmath.ex.0201c (varies=要选两条结果不同的路径；沿轴的结果（0）容易让人误以为极限为 0)
关于 $\displaystyle\lim_{(x,y)\to(0,0)}\frac{xy}{x^2+y^2}$，正确的结论是
  A. 等于 0
  B. 等于 1
  C. 不存在
  D. 等于 $\dfrac12$

[EX-CHOICE] advmath.ex.0201d (varies=函数在该点有定义不等于连续，还要有极限并相等)
设 $f(x,y)=\begin{cases}\dfrac{xy}{x^2+y^2},&(x,y)\neq(0,0)\\0,&(x,y)=(0,0)\end{cases}$，则 $f$ 在原点
  A. 连续
  B. 不连续，因为极限不存在
  C. 不连续，因为函数值不等于 0
  D. 无定义
===== ch2-sec2 =====

[RET] advmath.ret.0202
先猜再验：求 $z=x^2y$ 对 $x$ 的偏导数时，应把 $y$ 看成什么？
  A. 常数
  B. $x$ 的函数
  C. 0
  D. 与 $x$ 同样的变量，一起求导

[EX-NUM type=numeric] advmath.ex.0202a (varies=先求偏导函数再代点，不要先代点再求导（先代 $y=2$ 也可以，但 $x$ 不能先代）)
设 $z=x^2y+xy^2$，则 $\dfrac{\partial z}{\partial x}\Big|_{(1,2)}=$

[EX-NUM type=numeric] advmath.ex.0202b (varies=混合偏导数在连续条件下与求导次序无关)
设 $z=x^3y^2-3xy+y$，则 $\dfrac{\partial^2z}{\partial x\partial y}\Big|_{(1,1)}=$

[EX-NUM type=numeric] advmath.ex.0202c (varies=$\mathrm dx,\mathrm dy$ 是自变量的改变量，不是函数值)
设 $z=x^2y^3$，则 $x$ 由 1 变为 1.01、$y$ 由 2 变为 2.02 时，全微分 $\mathrm dz$ 的值为

[EX-CHOICE] advmath.ex.0202d (varies=四个箭头只有一个成立)
对二元函数 $f(x,y)$，下列推断**正确**的是
  A. 两个偏导数都存在 $\Rightarrow$ 可微
  B. 可微 $\Rightarrow$ 连续
  C. 连续 $\Rightarrow$ 偏导数存在
  D. 偏导数存在 $\Rightarrow$ 连续
===== ch2-sec3 =====

[RET] advmath.ret.0203
先猜再验：$z=f(u,v)$，$u=x+y,\ v=xy$。求 $\dfrac{\partial z}{\partial x}$ 时，结果里有几项？
  A. 1 项
  B. 2 项
  C. 3 项
  D. 4 项

[EX-NUM type=numeric] advmath.ex.0203a (varies=先算中间变量在该点的值，再代入链式法则的结果)
设 $z=u^2v$，$u=x+y$，$v=x-y$，则 $\dfrac{\partial z}{\partial x}\Big|_{(1,1)}=$

[EX-CHOICE] advmath.ex.0203b (varies=分子分母同时变号不改变值，要看总的负号个数)
由方程 $x^3+y^3=3xy$ 确定 $y=y(x)$，则 $\dfrac{\mathrm dy}{\mathrm dx}=$
  A. $\dfrac{y-x^2}{y^2-x}$
  B. $\dfrac{x^2-y}{y^2-x}$
  C. $\dfrac{y^2-x}{y-x^2}$
  D. $\dfrac{y+x^2}{y^2+x}$

[EX-NUM type=numeric] advmath.ex.0203c (varies=$F_z$ 本身为负时，公式里的负号与它相消)
由 $x^2+y^2-z^2=0$ 确定 $z=z(x,y)$（上半锥面），则在点 $(3,4,5)$ 处 $\dfrac{\partial z}{\partial x}=$
===== ch2-sec4 =====

[RET] advmath.ret.0204
先猜再验：$z=x^2+y^2$ 在原点处 $z_x=z_y=0$。原点是极大值点、极小值点，还是都不是？
  A. 极大值点
  B. 极小值点
  C. 都不是
  D. 无法判断

[EX-NUM type=numeric] advmath.ex.0204a (varies=二次函数配方与偏导数两种方法对照)
函数 $f(x,y)=x^2+y^2-2x+4y$ 的极小值为

[EX-CHOICE] advmath.ex.0204b (varies=可导且驻点，但 $\Delta<0$)
函数 $z=xy$ 在点 $(0,0)$
  A. 取极大值
  B. 取极小值
  C. 不取极值（驻点但是鞍点）
  D. 不可导

[EX-NUM type=numeric] advmath.ex.0204c (varies=拉格朗日乘数法与几何意义（点到直线距离）互相检验)
在约束 $x+y=2$ 下，$f=x^2+y^2$ 的最小值为

[EX-CHOICE] advmath.ex.0204d (varies=过切点只是必要条件；法向量的符号决定它是不是切平面)
曲面 $z=x^2+y^2$ 在点 $(1,2,5)$ 处的切平面方程为
  A. $2x+4y-z-5=0$
  B. $2x+4y+z-15=0$
  C. $x+2y-z=0$
  D. $2x+4y-z=0$

[EX-NUM type=numeric] advmath.ex.0204e (varies=方向向量必须先单位化：用 $(3,4)$ 直接计算会得到 16（是 5 倍）)
设 $f=x^2y$，则在点 $(1,2)$ 处沿方向 $\boldsymbol l=(3,4)$ 的方向导数为
===== ch3-sec1 =====

[RET] advmath.ret.0301
先猜再验：被积函数恒等于 1 时，二重积分 $\displaystyle\iint_Df(x,y)\,\mathrm d\sigma=\iint_D1\,\mathrm d\sigma$ 的值是什么？
  A. 0
  B. 区域 $D$ 的面积
  C. 区域 $D$ 的周长
  D. 与 $D$ 无关的常数 1

[EX-NUM type=numeric] advmath.ex.0301a (varies=矩形区域：内层上下限也是常数)
计算 $\displaystyle\iint_D(x+y)\,\mathrm d\sigma$，$D=\{(x,y)\,|\,0\le x\le2,\ 0\le y\le3\}$。

[EX-NUM type=numeric] advmath.ex.0301b (varies=被积函数为常数：直接用面积)
设 $D$ 是顶点为 $(0,0),(2,0),(0,2)$ 的三角形，则 $\displaystyle\iint_D2\,\mathrm d\sigma=$

[EX-CHOICE] advmath.ex.0301c (varies=用 $f\equiv1$ 求面积检验两种次序给出同一个值)
$D$ 由 $y=x$ 与 $y=x^2$ 围成（例 1 的区域），则 $\displaystyle\int_0^1\mathrm dx\int_{x^2}^{x}f(x,y)\,\mathrm dy$ 交换积分次序后等于
  A. $\displaystyle\int_0^1\mathrm dy\int_y^{\sqrt y}f(x,y)\,\mathrm dx$
  B. $\displaystyle\int_0^1\mathrm dy\int_{\sqrt y}^{y}f(x,y)\,\mathrm dx$
  C. $\displaystyle\int_0^1\mathrm dy\int_{y^2}^{y}f(x,y)\,\mathrm dx$
  D. $\displaystyle\int_0^1\mathrm dy\int_0^{y}f(x,y)\,\mathrm dx$

[EX-CHOICE] advmath.ex.0301d (varies=圆不过原点以外的情形：上限是 $\theta$ 的函数)
$D:\ x^2+y^2\le2x$，则 $\displaystyle\iint_Df(x,y)\,\mathrm d\sigma$ 化为极坐标下的累次积分是
  A. $\displaystyle\int_{-\pi/2}^{\pi/2}\mathrm d\theta\int_0^{2\cos\theta}f(r\cos\theta,r\sin\theta)\,r\,\mathrm dr$
  B. $\displaystyle\int_0^{2\pi}\mathrm d\theta\int_0^{2\cos\theta}f(r\cos\theta,r\sin\theta)\,r\,\mathrm dr$
  C. $\displaystyle\int_{-\pi/2}^{\pi/2}\mathrm d\theta\int_0^{2\cos\theta}f(r\cos\theta,r\sin\theta)\,\mathrm dr$
  D. $\displaystyle\int_{-\pi/2}^{\pi/2}\mathrm d\theta\int_0^{2}f(r\cos\theta,r\sin\theta)\,r\,\mathrm dr$

[EX-CHOICE] advmath.ex.0301e (varies=四个选项各错一处：漏 $r$、范围、多一个 $r$)
用极坐标计算单位圆盘 $x^2+y^2\le1$ 的面积 $\displaystyle\iint1\,\mathrm d\sigma$，正确的结果与算式是
  A. $\displaystyle\int_0^{2\pi}\mathrm d\theta\int_0^1r\,\mathrm dr=\pi$
  B. $\displaystyle\int_0^{2\pi}\mathrm d\theta\int_0^1\mathrm dr=2\pi$
  C. $\displaystyle\int_0^{\pi}\mathrm d\theta\int_0^1r\,\mathrm dr=\dfrac\pi2$
  D. $\displaystyle\int_0^{2\pi}\mathrm d\theta\int_0^1r^2\,\mathrm dr=\dfrac{2\pi}3$
===== ch3-sec2 =====

[RET] advmath.ret.0302
先猜再验：被积函数恒为 1 时，三重积分 $\displaystyle\iiint_\Omega1\,\mathrm dv$ 的值是
  A. 0
  B. 立体 $\Omega$ 的体积
  C. 立体 $\Omega$ 的表面积
  D. 1

[EX-NUM type=numeric] advmath.ex.0302a (varies=被积函数为 1：直接取体积)
$\Omega=\{(x,y,z)\,|\,0\le x\le1,\ 0\le y\le2,\ 0\le z\le3\}$，则 $\displaystyle\iiint_\Omega\mathrm dv=$

[EX-NUM type=numeric] advmath.ex.0302b (varies=被积函数只含 $z$：$x,y$ 方向的积分只贡献区间长度)
单位立方体 $\Omega=[0,1]\times[0,1]\times[0,1]$ 上，$\displaystyle\iiint_\Omega z\,\mathrm dv=$

[EX-CHOICE] advmath.ex.0302c (varies=同一个立体，被积函数是 1（体积）与 $z$（例 2）算出的是两个量)
抛物面 $z=x^2+y^2$ 与平面 $z=4$ 所围立体（例 2 的区域）的体积为
  A. $4\pi$
  B. $8\pi$
  C. $16\pi$
  D. $\dfrac{64\pi}3$

[EX-CHOICE] advmath.ex.0302d (varies=区分柱面与球面坐标的体积元素)
球面坐标下的体积元素 $\mathrm dv=$
  A. $\rho^2\sin\varphi\,\mathrm d\rho\,\mathrm d\varphi\,\mathrm d\theta$
  B. $\rho\,\mathrm d\rho\,\mathrm d\varphi\,\mathrm d\theta$
  C. $\rho^2\,\mathrm d\rho\,\mathrm d\varphi\,\mathrm d\theta$
  D. $r\,\mathrm dr\,\mathrm d\theta\,\mathrm dz$
===== ch3-sec3 =====

[RET] advmath.ret.0303
先猜再验：曲面 $z=x+y$ 在 $xOy$ 面上方正方形 $0\le x,y\le1$ 之上的那一块，面积比 $1$ 大还是小？
  A. 比 1 小
  B. 等于 1
  C. 比 1 大
  D. 无法比较

[EX-NUM type=numeric] advmath.ex.0303a (varies=常数项 $+1$ 只平移曲面，不影响面积)
曲面 $z=2x+2y+1$ 在 $0\le x\le1,\ 0\le y\le1$ 上方部分的面积为

[EX-CHOICE] advmath.ex.0303b (varies=用水平面（$f_x=f_y=0$）检验公式：应该得到 $D$ 的面积)
曲面 $z=f(x,y)$ 在 $D$ 上的面积公式是
  A. $\displaystyle\iint_D\sqrt{1+f_x^2+f_y^2}\,\mathrm d\sigma$
  B. $\displaystyle\iint_D(1+f_x^2+f_y^2)\,\mathrm d\sigma$
  C. $\displaystyle\iint_D\mathrm d\sigma$
  D. $\displaystyle\iint_D\sqrt{f_x^2+f_y^2}\,\mathrm d\sigma$

[EX-NUM type=numeric] advmath.ex.0303c (varies=用对称性几乎不需要计算)
均匀矩形薄片 $0\le x\le2,\ 0\le y\le4$ 的质心的横坐标 $\bar x=$

[EX-CHOICE] advmath.ex.0303d (varies=对 $x$ 轴用 $y^2$，对 $y$ 轴用 $x^2$：下标和被积变量是『反』的)
薄片 $D$（面密度 $\rho$）对 $x$ 轴的转动惯量 $I_x=$
  A. $\displaystyle\iint_Dy^2\rho\,\mathrm d\sigma$
  B. $\displaystyle\iint_Dx^2\rho\,\mathrm d\sigma$
  C. $\displaystyle\iint_D(x^2+y^2)\rho\,\mathrm d\sigma$
  D. $\displaystyle\iint_D\rho\,\mathrm d\sigma$