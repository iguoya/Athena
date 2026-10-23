===== ch1-sec2 =====

[RET] advmath.ret.0102 correct=B
  explain: 向量的模就是它的长度。在 $xOy$ 平面里，$(3,4)$ 是直角边为 3、4 的直角三角形的斜边：$\sqrt{3^2+4^2}=5$。空间里再加一项 $z^2$：$|\boldsymbol a|=\sqrt{x^2+y^2+z^2}$。

[EX-NUM] advmath.ex.0102a value=7 (type=numeric)
  solution: $\sqrt{(-2)^2+3^2+6^2}=\sqrt{4+9+36}=\sqrt{49}=7$。负号平方后消失。

[EX-NUM] advmath.ex.0102b value=8 (type=numeric)
  solution: 第 1 个分量：$2\times1-3\times(-2)=2+6=8$。（完整结果 $(8,1,6)$，见例 2。）

[EX-NUM] advmath.ex.0102c value=3 (type=numeric)
  solution: 平行 $\iff$ 对应分量成比例：$\dfrac12=\dfrac{-2}{-4}=\dfrac k6$，所以 $k=3$。

[EX-CHOICE] advmath.ex.0102d correct=B
  solution: 方向余弦是单位向量 $(\cos\alpha,\cos\beta,\cos\gamma)$ 的三个分量，它的模为 1，所以平方和为 1。D 错：$\sin^2$ 之和是 $3-1=2$。A、C 对一般向量不成立。

[EX-NUM] advmath.ex.0102e value=-3 (type=numeric)
  solution: 向量在坐标轴上的投影就是对应的坐标分量：$y$ 轴上为 $-3$。投影是数，可以为负，表示 $\boldsymbol a$ 与 $y$ 轴正向的夹角为钝角。
===== ch1-sec3 =====

[RET] advmath.ret.0103 correct=B
  explain: $\boldsymbol a\cdot\boldsymbol b=|\boldsymbol a||\boldsymbol b|\cos\theta=0$，两个模都非零，只能是 $\cos\theta=0$，$\theta=90^\circ$，垂直。数量积是判断垂直的工具。

[EX-NUM] advmath.ex.0103a value=-3 (type=numeric)
  solution: $1\cdot2+(-2)\cdot1+3\cdot(-1)=2-2-3=-3$。结果是数，不是向量。

[EX-NUM] advmath.ex.0103b value=-2 (type=numeric)
  solution: 垂直 $\iff\boldsymbol a\cdot\boldsymbol b=3k+2+4=0$，$k=-2$。

[EX-NUM] advmath.ex.0103c value=2 (type=numeric)
  solution: $\overrightarrow{AB}=(1,2,0),\ \overrightarrow{AC}=(2,0,0)$，$\overrightarrow{AB}\times\overrightarrow{AC}=(0,0,-4)$，模 4，面积 $\frac12\times4=2$。三点的 $z$ 坐标都是 1，在同一个水平面上，也可以直接用「底 2 × 高 2 ÷ 2」验证。

[EX-CHOICE] advmath.ex.0103d correct=B
  solution: 向量积**反交换**：交换两个因子，方向反过来，所以差一个负号。它是向量（不是数）；它**垂直**于 $\boldsymbol a$ 和 $\boldsymbol b$（不是平行）。
===== ch1-sec4 =====

[RET] advmath.ret.0104 correct=B
  explain: 方程里**没有 $z$**，意思是 $z$ 取任何值都满足，所以整条平行于 $z$ 轴的直线上的点都在图形上。在 $xOy$ 平面内它是半径为 2 的圆；沿 $z$ 轴方向把这个圆拉开，得到**圆柱面**。要得到那个圆，必须再加条件 $z=0$。

[EX-NUM] advmath.ex.0104a value=3 (type=numeric)
  solution: 配方：$(x+2)^2+(y-1)^2+z^2=4+4+1=9$，$R=3$，球心 $(-2,1,0)$。注意 $z$ 没有一次项，球心的 $z$ 坐标是 0。

[EX-CHOICE] advmath.ex.0104b correct=A
  solution: 绕 $y$ 轴旋转，$y$ 不变，$x$ 换成 $\pm\sqrt{x^2+z^2}$：$\dfrac{x^2+z^2}{4}+\dfrac{y^2}{9}=1$。B 把旋转轴搞反了（那是绕 $x$ 轴）；C 不是旋转曲面；D 是椭圆柱面（缺 $z$）。

[EX-CHOICE] advmath.ex.0104c correct=A
  solution: 由例 3：消去 $z$ 得 $2x^2-2x+y^2=0$，再与 $z=0$ 联立。B 少了 $z=0$，那是柱面；C 没有消去 $z$ 就直接令 $z=0$（把 $x+z=1$ 弄丢了）；D 右边应为 1 而不是 0。
===== ch1-sec5 =====

[RET] advmath.ret.0105 correct=B
  explain: 一个点 $M_0$ 加一个垂直于平面的向量 $\boldsymbol n$（法向量），平面上任一点 $M$ 满足 $\overrightarrow{M_0M}\perp\boldsymbol n$，即 $\overrightarrow{M_0M}\cdot\boldsymbol n=0$——这就是**点法式方程**。「一个点和一个方向」确定的是一条直线；两个点只确定一条直线。

[EX-CHOICE] advmath.ex.0105a correct=A
  solution: 点法式：$2(x-1)-(y-2)+(z-3)=0$，展开 $2x-2-y+2+z-3=0$，即 $2x-y+z-3=0$。检验过点：$2-2+3-3=0$ ✓。C 把点的坐标当成了法向量；B 常数项符号错；D 漏了常数项（过原点的平面）。

[EX-NUM] advmath.ex.0105b value=1 (type=numeric)
  solution: $d=\dfrac{|2\cdot1-2+2\cdot3-3|}{\sqrt{2^2+(-1)^2+2^2}}=\dfrac{|3|}{3}=1$。分子是绝对值，分母是法向量的模。

[EX-NUM] advmath.ex.0105c value=7 (type=numeric)
  solution: 例 3：$t=2$，$z=3+2\times2=7$（交点 $(3,0,7)$）。

[EX-CHOICE] advmath.ex.0105d correct=A
  solution: 方向向量 $=\boldsymbol n_1\times\boldsymbol n_2=(1,1,1)\times(1,-1,2)=(1\cdot2-1\cdot(-1),\ 1\cdot1-1\cdot2,\ 1\cdot(-1)-1\cdot1)=(3,-1,-2)$。B、C 是两个平面各自的法向量，不是直线的方向。

[EX-NUM] advmath.ex.0105e value=0.5 (type=numeric)
  solution: 法向量 $\boldsymbol n_1=(1,1,0),\ \boldsymbol n_2=(1,0,1)$，$\cos\theta=\dfrac{|1+0+0|}{\sqrt2\cdot\sqrt2}=\dfrac12$，夹角 $60^\circ$。
===== ch1-sec6 =====

[RET] advmath.ret.0106 correct=B
  explain: $z=h$ 代入：$x^2+y^2=h$，这是 $z=h$ 平面上半径 $\sqrt h$ 的圆。$h$ 越大圆越大，$h=0$ 时缩成一个点，$h<0$ 时无截痕——整个曲面是一个开口向上的碗。**用平行平面去截，看截痕如何变化**，是认识二次曲面的基本方法。

[EX-CHOICE] advmath.ex.0106a correct=C
  solution: 两正一负，右边 $+1$：单叶双曲面。若右边改成 $-1$ 才是双叶，改成 0 是锥面。

[EX-CHOICE] advmath.ex.0106b correct=B
  solution: $z^2=x^2+y^2$：右边为 0（没有常数项），顶点在原点，锥面。A 是旋转抛物面；C 是球面；D 是双叶双曲面（$x^2-y^2-z^2=1$，分成 $x\ge1$ 与 $x\le-1$ 两叶）。

[EX-NUM] advmath.ex.0106c value=5 (type=numeric)
  solution: $z=2$ 代入：$x^2+y^2=1+z^2=1+4=5$，半径 $\sqrt5$。

[EX-NUM] advmath.ex.0106d value=2 (type=numeric)
  solution: $x^2+y^2=4$，半径 $2$。若取 $z=-1$，则 $x^2+y^2=-1$ 无解，截痕为空：这个抛物面全在 $xOy$ 面上方。
===== ch2-sec1 =====

[RET] advmath.ret.0201 correct=B
  explain: 根号下要 $\ge0$：$1-x^2-y^2\ge0$，即 $x^2+y^2\le1$，原点为圆心、半径 1 的闭圆盘。一元函数的定义域是数轴上的一段，二元函数的定义域是**平面上的一块区域**。

[EX-CHOICE] advmath.ex.0201a correct=A
  solution: 对数的真数 $x+y>0$，严格大于 0，所以边界直线 $x+y=0$ 取不到。B 误含了边界；D 要求过强（$x=3,y=-1$ 时 $x+y=2>0$ 也在定义域内）。

[EX-NUM] advmath.ex.0201b value=1 (type=numeric)
  solution: 令 $u=x^2+y^2\to0$，$\dfrac{\sin u}{u}\to1$。

[EX-CHOICE] advmath.ex.0201c correct=C
  solution: 沿 $y=x$：$\dfrac{x^2}{2x^2}=\dfrac12$；沿 $y=-x$：$\dfrac{-x^2}{2x^2}=-\dfrac12$。两条路径极限不同，极限**不存在**。注意沿坐标轴趋近（$y=0$）得 0，只验证坐标轴会得出错误结论。

[EX-CHOICE] advmath.ex.0201d correct=B
  solution: 原点处函数值 $f(0,0)=0$ 有定义，但 $\lim_{(x,y)\to(0,0)}f(x,y)$ 不存在（上一题），所以 $f$ 在原点**不连续**。连续要求极限存在且等于函数值。
===== ch2-sec2 =====

[RET] advmath.ret.0202 correct=A
  explain: 偏导数是「只让一个变量变化，其余都固定」的变化率。$\partial z/\partial x$ 把 $y$ 当作常数：$\dfrac{\partial}{\partial x}(x^2y)=2xy$。所有的求导法则都和一元函数相同。

[EX-NUM] advmath.ex.0202a value=8 (type=numeric)
  solution: $z_x=2xy+y^2$，代入 $(1,2)$：$2\cdot1\cdot2+2^2=4+4=8$。

[EX-NUM] advmath.ex.0202b value=3 (type=numeric)
  solution: $z_{xy}=6x^2y-3$（例 2），代入 $(1,1)$：$6-3=3$。

[EX-NUM] advmath.ex.0202c value=0.4 (type=numeric)
  solution: 在 $(1,2)$：$\mathrm dz=z_x\mathrm dx+z_y\mathrm dy=16\times0.01+12\times0.02=0.4$。

[EX-CHOICE] advmath.ex.0202d correct=B
  solution: 只有「可微 $\Rightarrow$ 连续」成立。A、D 见上文陷阱（偏导数存在推不出连续、可微）；C 反例 $f=\sqrt{x^2+y^2}$ 在原点连续但偏导数不存在。
===== ch2-sec3 =====

[RET] advmath.ret.0203 correct=B
  explain: $x$ 通过**两条路**影响 $z$：经过 $u$（$x\to u\to z$）和经过 $v$（$x\to v\to z$）。链式法则把每条路的变化率相乘、再把各条路相加：$\dfrac{\partial z}{\partial x}=\dfrac{\partial z}{\partial u}\dfrac{\partial u}{\partial x}+\dfrac{\partial z}{\partial v}\dfrac{\partial v}{\partial x}$，共 2 项。

[EX-NUM] advmath.ex.0203a value=4 (type=numeric)
  solution: $z_u=2uv,\ z_v=u^2$，$u_x=1,\ v_x=1$。$z_x=2uv\cdot1+u^2\cdot1$。在 $(1,1)$：$u=2,\ v=0$，$z_x=0+4=4$。

[EX-CHOICE] advmath.ex.0203b correct=A
  solution: $F=x^3+y^3-3xy$，$F_x=3x^2-3y,\ F_y=3y^2-3x$。$\dfrac{\mathrm dy}{\mathrm dx}=-\dfrac{3x^2-3y}{3y^2-3x}=\dfrac{y-x^2}{y^2-x}$。B 漏了公式里的负号；C 把 $F_x/F_y$ 写成了 $F_y/F_x$（上下颠倒）；D 在约分时把减号看成了加号。

[EX-NUM] advmath.ex.0203c value=0.6 (type=numeric)
  solution: $F=x^2+y^2-z^2$，$F_x=2x,\ F_z=-2z$，$\dfrac{\partial z}{\partial x}=-\dfrac{2x}{-2z}=\dfrac xz$，在 $(3,4,5)$：$\dfrac35=0.6$。注意 $F_z=-2z$ 里自带负号，两个负号抵消。
===== ch2-sec4 =====

[RET] advmath.ret.0204 correct=B
  explain: $z=x^2+y^2\ge0=z(0,0)$，原点是最低点，**极小值点**（见下图左）。偏导数同时为零的点叫**驻点**，它是极值点的候选，但不一定是极值点——$z=xy$ 在原点也有 $z_x=z_y=0$，却是「鞍点」。

[EX-NUM] advmath.ex.0204a value=-5 (type=numeric)
  solution: $f_x=2x-2=0,\ f_y=2y+4=0$，驻点 $(1,-2)$；$A=2,\ B=0,\ C=2$，$\Delta=4>0,\ A>0$，极小。$f(1,-2)=1+4-2-8=-5$。（也可配方：$(x-1)^2+(y+2)^2-5$。）

[EX-CHOICE] advmath.ex.0204b correct=C
  solution: $z_x=y,\ z_y=x$，$(0,0)$ 是驻点；$A=0,\ B=1,\ C=0$，$\Delta=-1<0$，不是极值。

[EX-NUM] advmath.ex.0204c value=2 (type=numeric)
  solution: $L=x^2+y^2+\lambda(x+y-2)$：$2x+\lambda=0,\ 2y+\lambda=0$，所以 $x=y=1$，$f=2$。几何上这是原点到直线 $x+y=2$ 的最短距离的平方：距离 $\sqrt2$。

[EX-CHOICE] advmath.ex.0204d correct=A
  solution: 例 3：法向量 $(2,4,-1)$，$2(x-1)+4(y-2)-(z-5)=0$，即 $2x+4y-z-5=0$。A、B、C 三个平面**都过切点** $(1,2,5)$（代入都成立），只有 A 的法向量与曲面的法向量 $(2,4,-1)$ 一致：B 的法向量是 $(2,4,1)$，C 的是 $(1,2,-1)$，方向都不对。D 不过切点。

[EX-NUM] advmath.ex.0204e value=3.2 (type=numeric)
  solution: $\nabla f(1,2)=(4,1)$，单位方向 $(\frac35,\frac45)$，$\frac{\partial f}{\partial l}=4\cdot\frac35+1\cdot\frac45=\frac{16}5=3.2$。
===== ch3-sec1 =====

[RET] advmath.ret.0301 correct=B
  explain: 二重积分是把 $D$ 分成小块、每块取 $f\cdot\Delta\sigma$ 再求和。$f\equiv1$ 时每块就是 $\Delta\sigma$，总和是 $D$ 的面积 $\sigma$。若 $f\ge0$，二重积分是以 $D$ 为底、曲面 $z=f(x,y)$ 为顶的**曲顶柱体的体积**。

[EX-NUM] advmath.ex.0301a value=15 (type=numeric)
  solution: $\displaystyle\int_0^2\mathrm dx\int_0^3(x+y)\,\mathrm dy=\int_0^2\left(3x+\frac92\right)\mathrm dx=6+9=15$。矩形区域上限都是常数，次序可任意。

[EX-NUM] advmath.ex.0301b value=4 (type=numeric)
  solution: 被积函数是常数 2，积分 $=2\times D$ 的面积。三角形面积 $\frac12\cdot2\cdot2=2$，所以 $2\times2=4$。不需要写累次积分。

[EX-CHOICE] advmath.ex.0301c correct=A
  solution: 区域 $x^2\le y\le x$ 即 $y\le x\le\sqrt y$（$y\in[0,1]$）：左边界是 $x=y$（直线），右边界是 $x=\sqrt y$（抛物线 $y=x^2$ 的反函数）。B 上下限颠倒；C 用了错的边界；D 丢了抛物线边界。核对：$f\equiv1$ 时 $\int_0^1(\sqrt y-y)\mathrm dy=\frac23-\frac12=\frac16$，与面积一致。

[EX-CHOICE] advmath.ex.0301d correct=A
  solution: $x^2+y^2\le2x$ 即 $r^2\le2r\cos\theta$，$r\le2\cos\theta$（圆心 $(1,0)$、半径 1，在右半平面）；要 $\cos\theta\ge0$，$-\frac\pi2\le\theta\le\frac\pi2$。B 的 $\theta$ 范围错（$\cos\theta<0$ 时上限为负）；C 漏了 $r$；D 把圆当成了半径 2 的圆。

[EX-CHOICE] advmath.ex.0301e correct=A
  solution: 面积元素 $r\,\mathrm dr\,\mathrm d\theta$，$\theta$ 绕满一圈 $[0,2\pi]$：$2\pi\cdot\frac12=\pi$，与圆面积公式一致。B 漏 $r$；C 只转了半圈；D 多乘了一个 $r$。
===== ch3-sec2 =====

[RET] advmath.ret.0302 correct=B
  explain: 与二重积分同理：$f\equiv1$ 时每个小块的贡献就是它的体积 $\Delta v$，总和是 $\Omega$ 的体积 $V$。如果 $f$ 是密度，三重积分 $\iiint\rho\,\mathrm dv$ 就是质量。

[EX-NUM] advmath.ex.0302a value=6 (type=numeric)
  solution: 体积 $=1\times2\times3=6$。

[EX-NUM] advmath.ex.0302b value=0.5 (type=numeric)
  solution: $\displaystyle\int_0^1\mathrm dx\int_0^1\mathrm dy\int_0^1z\,\mathrm dz=1\cdot1\cdot\frac12=\frac12$。

[EX-CHOICE] advmath.ex.0302c correct=B
  solution: 柱面坐标：$V=\displaystyle\int_0^{2\pi}\mathrm d\theta\int_0^2r\,\mathrm dr\int_{r^2}^4\mathrm dz=2\pi\int_0^2(4r-r^3)\,\mathrm dr=2\pi(8-4)=8\pi$。D 是例 2 里 $\iiint z\,\mathrm dv$ 的值，被积函数不同。

[EX-CHOICE] advmath.ex.0302d correct=A
  solution: 球面坐标：$\mathrm dv=\rho^2\sin\varphi\,\mathrm d\rho\,\mathrm d\varphi\,\mathrm d\theta$。D 是**柱面**坐标的体积元素；B、C 漏了 $\sin\varphi$ 或 $\rho$ 的幂次不对。
===== ch3-sec3 =====

[RET] advmath.ret.0303 correct=C
  explain: 这块曲面是倾斜的平面，倾斜之后比它在底面的投影（面积 1）**大**。倾斜程度由法向量与 $z$ 轴的夹角决定，曲面面积公式里的 $\sqrt{1+z_x^2+z_y^2}\ge1$ 就是这个放大系数。

[EX-NUM] advmath.ex.0303a value=3 (type=numeric)
  solution: $z_x=z_y=2$，$\sqrt{1+4+4}=3$，面积 $=3\times1=3$。

[EX-CHOICE] advmath.ex.0303b correct=A
  solution: 放大系数是 $\sqrt{1+f_x^2+f_y^2}$。B 漏了根号；C 是投影面积；D 漏了 1（水平的曲面 $f_x=f_y=0$ 会得到面积 0，与事实不符）。

[EX-NUM] advmath.ex.0303c value=1 (type=numeric)
  solution: 矩形关于直线 $x=1$ 对称，质心在对称轴上，$\bar x=1$（也可算：$\iint x\,\mathrm d\sigma=\int_0^2x\cdot4\,\mathrm dx=8$，面积 8，$\bar x=1$）。

[EX-CHOICE] advmath.ex.0303d correct=A
  solution: 转动惯量是「质量 × 到轴距离的平方」。点 $(x,y)$ 到 $x$ 轴的距离是 $|y|$，所以对 $x$ 轴用 $y^2$。B 是对 $y$ 轴；C 是对原点；D 是质量。