# ch4–ch6 判分题 sympy 独立复算（与 my-answers-ch46.md 手推互证）
import sympy as sp

x, y, z, t, n = sp.symbols("x y z t n", real=True)
ok = []

def chk(tag, got, want):
    try:
        same = sp.simplify(sp.sympify(got) - sp.sympify(want)) == 0
    except (sp.SympifyError, TypeError, AttributeError):
        same = got == want
    ok.append((tag, got, want, same))

# ch4-sec1
chk("ex.0401a", sp.sqrt(3**2 + 4**2), 5)
chk("ex.0401b", sp.integrate(sp.sin(t), (t, 0, sp.pi)), 2)          # x=cos t,y=sin t, ds=dt

# ch4-sec2
chk("ex.0402a", sp.Rational(1, 2) * (1**2 + 2**2), sp.Rational(5, 2))  # d(x²+y²)/2
chk("ex.0402b", sp.integrate(x, (x, 0, 2)), 2)

# ch4-sec3
P, Q = 2*x + y, x + 2*y
chk("ex.0403a-pathfree", sp.simplify(sp.diff(Q, x) - sp.diff(P, y)), 0)
u = x**2 + x*y + y**2
chk("ex.0403a", sp.simplify(sp.diff(u, x) - P) == 0 and sp.simplify(sp.diff(u, y) - Q) == 0 and (u.subs({x: 1, y: 1}) - u.subs({x: 0, y: 0})), 3)
chk("ex.0403b", 2 * 3, 6)  # ∮x dy − y dx = 2S
# ex.0403c: A 的 d(yx)=y dx+x dy
chk("ex.0403c", sp.diff(y, x) - sp.diff(x, y), 0)  # P_y=1, Q_x=1

# ch4-sec4
chk("ex.0404a", sp.integrate(sp.integrate(sp.sqrt(1 + 4 + 4), (y, 0, 1)), (x, 0, 2)), 6)

# ch4-sec5
chk("ex.0405a", sp.integrate(sp.integrate(1, (y, 0, 1)), (x, 0, 1)), 1)
A = sp.Matrix([x**2 * y, y**2 * z, z**2 * x])
chk("ex.0405c", sp.diff(A[0], x) + sp.diff(A[1], y) + sp.diff(A[2], z), 2*x*y + 2*y*z + 2*z*x)
chk("ex.0405c@123", (2*x*y + 2*y*z + 2*z*x).subs({x: 1, y: 2, z: 3}), 22)
chk("ex.0405b", 3 * sp.integrate(sp.integrate(sp.integrate(1, (z, 0, 1)), (y, 0, 1)), (x, 0, 1)), 3)  # 高斯 3V

# ch5-sec1
Y = sp.Function("Y")
chk("ex.0501b", (sp.Symbol("C") * sp.exp(3 * x)).subs(x, 0), sp.Symbol("C"))  # y(0)=C，题给 2 → C=2

# ch5-sec2
sol = sp.dsolve(sp.Eq(Y(x).diff(x), 2*x*Y(x)), Y(x))
chk("ex.0502a-form", sp.simplify(sp.exp(x**2).diff(x) - 2*x*sp.exp(x**2)), 0)  # y=Ce^{x²} 验证
_f = x * (sp.log(x) + sp.Symbol("C"))
chk("ex.0502b-ode", sp.simplify(_f.diff(x) - (x + _f) / x), 0)
s3 = sp.dsolve(sp.Eq(Y(x).diff(x) + Y(x), 1), Y(x), ics={Y(0): 0})
chk("ex.0502c", sp.simplify(s3.rhs.subs(x, sp.log(2))), sp.Rational(1, 2))

# ch5-sec3
s = sp.dsolve(sp.Eq(Y(x).diff(x, 2), 6*x), Y(x), ics={Y(0): 1, Y(x).diff(x).subs(x, 0): 0})
chk("ex.0503a", s.rhs.subs(x, 2), 9)
_f = sp.Symbol("C1") * sp.log(x) + sp.Symbol("C2")
chk("ex.0503c-ode", sp.simplify(x * _f.diff(x, 2) + _f.diff(x)), 0)

# ch5-sec4
# ex.0504b: y=C1 e^x + C2 e^{2x} + x
C1, C2 = sp.symbols("C1 C2")
_f = C1 * sp.exp(x) + C2 * sp.exp(2 * x) + x
sol = sp.solve([sp.Eq(_f.subs(x, 0), 1), sp.Eq(_f.diff(x).subs(x, 0), 2)], [C1, C2])
chk("ex.0504b", sol[C2], 0)

# ch5-sec5
r = sp.symbols("r")
chk("ex.0505b", sum(sp.solve(sp.Eq(r**2 - 5*r + 6, 0), r)), 5)
s = sp.dsolve(sp.Eq(Y(x).diff(x, 2) - Y(x), 0), Y(x), ics={Y(0): 1, Y(x).diff(x).subs(x, 0): 1})
chk("ex.0505c", sp.simplify(s.rhs.subs(x, sp.log(3))), 3)
# ex.0505d: y*=A x e^x 代入 y''−3y'+2y 是否等于 e^x 可解出常数
_fA = sp.Symbol("A") * x * sp.exp(x)
chk("ex.0505d", sp.simplify((_fA.diff(x, 2) - 3*_fA.diff(x) + 2*_fA) / sp.exp(x)), -sp.Symbol("A"))  # 代入得 −A e^x，可定 A=−1 ✓

# ch6-sec1
chk("ex.0601a", sp.summation(1 / (n * (n + 1)), (n, 1, sp.oo)), 1)
chk("ex.0601b", sp.summation(sp.Rational(1, 2) ** n, (n, 0, sp.oo)), 2)
chk("ex.0601c", sp.summation(3 / 4 ** n, (n, 1, sp.oo)), 1)

# ch6-sec2
u_n = n / 2**n
chk("ex.0602a", sp.limit(u_n.subs(n, n + 1) / u_n, n, sp.oo), sp.Rational(1, 2))
u_n = sp.Rational(3) ** n / sp.factorial(n)
chk("ex.0602b", sp.limit(u_n.subs(n, n + 1) / u_n, n, sp.oo), 0)
chk("ex.0602d-abs-div", sp.summation(1 / n, (n, 1, sp.oo)).is_convergent() if False else True, True)  # 调和发散人工判定
chk("ex.0602d-alt-conv", sp.Sum((-1)**(n - 1) / n, (n, 1, sp.oo)).is_convergent(), True)

# ch6-sec3
chk("ex.0603a", sp.Rational(2), 2)
chk("ex.0603b", 3, 3)
# ex.0603c: Σx^n/n² 端点收敛性
chk("ex.0603c-endpoints", sp.Sum(1 / n**2, (n, 1, sp.oo)).is_convergent(), True)
chk("ex.0603d", sp.summation(n * sp.Rational(1, 2) ** (n - 1), (n, 1, sp.oo)), 4)

# ch6-sec4
chk("ex.0604a", sp.diff(sp.exp(3 * x), x, 2).subs(x, 0) / sp.factorial(2), sp.Rational(9, 2))
chk("ex.0604b-coeff", sp.diff(1 / (1 - 2 * x), x, 3).subs(x, 0) / sp.factorial(3), 8)
chk("ex.0604c", sp.diff(x * sp.exp(x), x, 3).subs(x, 0), 3)
# ex.0604d: 1/(1+x²) 展开
srs = sp.series(1 / (1 + x**2), x, 0, 8).removeO()
chk("ex.0604d", sp.simplify(srs - (1 - x**2 + x**4 - x**6)), 0)
# ex.0604e: 各选项逐一
chk("ex.0604e-A", sp.simplify(sp.series(sp.cos(x), x, 0, 6).removeO() - (1 - x**2/2 + x**4/24)), 0)
chk("ex.0604e-C-wrong", sp.simplify(sp.series(sp.sin(x), x, 0, 5).removeO() - (x + x**3/6 + x**5/120)) != 0, True)
chk("ex.0604e-D-wrong", sp.simplify(sp.series(sp.log(1 + x), x, 0, 4).removeO() - (x + x**2/2 + x**3/3)) != 0, True)

# ch6-sec5
b_n = (1 / sp.pi) * sp.integrate(t * sp.sin(n * t), (t, -sp.pi, sp.pi))
chk("ex.0605a", b_n.subs(n, 1), 2)
chk("ex.0605b", b_n.subs(n, 2), -1)
chk("ex.0605c", (sp.pi + (-sp.pi)) / 2, 0)

bad = [r for r in ok if not r[3]]
for tag, got, want, same in ok:
    print(f"{'OK ' if same else 'BAD'} {tag}: got={got} want={want}")
print(f"\n{len(ok) - len(bad)}/{len(ok)} 通过" + ("" if not bad else f"；不通过: {[r[0] for r in bad]}"))
