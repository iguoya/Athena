
# ch4-sec1 / pitfall
{
 "kind": "pitfall",
 "wrong": "把 $L$ 的方向反过来，对弧长的曲线积分要变号：$\\displaystyle\\int_{L^-}f\\,\\mathrm ds=-\\int_Lf\\,\\mathrm ds$。",
 "why_wrong": "变号是下一节**对坐标**的曲线积分的性质。对弧长的积分里 $\\mathrm ds$ 是弧长元素，永远非负，与走向无关。例：$f\\equiv1$ 时积分是弧长，不可能因为反向而变成负数。",
 "right": "对弧长：$\\displaystyle\\int_{L^-}f\\,\\mathrm ds=\\int_Lf\\,\\mathrm ds$。对坐标：$\\displaystyle\\int_{L^-}P\\,\\mathrm dx+Q\\,\\mathrm dy=-\\int_LP\\,\\mathrm dx+Q\\,\\mathrm dy$。"
}
# ch4-sec1 / example
{
 "kind": "example",
 "title": "例 1（参数方程）",
 "problem": "计算 $\\displaystyle\\int_Lxy\\,\\mathrm ds$，$L$ 是 $x=\\cos t,\\ y=\\sin t\\ \\left(0\\le t\\le\\frac\\pi2\\right)$。",
 "steps": [
  {
   "text": "$x'=-\\sin t,\\ y'=\\cos t$，$\\sqrt{x'^2+y'^2}=1$，所以 $\\mathrm ds=\\mathrm dt$。",
   "why": "单位圆上弧长元素就是角度元素。"
  },
  {
   "text": "$\\displaystyle\\int_0^{\\pi/2}\\cos t\\sin t\\,\\mathrm dt=\\left.\\frac{\\sin^2t}{2}\\right|_0^{\\pi/2}=\\dfrac12$。",
   "why": "下限小于上限。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec1 / example
{
 "kind": "example",
 "title": "例 2（直线段）",
 "problem": "计算 $\\displaystyle\\int_L(x+y)\\,\\mathrm ds$，$L$ 是线段 $y=2x\\ (0\\le x\\le1)$。",
 "steps": [
  {
   "text": "$y'=2$，$\\mathrm ds=\\sqrt{1+4}\\,\\mathrm dx=\\sqrt5\\,\\mathrm dx$；在 $L$ 上 $x+y=3x$。",
   "why": "把 $y$ 用 $2x$ 代入，$\\mathrm ds$ 用 $\\sqrt{1+y'^2}\\,\\mathrm dx$。"
  },
  {
   "text": "$\\displaystyle\\int_0^13x\\sqrt5\\,\\mathrm dx=\\frac{3\\sqrt5}{2}$。",
   "why": "$\\sqrt5$ 是常数，提出。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec1 / example
{
 "kind": "example",
 "title": "例 3（质量）",
 "problem": "半径为 2 的半圆形细丝 $x^2+y^2=4,\\ y\\ge0$，线密度 $\\rho=y$，求质量。",
 "steps": [
  {
   "text": "参数 $x=2\\cos t,\\ y=2\\sin t\\ (0\\le t\\le\\pi)$，$\\mathrm ds=2\\,\\mathrm dt$。",
   "why": "半径 $R=2$ 时 $\\mathrm ds=R\\,\\mathrm dt$。"
  },
  {
   "text": "$M=\\displaystyle\\int_Ly\\,\\mathrm ds=\\int_0^\\pi2\\sin t\\cdot2\\,\\mathrm dt=4\\cdot2=8$。",
   "why": "$\\int_0^\\pi\\sin t\\,\\mathrm dt=2$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec2 / pitfall
{
 "kind": "pitfall",
 "wrong": "化成定积分时，参数的下限一定比上限小，所以从 $t=\\pi$ 走到 $t=0$ 也要写成 $\\int_0^\\pi$。",
 "why_wrong": "对坐标的曲线积分，**下限是起点的参数，上限是终点的参数**，可以下限大于上限。把积分限写反就是把方向弄反了，结果差一个符号。例：$\\displaystyle\\int_{(1,1)\\to(0,0)}y\\,\\mathrm dx+x\\,\\mathrm dy$（$y=x^2$ 反向）$=\\int_1^0 3x^2\\,\\mathrm dx=-1$。",
 "right": "先判断起点、终点，再把参数限按「起点 $\\to$ 终点」写。下限小于上限只是**对弧长**积分的要求。"
}
# ch4-sec2 / example
{
 "kind": "example",
 "title": "例 1（沿抛物线）",
 "problem": "计算 $\\displaystyle\\int_Ly\\,\\mathrm dx+x\\,\\mathrm dy$，$L$ 是抛物线 $y=x^2$ 上从 $(0,0)$ 到 $(1,1)$ 的一段。",
 "steps": [
  {
   "text": "$y=x^2,\\ y'=2x$，$x$ 从 0 到 1：$\\displaystyle\\int_0^1\\left[x^2\\cdot1+x\\cdot2x\\right]\\mathrm dx$。",
   "why": "$P=y=x^2$，$Q=x$，$\\mathrm dy=y'\\mathrm dx=2x\\,\\mathrm dx$。"
  },
  {
   "text": "$=\\displaystyle\\int_0^13x^2\\,\\mathrm dx=1$。",
   "why": "也可以看出 $y\\,\\mathrm dx+x\\,\\mathrm dy=\\mathrm d(xy)$，积分 $=xy\\big|_{(0,0)}^{(1,1)}=1$，只与起点终点有关（下节）。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec2 / example
{
 "kind": "example",
 "title": "例 2（逆时针沿圆）",
 "problem": "计算 $\\displaystyle\\oint_L-y\\,\\mathrm dx+x\\,\\mathrm dy$，$L$ 是单位圆 $x^2+y^2=1$，逆时针方向。",
 "steps": [
  {
   "text": "参数 $x=\\cos t,\\ y=\\sin t$，$t$ 从 0 到 $2\\pi$（逆时针，起点 $t=0$，终点 $t=2\\pi$）。",
   "why": "方向决定参数增加的方向。"
  },
  {
   "text": "$\\displaystyle\\int_0^{2\\pi}\\left[-\\sin t\\cdot(-\\sin t)+\\cos t\\cdot\\cos t\\right]\\mathrm dt=\\int_0^{2\\pi}1\\,\\mathrm dt=2\\pi$。",
   "why": "这是单位圆面积 $\\pi$ 的 2 倍，下节格林公式给出原因。顺时针时结果是 $-2\\pi$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec3 / figure
{
 "kind": "figure",
 "file": "ch4-sec3-green.svg",
 "caption": "左：正向 = 沿边界前进时区域在左侧（逆时针）。右：区域内部若含 $P,Q$ 无定义的奇点（如原点），格林公式的条件不满足，不能直接用。"
}
# ch4-sec3 / pitfall
{
 "kind": "pitfall",
 "wrong": "$\\displaystyle\\frac{\\partial Q}{\\partial x}=\\frac{\\partial P}{\\partial y}$ 处处成立，所以沿**任何**闭曲线的积分都是 0。",
 "why_wrong": "忽略了「区域内 $P,Q$ 要有连续偏导数」。例：$P=\\dfrac{-y}{x^2+y^2},\\ Q=\\dfrac{x}{x^2+y^2}$，在除去原点的平面上 $Q_x=P_y$ 处处成立，但沿单位圆逆时针一圈 $\\oint=\\int_0^{2\\pi}(\\sin^2t+\\cos^2t)\\,\\mathrm dt=2\\pi\\neq0$，因为圆内有奇点原点，$P,Q$ 在那里无定义。",
 "right": "路径无关的结论要求 $D$ **单连通**且 $P,Q$ 在 $D$ 内处处有连续偏导。闭曲线内含奇点时必须单独处理。"
}
# ch4-sec3 / example
{
 "kind": "example",
 "title": "例 1（用格林公式化为二重积分）",
 "problem": "计算 $\\displaystyle\\oint_Ly^2\\,\\mathrm dx+x\\,\\mathrm dy$，$L$ 是由 $y=x^2$ 与 $y=x$ 围成区域的正向边界。",
 "steps": [
  {
   "text": "$P=y^2,\\ Q=x$，$\\dfrac{\\partial Q}{\\partial x}-\\dfrac{\\partial P}{\\partial y}=1-2y$。",
   "why": "先写出被积函数。"
  },
  {
   "text": "$D$：$0\\le x\\le1,\\ x^2\\le y\\le x$。$\\displaystyle\\iint_D(1-2y)\\,\\mathrm d\\sigma=\\int_0^1\\mathrm dx\\int_{x^2}^{x}(1-2y)\\,\\mathrm dy=\\int_0^1\\left[y-y^2\\right]_{x^2}^{x}\\mathrm dx$。",
   "why": "内层对 $y$ 积分，上下限分别代入 $x$ 与 $x^2$。"
  },
  {
   "text": "$=\\displaystyle\\int_0^1(x-2x^2+x^4)\\,\\mathrm dx=\\frac12-\\frac23+\\frac15=\\frac1{30}$。",
   "why": "已用直接沿 $y=x^2$（$0\\to1$）再沿 $y=x$（$1\\to0$）两段计算验证，结果同为 $\\frac1{30}$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造；公式与直接计算两种方法已用 sympy 对照"
  }
 ]
}
# ch4-sec3 / example
{
 "kind": "example",
 "title": "例 2（用曲线积分求面积）",
 "problem": "求椭圆 $x=a\\cos t,\\ y=b\\sin t$（$0\\le t\\le2\\pi$）围成的面积。",
 "steps": [
  {
   "text": "$A=\\dfrac12\\oint_Lx\\,\\mathrm dy-y\\,\\mathrm dx=\\dfrac12\\displaystyle\\int_0^{2\\pi}\\left[a\\cos t\\cdot b\\cos t-b\\sin t\\cdot(-a\\sin t)\\right]\\mathrm dt$。",
   "why": "$\\mathrm dx=-a\\sin t\\,\\mathrm dt,\\ \\mathrm dy=b\\cos t\\,\\mathrm dt$；$t$ 增大时逆时针，是正向。"
  },
  {
   "text": "$=\\dfrac12\\displaystyle\\int_0^{2\\pi}ab\\,\\mathrm dt=\\pi ab$。",
   "why": "$a=b=R$ 时得圆的面积 $\\pi R^2$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec3 / example
{
 "kind": "example",
 "title": "例 3（路径无关与全微分求积）",
 "problem": "证明 $2xy\\,\\mathrm dx+x^2\\,\\mathrm dy$ 是全微分，并求 $\\displaystyle\\int_{(0,0)}^{(1,2)}2xy\\,\\mathrm dx+x^2\\,\\mathrm dy$。",
 "steps": [
  {
   "text": "$P=2xy,\\ Q=x^2$：$\\dfrac{\\partial Q}{\\partial x}=2x=\\dfrac{\\partial P}{\\partial y}$，在全平面（单连通）上成立，所以是全微分，积分与路径无关。",
   "why": "判别式相等。"
  },
  {
   "text": "找 $u$：$u_x=2xy\\Rightarrow u=x^2y+\\varphi(y)$，$u_y=x^2+\\varphi'(y)=x^2\\Rightarrow\\varphi'=0$。取 $u=x^2y$。",
   "why": "先对 $x$ 积分，再用 $u_y=Q$ 确定 $y$ 的部分。"
  },
  {
   "text": "积分 $=u(1,2)-u(0,0)=2-0=2$。",
   "why": "只与起点终点有关；沿折线 $(0,0)\\to(1,0)\\to(1,2)$ 计算：第一段 $y=0$ 积分为 0，第二段 $x=1$ 积分 $\\int_0^21\\,\\mathrm dy=2$，也得 2。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec4 / pitfall
{
 "kind": "pitfall",
 "wrong": "对面积的曲面积分化成二重积分时，面积元素 $\\mathrm dS=\\mathrm dx\\,\\mathrm dy$。",
 "why_wrong": "$\\mathrm dx\\,\\mathrm dy$ 是**投影**面积元素，曲面倾斜时 $\\mathrm dS$ 更大：$\\mathrm dS=\\sqrt{1+z_x^2+z_y^2}\\,\\mathrm dx\\,\\mathrm dy$。例：平面 $x+y+z=1$ 的 $\\mathrm dS=\\sqrt3\\,\\mathrm dx\\,\\mathrm dy$，漏掉 $\\sqrt3$ 结果会错。",
 "right": "$\\mathrm dS=\\sqrt{1+z_x^2+z_y^2}\\,\\mathrm dx\\,\\mathrm dy$。下一节对**坐标**的曲面积分才直接用 $\\mathrm dx\\,\\mathrm dy$。"
}
# ch4-sec4 / example
{
 "kind": "example",
 "title": "例 1（平面）",
 "problem": "计算 $\\displaystyle\\iint_\\Sigma(x+y+z)\\,\\mathrm dS$，$\\Sigma$ 是平面 $x+y+z=1$ 在第一卦限的部分。",
 "steps": [
  {
   "text": "在 $\\Sigma$ 上 $x+y+z=1$，所以被积函数 $=1$，积分 $=\\iint_\\Sigma\\mathrm dS$（$\\Sigma$ 的面积）。",
   "why": "先代入曲面方程，大大简化。"
  },
  {
   "text": "$z=1-x-y$，$z_x=z_y=-1$，$\\mathrm dS=\\sqrt3\\,\\mathrm dx\\,\\mathrm dy$；投影 $D_{xy}$ 是三角形 $x,y\\ge0,\\ x+y\\le1$，面积 $\\frac12$。积分 $=\\sqrt3\\cdot\\dfrac12=\\dfrac{\\sqrt3}2$。",
   "why": "投影面积乘倾斜系数 $\\sqrt3$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec4 / example
{
 "kind": "example",
 "title": "例 2（上半球面）",
 "problem": "计算 $\\displaystyle\\iint_\\Sigma z\\,\\mathrm dS$，$\\Sigma$ 是上半球面 $z=\\sqrt{R^2-x^2-y^2}$。",
 "steps": [
  {
   "text": "$z_x=\\dfrac{-x}{z},\\ z_y=\\dfrac{-y}{z}$，$\\sqrt{1+z_x^2+z_y^2}=\\sqrt{\\dfrac{z^2+x^2+y^2}{z^2}}=\\dfrac Rz$。",
   "why": "利用 $x^2+y^2+z^2=R^2$。"
  },
  {
   "text": "$\\displaystyle\\iint_\\Sigma z\\,\\mathrm dS=\\iint_{x^2+y^2\\le R^2}z\\cdot\\frac Rz\\,\\mathrm dx\\,\\mathrm dy=R\\cdot\\pi R^2=\\pi R^3$。",
   "why": "$z$ 恰好被约去，剩下 $R$ 乘投影圆盘面积 $\\pi R^2$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec5 / figure
{
 "kind": "figure",
 "file": "ch4-sec5-orientation.svg",
 "caption": "上半球面 $x^2+y^2+z^2=1,\\ z\\ge0$ 的**外侧**：法向量（箭头）指向球外，在曲面的上部也是「向上」，所以外侧对 $\\mathrm dx\\,\\mathrm dy$ 来说是上侧。"
}
# ch4-sec5 / pitfall
{
 "kind": "pitfall",
 "wrong": "$\\displaystyle\\iint_\\Sigma R\\,\\mathrm dx\\,\\mathrm dy$ 和 $\\displaystyle\\iint_\\Sigma R\\,\\mathrm dS$ 是同一个东西，都等于 $\\iint_{D_{xy}}R\\,\\sqrt{1+z_x^2+z_y^2}\\,\\mathrm dx\\,\\mathrm dy$。",
 "why_wrong": "前者对坐标，$\\mathrm dx\\,\\mathrm dy$ 是**带符号投影**，化成二重积分时**没有**倾斜系数，且要判断侧。后者对面积。例：单位上半球面，$\\displaystyle\\iint_\\Sigma z\\,\\mathrm dS=\\pi$（§4 例 2，$R=1$），而上侧的 $\\displaystyle\\iint_\\Sigma z\\,\\mathrm dx\\,\\mathrm dy=\\iint_{x^2+y^2\\le1}\\sqrt{1-x^2-y^2}\\,\\mathrm dx\\,\\mathrm dy=\\dfrac{2\\pi}3$。",
 "right": "对坐标：$\\pm\\iint_{D_{xy}}R(x,y,z(x,y))\\,\\mathrm dx\\,\\mathrm dy$；对面积：$\\iint_{D_{xy}}f\\sqrt{1+z_x^2+z_y^2}\\,\\mathrm dx\\,\\mathrm dy$。"
}
# ch4-sec5 / example
{
 "kind": "example",
 "title": "例 1（投影法）",
 "problem": "计算 $\\displaystyle\\iint_\\Sigma z\\,\\mathrm dx\\,\\mathrm dy$，$\\Sigma$ 是上半球面 $x^2+y^2+z^2=1,\\ z\\ge0$ 的上侧（外侧）。",
 "steps": [
  {
   "text": "$\\Sigma:\\ z=\\sqrt{1-x^2-y^2}$，投影 $D_{xy}:\\ x^2+y^2\\le1$；上侧取 $+$。",
   "why": "外侧在上半球就是朝上的一侧。"
  },
  {
   "text": "$\\displaystyle\\iint_{x^2+y^2\\le1}\\sqrt{1-x^2-y^2}\\,\\mathrm dx\\,\\mathrm dy=\\int_0^{2\\pi}\\mathrm d\\theta\\int_0^1\\sqrt{1-r^2}\\,r\\,\\mathrm dr=2\\pi\\cdot\\frac13=\\frac{2\\pi}3$。",
   "why": "极坐标；$\\int_0^1r\\sqrt{1-r^2}\\,\\mathrm dr=\\frac13$。结果是半球体积的量级：$\\frac{2\\pi}3$ 正好是上半球的体积。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch4-sec5 / example
{
 "kind": "example",
 "title": "例 2（高斯公式，选学）",
 "problem": "计算 $\\displaystyle\\oint\\!\\!\\!\\oint_\\Sigma x\\,\\mathrm dy\\,\\mathrm dz+y\\,\\mathrm dz\\,\\mathrm dx+z\\,\\mathrm dx\\,\\mathrm dy$，$\\Sigma$ 是球面 $x^2+y^2+z^2=R^2$ 的外侧。",
 "steps": [
  {
   "text": "$P=x,\\ Q=y,\\ R=z$，$\\operatorname{div}\\boldsymbol A=1+1+1=3$。",
   "why": "高斯公式的被积函数。"
  },
  {
   "text": "$\\displaystyle\\iiint_\\Omega3\\,\\mathrm dv=3\\cdot\\frac43\\pi R^3=4\\pi R^3$。",
   "why": "也等于球面面积 $4\\pi R^2$ 乘 $R$：在球面上 $\\boldsymbol A\\cdot\\boldsymbol n=R$。两种方法一致。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch5-sec1 / figure
{
 "kind": "figure",
 "file": "ch5-sec1-family.svg",
 "caption": "$y'=y$ 的通解 $y=C\\mathrm e^x$ 是一族曲线（灰色）；初始条件 $y(0)=1$ 选出其中过 $(0,1)$ 的一条（红色，$C=1$）。"
}
# ch5-sec1 / pitfall
{
 "kind": "pitfall",
 "wrong": "$y=C_1\\mathrm e^x+C_2\\mathrm e^{x}$ 是二阶方程 $y''-y=0$ 的通解，因为含有两个任意常数。",
 "why_wrong": "两个常数必须是**独立的**。$C_1\\mathrm e^x+C_2\\mathrm e^x=(C_1+C_2)\\mathrm e^x$，实际上只有一个独立常数，它不是 $y''-y=0$ 的通解。通解应为 $y=C_1\\mathrm e^x+C_2\\mathrm e^{-x}$（两个函数不成比例）。",
 "right": "通解的任意常数个数 = 阶数，且这些常数不能合并成更少的。判断独立性见 §4 的线性无关。"
}
# ch5-sec1 / example
{
 "kind": "example",
 "title": "例 1（验证通解、确定特解）",
 "problem": "验证 $y=C\\mathrm e^{2x}$ 是 $y'=2y$ 的通解，并求满足 $y(0)=3$ 的特解。",
 "steps": [
  {
   "text": "$y'=2C\\mathrm e^{2x}=2y$，对任意 $C$ 成立；方程一阶，解含一个任意常数，所以是通解。",
   "why": "代回方程，常数个数对上阶数。"
  },
  {
   "text": "$y(0)=C\\mathrm e^0=C=3$，特解 $y=3\\mathrm e^{2x}$。",
   "why": "初始条件定出常数。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec1 / example
{
 "kind": "example",
 "title": "例 2（二阶方程的通解）",
 "problem": "验证 $y=C_1\\cos x+C_2\\sin x$ 是 $y''+y=0$ 的通解。",
 "steps": [
  {
   "text": "$y'=-C_1\\sin x+C_2\\cos x$，$y''=-C_1\\cos x-C_2\\sin x=-y$，所以 $y''+y=0$ 恒成立。",
   "why": "二阶导数恰好是 $-y$。"
  },
  {
   "text": "方程二阶，解含两个任意常数 $C_1,C_2$，且 $\\cos x,\\sin x$ 不成比例（独立），所以是通解。",
   "why": "独立性：$\\sin x/\\cos x=\\tan x$ 不是常数。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec2 / pitfall
{
 "kind": "pitfall",
 "wrong": "解 $\\dfrac{\\mathrm dy}{\\mathrm dx}=2xy$ 时，$\\dfrac{\\mathrm dy}{y}=2x\\,\\mathrm dx$ 两边积分得 $\\ln y=x^2$。",
 "why_wrong": "漏了任意常数，也漏了绝对值。正确：$\\ln|y|=x^2+C_1$，$y=\\pm\\mathrm e^{C_1}\\mathrm e^{x^2}=C\\mathrm e^{x^2}$（$C$ 为任意非零常数，再把 $y\\equiv0$ 这个解并入，$C$ 取任意实数）。漏掉 $C$ 只得到一个特解，不是通解。",
 "right": "积分后立刻写 $+C$；一阶方程的通解含一个任意常数。"
}
# ch5-sec2 / example
{
 "kind": "example",
 "title": "例 1（可分离变量）",
 "problem": "求 $\\dfrac{\\mathrm dy}{\\mathrm dx}=-\\dfrac xy$ 满足 $y(0)=2$ 的特解。",
 "steps": [
  {
   "text": "分离变量：$y\\,\\mathrm dy=-x\\,\\mathrm dx$，积分 $\\dfrac{y^2}2=-\\dfrac{x^2}2+C$，即 $x^2+y^2=C'$。",
   "why": "通解是以原点为圆心的一族圆。"
  },
  {
   "text": "$y(0)=2$：$0+4=C'$，特解 $x^2+y^2=4$，由 $y(0)=2>0$ 取上半圆 $y=\\sqrt{4-x^2}$。",
   "why": "初始条件还要决定取圆的哪一支。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch5-sec2 / example
{
 "kind": "example",
 "title": "例 2（齐次方程）",
 "problem": "求 $\\dfrac{\\mathrm dy}{\\mathrm dx}=\\dfrac{x+y}{x}$ 的通解（$x>0$）。",
 "steps": [
  {
   "text": "右边 $=1+\\dfrac yx$，是齐次方程。令 $u=\\dfrac yx$，$y'=u+xu'$：$u+xu'=1+u$，$xu'=1$。",
   "why": "两边的 $u$ 抵消，变成最简单的可分离方程。"
  },
  {
   "text": "$\\mathrm du=\\dfrac{\\mathrm dx}x$，$u=\\ln x+C$。换回：$y=x(\\ln x+C)$。",
   "why": "检验：$y'=\\ln x+C+1$，右边 $\\frac{x+y}{x}=1+\\ln x+C$，一致。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec2 / example
{
 "kind": "example",
 "title": "例 3（一阶线性）",
 "problem": "求 $y'+2y=\\mathrm e^{-x}$ 的通解。",
 "steps": [
  {
   "text": "$P=2,\\ Q=\\mathrm e^{-x}$。积分因子 $\\mathrm e^{\\int2\\,\\mathrm dx}=\\mathrm e^{2x}$。",
   "why": "公式中的 $\\int P\\,\\mathrm dx$ 不再加常数。"
  },
  {
   "text": "$y=\\mathrm e^{-2x}\\left(\\int\\mathrm e^{-x}\\mathrm e^{2x}\\,\\mathrm dx+C\\right)=\\mathrm e^{-2x}(\\mathrm e^x+C)=\\mathrm e^{-x}+C\\mathrm e^{-2x}$。",
   "why": "检验：$y'+2y=(-\\mathrm e^{-x}-2C\\mathrm e^{-2x})+(2\\mathrm e^{-x}+2C\\mathrm e^{-2x})=\\mathrm e^{-x}$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec2 / example
{
 "kind": "example",
 "title": "例 4（带初始条件的线性方程）",
 "problem": "求 $y'+\\dfrac yx=x^2$（$x>0$）满足 $y(1)=1$ 的特解。",
 "steps": [
  {
   "text": "$P=\\dfrac1x$，积分因子 $\\mathrm e^{\\int\\frac1x\\mathrm dx}=x$。方程两边乘 $x$：$(xy)'=x^3$，$xy=\\dfrac{x^4}4+C$，$y=\\dfrac{x^3}4+\\dfrac Cx$。",
   "why": "积分因子让左边变成乘积的导数。"
  },
  {
   "text": "$y(1)=\\dfrac14+C=1$，$C=\\dfrac34$。特解 $y=\\dfrac{x^3}4+\\dfrac3{4x}$。",
   "why": "代入初始条件定 $C$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec3 / pitfall
{
 "kind": "pitfall",
 "wrong": "方程不显含 $x$（如 $yy''-y'^2=0$）时，也令 $y''=\\dfrac{\\mathrm dp}{\\mathrm dx}$ 来化简。",
 "why_wrong": "$p=y'$ 此时含有 $y$，$\\dfrac{\\mathrm dp}{\\mathrm dx}$ 仍是二阶问题，没有降阶。必须把 $p$ 当作 $y$ 的函数：$y''=p\\dfrac{\\mathrm dp}{\\mathrm dy}$，才得到关于 $p,y$ 的一阶方程。",
 "right": "缺 $x$：$y''=p\\,\\dfrac{\\mathrm dp}{\\mathrm dy}$；缺 $y$：$y''=\\dfrac{\\mathrm dp}{\\mathrm dx}$。"
}
# ch5-sec3 / example
{
 "kind": "example",
 "title": "例 1（$y''=f(x)$，带初值）",
 "problem": "求 $y''=6x$ 满足 $y(0)=1,\\ y'(0)=0$ 的特解。",
 "steps": [
  {
   "text": "$y'=3x^2+C_1$，$y'(0)=C_1=0$；$y=x^3+C_2$，$y(0)=C_2=1$。",
   "why": "每积分一次立刻用对应的初始条件定常数，比最后一起定更省力。"
  },
  {
   "text": "特解 $y=x^3+1$。",
   "why": "检验：$y''=6x$ ✓，$y(0)=1$ ✓，$y'(0)=0$ ✓。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算"
  }
 ]
}
# ch5-sec3 / example
{
 "kind": "example",
 "title": "例 2（不显含 $y$）",
 "problem": "求 $xy''+y'=0$（$x>0$）的通解。",
 "steps": [
  {
   "text": "令 $p=y'$，$y''=p'$：$xp'+p=0$，即 $(xp)'=0$，$xp=C_1$，$p=\\dfrac{C_1}x$。",
   "why": "方程里没有 $y$，只有 $y',y''$。"
  },
  {
   "text": "$y=\\int\\dfrac{C_1}x\\,\\mathrm dx=C_1\\ln x+C_2$。",
   "why": "再积分一次，出现第二个常数。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec3 / example
{
 "kind": "example",
 "title": "例 3（不显含 $x$）",
 "problem": "求 $y\\,y''-(y')^2=0$ 的通解。",
 "steps": [
  {
   "text": "令 $p=y'$，$y''=p\\dfrac{\\mathrm dp}{\\mathrm dy}$：$y\\,p\\dfrac{\\mathrm dp}{\\mathrm dy}-p^2=0$，即 $p\\left(y\\dfrac{\\mathrm dp}{\\mathrm dy}-p\\right)=0$。",
   "why": "把 $y$ 当自变量、$p$ 当未知函数。"
  },
  {
   "text": "$p\\neq0$ 时 $\\dfrac{\\mathrm dp}p=\\dfrac{\\mathrm dy}y$，$p=C_1y$，即 $y'=C_1y$，$y=C_2\\mathrm e^{C_1x}$。",
   "why": "$p=0$ 对应 $y=$ 常数，已包含在 $C_1=0$ 的情形里。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec4 / pitfall
{
 "kind": "pitfall",
 "wrong": "$y_1=\\mathrm e^x,\\ y_2=2\\mathrm e^x$ 是齐次方程 $y''-y=0$ 的两个解，所以 $y=C_1y_1+C_2y_2$ 是它的通解。",
 "why_wrong": "$y_2/y_1=2$ 是常数，二者线性相关。$C_1\\mathrm e^x+2C_2\\mathrm e^x=(C_1+2C_2)\\mathrm e^x$ 只有一个独立常数，不是二阶方程的通解。要取线性无关的解，如 $\\mathrm e^x$ 与 $\\mathrm e^{-x}$（比值 $\\mathrm e^{-2x}$ 不是常数）。",
 "right": "通解需要**线性无关**的两个解；先用比值是否为常数检验。"
}
# ch5-sec4 / example
{
 "kind": "example",
 "title": "例 1（由两个解写通解）",
 "problem": "验证 $y_1=\\mathrm e^x,\\ y_2=\\mathrm e^{2x}$ 是 $y''-3y'+2y=0$ 的线性无关解，并写出通解。",
 "steps": [
  {
   "text": "$y_1$：$1-3+2=0$ ✓；$y_2=\\mathrm e^{2x}$：$4-3\\cdot2+2=0$ ✓。",
   "why": "代入方程：$y''-3y'+2y$ 对 $\\mathrm e^{rx}$ 的值是 $(r^2-3r+2)\\mathrm e^{rx}$。"
  },
  {
   "text": "$\\dfrac{y_2}{y_1}=\\mathrm e^x$ 不是常数，线性无关。通解 $y=C_1\\mathrm e^x+C_2\\mathrm e^{2x}$。",
   "why": "两个线性无关的解，通解结构定理。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec4 / example
{
 "kind": "example",
 "title": "例 2（非齐次方程的通解结构）",
 "problem": "已知 $y^*=x$ 是 $y''-3y'+2y=2x-3$ 的一个特解，求通解。",
 "steps": [
  {
   "text": "验证特解：$y^*=x$，$y^{*\\prime}=1,\\ y^{*\\prime\\prime}=0$：$0-3+2x=2x-3$ ✓。",
   "why": "确认它真的是特解。"
  },
  {
   "text": "通解 $y=Y+y^*=C_1\\mathrm e^x+C_2\\mathrm e^{2x}+x$（$Y$ 来自例 1）。",
   "why": "非齐次通解 = 齐次通解 + 一个特解。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch5-sec5 / figure
{
 "kind": "figure",
 "file": "ch5-sec5-roots.svg",
 "caption": "三类特征根对应的解的形状：不等实根（指数函数的组合）、二重根（带 $x$ 的因子，先升后降）、共轭复根（振荡，包络线是 $\\pm\\mathrm e^{\\alpha x}$；$\\alpha<0$ 时衰减）。"
}
# ch5-sec5 / pitfall
{
 "kind": "pitfall",
 "wrong": "$y''-4y'+4y=0$ 的特征方程有二重根 $r=2$，通解是 $y=C\\mathrm e^{2x}$。",
 "why_wrong": "二重根只给出一个解 $\\mathrm e^{2x}$，二阶方程需要两个线性无关的解。另一个解是 $x\\mathrm e^{2x}$（可代入验证），所以通解 $y=(C_1+C_2x)\\mathrm e^{2x}$。若只写一项，常数个数少于阶数。",
 "right": "二重根：$(C_1+C_2x)\\mathrm e^{rx}$，两个任意常数。"
}
# ch5-sec5 / example
{
 "kind": "example",
 "title": "例 1（三类特征根）",
 "problem": "求下列方程的通解：(1) $y''-3y'+2y=0$；(2) $y''-4y'+4y=0$；(3) $y''+2y'+5y=0$。",
 "steps": [
  {
   "text": "(1) $r^2-3r+2=0$，$r=1,2$。$y=C_1\\mathrm e^x+C_2\\mathrm e^{2x}$。",
   "why": "两个不等实根。"
  },
  {
   "text": "(2) $r^2-4r+4=(r-2)^2=0$，二重根 $r=2$。$y=(C_1+C_2x)\\mathrm e^{2x}$。",
   "why": "二重根要补上 $x$ 因子。"
  },
  {
   "text": "(3) $r^2+2r+5=0$，$r=-1\\pm2\\mathrm i$，$\\alpha=-1,\\beta=2$。$y=\\mathrm e^{-x}(C_1\\cos2x+C_2\\sin2x)$。",
   "why": "复根的实部进指数，虚部进三角函数。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，三个通解均已用 sympy 代回验证"
  }
 ]
}
# ch5-sec5 / example
{
 "kind": "example",
 "title": "例 2（非齐次，选学：$\\lambda$ 是单根）",
 "problem": "求 $y''-3y'+2y=\\mathrm e^x$ 的通解。",
 "steps": [
  {
   "text": "齐次通解 $Y=C_1\\mathrm e^x+C_2\\mathrm e^{2x}$。$f=\\mathrm e^x$，$\\lambda=1$，$P_0=1$（零次）。",
   "why": "$\\lambda=1$ 是特征方程的**单根**，取 $k=1$。"
  },
  {
   "text": "设 $y^*=Ax\\mathrm e^x$：$y^{*\\prime}=A(1+x)\\mathrm e^x,\\ y^{*\\prime\\prime}=A(2+x)\\mathrm e^x$，代入：$A\\left[(2+x)-3(1+x)+2x\\right]\\mathrm e^x=-A\\mathrm e^x=\\mathrm e^x$，$A=-1$。",
   "why": "$x$ 项抵消，只剩常数项；若误设 $A\\mathrm e^x$ 会得到 $0=1$ 的矛盾。"
  },
  {
   "text": "通解 $y=C_1\\mathrm e^x+C_2\\mathrm e^{2x}-x\\mathrm e^x$。",
   "why": "已用 sympy 代回验证。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 代回验证"
  }
 ]
}
# ch6-sec1 / figure
{
 "kind": "figure",
 "file": "ch6-sec1-partial-sums.svg",
 "caption": "两个级数的部分和：$\\sum\\frac1{n^2}$ 的部分和趋于 $\\frac{\\pi^2}{6}\\approx1.645$（收敛）；$\\sum\\frac1n$ 的通项也趋于 0，但部分和像 $\\ln n$ 一样无限增长（发散）。"
}
# ch6-sec1 / pitfall
{
 "kind": "pitfall",
 "wrong": "$\\displaystyle\\lim_{n\\to\\infty}u_n=0$，所以级数 $\\sum u_n$ 收敛。",
 "why_wrong": "$u_n\\to0$ 只是**必要**条件，不是充分条件。调和级数 $\\sum\\dfrac1n$ 的通项趋于 0，却发散：$\\dfrac1n$ 虽然小，加起来的速度仍使部分和像 $\\ln n$ 一样无界。",
 "right": "用法：$u_n\\not\\to0$ $\\Rightarrow$ 发散（有效）；$u_n\\to0$ 则**无结论**，必须用别的方法（比较、比值、$p$ 级数等）。"
}
# ch6-sec1 / example
{
 "kind": "example",
 "title": "例 1（裂项求和）",
 "problem": "求 $\\displaystyle\\sum_{n=1}^\\infty\\frac1{n(n+1)}$ 的和。",
 "steps": [
  {
   "text": "裂项：$\\dfrac1{n(n+1)}=\\dfrac1n-\\dfrac1{n+1}$。",
   "why": "把一项拆成两项之差，使得相邻项抵消。"
  },
  {
   "text": "$S_n=\\left(1-\\dfrac12\\right)+\\left(\\dfrac12-\\dfrac13\\right)+\\cdots+\\left(\\dfrac1n-\\dfrac1{n+1}\\right)=1-\\dfrac1{n+1}\\to1$。",
   "why": "中间的项两两抵消，只剩首尾。"
  },
  {
   "text": "级数收敛，和为 1。",
   "why": "$\\lim S_n=1$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 求和验证"
  }
 ]
}
# ch6-sec1 / example
{
 "kind": "example",
 "title": "例 2（几何级数）",
 "problem": "求 (1) $\\displaystyle\\sum_{n=0}^\\infty\\left(\\frac13\\right)^n$；(2) $\\displaystyle\\sum_{n=1}^\\infty\\frac2{3^n}$。",
 "steps": [
  {
   "text": "(1) 首项 $a=1$，公比 $q=\\frac13$，$|q|<1$：和 $=\\dfrac1{1-\\frac13}=\\dfrac32$。",
   "why": "几何级数求和公式 $a/(1-q)$，$a$ 是**第一项**。"
  },
  {
   "text": "(2) 首项（$n=1$）$a=\\dfrac23$，公比 $\\dfrac13$：和 $=\\dfrac{2/3}{1-1/3}=1$。",
   "why": "起始下标是 1，首项不是 $2$ 而是 $2/3$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 求和验证"
  }
 ]
}
# ch6-sec1 / example
{
 "kind": "example",
 "title": "例 3（用必要条件判发散）",
 "problem": "判断 $\\displaystyle\\sum_{n=1}^\\infty\\frac n{n+1}$ 的敛散性。",
 "steps": [
  {
   "text": "$u_n=\\dfrac n{n+1}\\to1\\neq0$。",
   "why": "先检查通项的极限。"
  },
  {
   "text": "通项不趋于 0，由必要条件的逆否命题，级数**发散**。",
   "why": "不需要再用别的判别法。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造；必要条件的使用"
  }
 ]
}
# ch6-sec2 / pitfall
{
 "kind": "pitfall",
 "wrong": "比值判别法求得 $\\rho=1$，所以级数发散（或收敛）。",
 "why_wrong": "$\\rho=1$ 时比值法**没有结论**。$\\sum\\dfrac1n$（发散）与 $\\sum\\dfrac1{n^2}$（收敛）的比值极限都是 1：$\\dfrac{1/(n+1)}{1/n}=\\dfrac n{n+1}\\to1$，$\\dfrac{n^2}{(n+1)^2}\\to1$。",
 "right": "$\\rho=1$ 时改用比较判别法（与 $p$ 级数比）、积分判别或其他方法。"
}
# ch6-sec2 / example
{
 "kind": "example",
 "title": "例 1（比值判别法）",
 "problem": "判断 $\\displaystyle\\sum_{n=1}^\\infty\\frac n{2^n}$ 的敛散性。",
 "steps": [
  {
   "text": "$\\dfrac{u_{n+1}}{u_n}=\\dfrac{(n+1)/2^{n+1}}{n/2^n}=\\dfrac{n+1}{2n}\\to\\dfrac12$。",
   "why": "通项含 $2^n$，比值法合适。"
  },
  {
   "text": "$\\rho=\\dfrac12<1$，级数**收敛**。",
   "why": "通项含 $2^n$（指数），比值法最直接；前几项 $\\frac12,\\frac24,\\frac38,\\frac4{16},\\dots$ 也确实在快速变小。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，极限已用 sympy 复核"
  }
 ]
}
# ch6-sec2 / example
{
 "kind": "example",
 "title": "例 2（比较判别法）",
 "problem": "判断 $\\displaystyle\\sum_{n=1}^\\infty\\frac1{n^2+1}$ 的敛散性。",
 "steps": [
  {
   "text": "$0<\\dfrac1{n^2+1}<\\dfrac1{n^2}$，而 $\\sum\\dfrac1{n^2}$ 是 $p=2>1$ 的 $p$ 级数，收敛。",
   "why": "放大分母变小：通项小于一个收敛级数的通项。"
  },
  {
   "text": "由比较判别法，$\\sum\\dfrac1{n^2+1}$ **收敛**。",
   "why": "也可用极限形式：$\\lim\\frac{1/(n^2+1)}{1/n^2}=1\\in(0,\\infty)$，同敛散。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造；比较判别法"
  }
 ]
}
# ch6-sec2 / example
{
 "kind": "example",
 "title": "例 3（绝对收敛与条件收敛）",
 "problem": "判断 (1) $\\displaystyle\\sum_{n=1}^\\infty\\frac{(-1)^{n-1}}n$；(2) $\\displaystyle\\sum_{n=1}^\\infty\\frac{(-1)^{n-1}}{n^2}$ 是绝对收敛、条件收敛还是发散。",
 "steps": [
  {
   "text": "(1) 交错级数，$\\frac1n$ 单调减且 $\\to0$，由莱布尼茨判别法收敛。但 $\\sum\\left|\\frac{(-1)^{n-1}}n\\right|=\\sum\\frac1n$ 发散。所以**条件收敛**。",
   "why": "收敛靠正负相消，去掉符号就发散。"
  },
  {
   "text": "(2) 同样收敛；$\\sum\\frac1{n^2}$ 收敛，所以**绝对收敛**。",
   "why": "绝对收敛比条件收敛强。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造；绝对收敛与条件收敛的经典对照"
  }
 ]
}
# ch6-sec3 / figure
{
 "kind": "figure",
 "file": "ch6-sec3-geometric.svg",
 "caption": "几何级数 $\\sum x^n$ 的部分和（彩色曲线）与和函数 $\\frac1{1-x}$（黑色）。在收敛区间 $(-1,1)$（浅蓝带）内，项数越多，曲线越贴近 $\\frac1{1-x}$；区间之外（如 $x<-1$），部分和越来越偏离。"
}
# ch6-sec3 / pitfall
{
 "kind": "pitfall",
 "wrong": "收敛半径是 $R$，所以收敛域就是 $[-R,R]$ 或 $(-R,R)$，不用再判断端点。",
 "why_wrong": "端点的敛散性与 $R$ 无关，必须逐个检验。例：$\\sum\\dfrac{x^n}n$，$R=1$；$x=1$ 时是调和级数，发散；$x=-1$ 时是交错级数 $\\sum\\dfrac{(-1)^n}n$，收敛。收敛域是 $[-1,1)$，一端含一端不含。",
 "right": "求出 $R$ 后，把 $x=R$ 与 $x=-R$ 分别代入，用数项级数的判别法判断。"
}
# ch6-sec3 / example
{
 "kind": "example",
 "title": "例 1（收敛半径与收敛域）",
 "problem": "求 $\\displaystyle\\sum_{n=1}^\\infty\\frac{x^n}n$ 的收敛域。",
 "steps": [
  {
   "text": "$a_n=\\dfrac1n$，$R=\\lim\\left|\\dfrac{a_n}{a_{n+1}}\\right|=\\lim\\dfrac{n+1}n=1$。收敛区间 $(-1,1)$。",
   "why": "先求半径。"
  },
  {
   "text": "$x=1$：调和级数，发散。$x=-1$：$\\sum\\dfrac{(-1)^n}n$，交错级数，莱布尼茨判别收敛。",
   "why": "端点逐个检验。"
  },
  {
   "text": "收敛域 $[-1,1)$。",
   "why": "含 $-1$，不含 $1$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造；极限已用 sympy 复核"
  }
 ]
}
# ch6-sec3 / example
{
 "kind": "example",
 "title": "例 2（收敛半径为 $\\infty$）",
 "problem": "求 $\\displaystyle\\sum_{n=0}^\\infty\\frac{x^n}{n!}$ 的收敛半径。",
 "steps": [
  {
   "text": "$R=\\lim\\left|\\dfrac{1/n!}{1/(n+1)!}\\right|=\\lim(n+1)=+\\infty$。",
   "why": "阶乘增长极快。"
  },
  {
   "text": "收敛域是整条数轴 $(-\\infty,+\\infty)$。这个级数就是 $\\mathrm e^x$ 的展开式（下一节）。",
   "why": "$R=\\infty$ 时没有端点要检验。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造；极限已用 sympy 复核"
  }
 ]
}
# ch6-sec3 / example
{
 "kind": "example",
 "title": "例 3（用逐项求导求和函数）",
 "problem": "求 $\\displaystyle\\sum_{n=1}^\\infty nx^{n-1}$ 的和函数，并求 $x=\\dfrac12$ 时的值。",
 "steps": [
  {
   "text": "$\\displaystyle\\sum_{n=1}^\\infty nx^{n-1}=\\left(\\sum_{n=0}^\\infty x^n\\right)'=\\left(\\dfrac1{1-x}\\right)'=\\dfrac1{(1-x)^2}$，$|x|<1$。",
   "why": "逐项求导，收敛半径不变，仍是 1。"
  },
  {
   "text": "$x=\\dfrac12$：$\\dfrac1{(1/2)^2}=4$。",
   "why": "检验前几项：$1+2\\cdot\\frac12+3\\cdot\\frac14+4\\cdot\\frac18+\\cdots$，$1+1+0.75+0.5+0.3125+\\cdots$ 趋于 4。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已用 sympy 复核"
  }
 ]
}
# ch6-sec4 / pitfall
{
 "kind": "pitfall",
 "wrong": "$\\dfrac1{1+x^2}=1+x^2+x^4+\\cdots$（直接套 $\\dfrac1{1-x}$ 的展开式，把 $x$ 换成 $x^2$）。",
 "why_wrong": "代换要和原式一致。$\\dfrac1{1-u}=\\sum u^n$ 里的 $u$ 要使 $1-u=1+x^2$，即 $u=-x^2$。所以 $\\dfrac1{1+x^2}=\\sum(-x^2)^n=1-x^2+x^4-x^6+\\cdots$，符号**交替**，范围 $|x|<1$。把 $u$ 取成 $x^2$ 得到的是 $\\dfrac1{1-x^2}$ 的展开式。",
 "right": "先把函数写成 $\\dfrac1{1-u}$ 的形式，找出 $u$，再代入 $\\sum u^n$。"
}
# ch6-sec4 / example
{
 "kind": "example",
 "title": "例 1（代换）",
 "problem": "把 $\\dfrac1{1+x^2}$ 与 $\\mathrm e^{-x^2}$ 展开成 $x$ 的幂级数。",
 "steps": [
  {
   "text": "$\\dfrac1{1+x^2}=\\dfrac1{1-(-x^2)}=\\displaystyle\\sum_{n=0}^\\infty(-x^2)^n=\\sum_{n=0}^\\infty(-1)^nx^{2n}$，$|x|<1$。",
   "why": "令 $u=-x^2$，要求 $|u|<1$ 即 $|x|<1$。"
  },
  {
   "text": "$\\mathrm e^{-x^2}=\\displaystyle\\sum_{n=0}^\\infty\\frac{(-x^2)^n}{n!}=\\sum_{n=0}^\\infty\\frac{(-1)^nx^{2n}}{n!}=1-x^2+\\frac{x^4}{2}-\\cdots$，$x\\in(-\\infty,+\\infty)$。",
   "why": "$\\mathrm e^u$ 对一切 $u$ 成立，所以代换后对一切 $x$ 成立。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，前几项已用 sympy 复核"
  }
 ]
}
# ch6-sec4 / example
{
 "kind": "example",
 "title": "例 2（逐项积分）",
 "problem": "把 $\\arctan x$ 展开成 $x$ 的幂级数。",
 "steps": [
  {
   "text": "$(\\arctan x)'=\\dfrac1{1+x^2}=\\sum_{n=0}^\\infty(-1)^nx^{2n}$，$|x|<1$。",
   "why": "先求导，得到已知的展开式（例 1）。"
  },
  {
   "text": "逐项积分（$\\arctan0=0$）：$\\arctan x=\\displaystyle\\sum_{n=0}^\\infty\\frac{(-1)^nx^{2n+1}}{2n+1}=x-\\frac{x^3}3+\\frac{x^5}5-\\cdots$，$|x|<1$（端点 $x=\\pm1$ 也收敛，成立范围 $[-1,1]$）。",
   "why": "取 $x=1$：$\\frac\\pi4=1-\\frac13+\\frac15-\\cdots$，莱布尼茨级数。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，前几项已用 sympy 复核"
  }
 ]
}
# ch6-sec4 / example
{
 "kind": "example",
 "title": "例 3（近似计算）",
 "problem": "用前两项估计 $\\sin0.1$，并估计误差。",
 "steps": [
  {
   "text": "$\\sin x=x-\\dfrac{x^3}{6}+\\dfrac{x^5}{120}-\\cdots$。取前两项：$\\sin0.1\\approx0.1-\\dfrac{0.001}{6}=0.0998333\\cdots$。",
   "why": "代入 $x=0.1$。"
  },
  {
   "text": "这是交错级数，误差小于第一个舍去的项的绝对值 $\\dfrac{0.1^5}{120}\\approx8.3\\times10^{-8}$。",
   "why": "交错级数的余项不超过首项被舍去项的大小。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，已复算（sin 0.1 = 0.0998334166…）"
  }
 ]
}
# ch6-sec5 / figure
{
 "kind": "figure",
 "file": "ch6-sec5-fourier.svg",
 "caption": "$f(x)=x$（$-\\pi<x<\\pi$，按周期 $2\\pi$ 延拓）的傅里叶级数 $2\\sum(-1)^{n+1}\\frac{\\sin nx}n$ 的部分和：项数增加，在内部越来越贴近 $y=x$；在端点 $x=\\pm\\pi$（延拓后的间断点）收敛到 0，即左右极限 $\\pm\\pi$ 的平均值。"
}
# ch6-sec5 / pitfall
{
 "kind": "pitfall",
 "wrong": "$f(x)=x$ 的傅里叶级数在 $x=\\pi$ 处收敛于 $f(\\pi)=\\pi$。",
 "why_wrong": "$f(x)=x$ 按周期 $2\\pi$ 延拓后，在 $x=\\pi$ 处有**跳跃**：左极限 $\\pi$，右极限 $-\\pi$（下一个周期从 $-\\pi$ 开始）。间断点处级数收敛于左右极限的平均 $\\dfrac{\\pi+(-\\pi)}2=0$，而不是函数在该点的值。事实上级数 $2\\sum(-1)^{n+1}\\frac{\\sin n\\pi}{n}$ 的每一项都是 0。",
 "right": "间断点：收敛于 $\\dfrac{f(x^-)+f(x^+)}2$；连续点：收敛于 $f(x)$。"
}
# ch6-sec5 / example
{
 "kind": "example",
 "title": "例 1（奇函数）",
 "problem": "把 $f(x)=x\\ (-\\pi<x<\\pi)$ 展开成傅里叶级数（周期 $2\\pi$）。",
 "steps": [
  {
   "text": "$f$ 是奇函数：$a_n=0$（$n=0,1,2,\\dots$）。",
   "why": "$x\\cos nx$ 是奇函数，对称区间积分为 0。"
  },
  {
   "text": "$b_n=\\dfrac1\\pi\\displaystyle\\int_{-\\pi}^\\pi x\\sin nx\\,\\mathrm dx=\\dfrac2\\pi\\int_0^\\pi x\\sin nx\\,\\mathrm dx=\\dfrac{2(-1)^{n+1}}n$。",
   "why": "分部积分：$\\int_0^\\pi x\\sin nx\\,\\mathrm dx=-\\frac{\\pi\\cos n\\pi}n$。$b_1=2$，$b_2=-1$，$b_3=\\frac23$。"
  },
  {
   "text": "$x=2\\displaystyle\\sum_{n=1}^\\infty\\frac{(-1)^{n+1}}n\\sin nx=2\\left(\\sin x-\\frac{\\sin2x}2+\\frac{\\sin3x}3-\\cdots\\right)$，$-\\pi<x<\\pi$。",
   "why": "在 $x=\\pm\\pi$（间断点）处级数的和是 0，不是 $\\pm\\pi$。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，傅里叶系数已用 sympy 积分复核"
  }
 ]
}
# ch6-sec5 / example
{
 "kind": "example",
 "title": "例 2（偶函数）",
 "problem": "把 $f(x)=|x|\\ (-\\pi\\le x\\le\\pi)$ 展开成傅里叶级数，并由此求 $\\displaystyle\\sum_{k=0}^\\infty\\frac1{(2k+1)^2}$。",
 "steps": [
  {
   "text": "$f$ 是偶函数：$b_n=0$。$a_0=\\dfrac2\\pi\\displaystyle\\int_0^\\pi x\\,\\mathrm dx=\\pi$，$a_n=\\dfrac2\\pi\\int_0^\\pi x\\cos nx\\,\\mathrm dx=\\dfrac{2\\left[(-1)^n-1\\right]}{\\pi n^2}$。",
   "why": "$n$ 为偶数时 $a_n=0$，$n$ 为奇数时 $a_n=-\\dfrac4{\\pi n^2}$。"
  },
  {
   "text": "$|x|=\\dfrac\\pi2-\\dfrac4\\pi\\displaystyle\\sum_{k=0}^\\infty\\frac{\\cos(2k+1)x}{(2k+1)^2}$，$-\\pi\\le x\\le\\pi$（$|x|$ 连续，级数处处收敛于 $|x|$）。",
   "why": "只有奇数项。"
  },
  {
   "text": "取 $x=0$：$0=\\dfrac\\pi2-\\dfrac4\\pi\\displaystyle\\sum_{k=0}^\\infty\\frac1{(2k+1)^2}$，所以 $\\displaystyle\\sum_{k=0}^\\infty\\dfrac1{(2k+1)^2}=\\dfrac{\\pi^2}8$。",
   "why": "用收敛定理（$x=0$ 是连续点）把傅里叶级数变成数项级数的求和。"
  }
 ],
 "source_refs": [
  {
   "relation": "authored",
   "note": "自造，傅里叶系数与级数和已用 sympy 复核"
  }
 ]
}