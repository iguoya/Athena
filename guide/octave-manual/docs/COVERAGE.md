# 覆盖表：Octave 手册 → 线代与高数

手册（钉 `release-8-4-0`）有 40 多章、上千个函数，是参考手册而不是教程。本应用按「用 Octave 学线性代数与高等数学」裁剪，
并分两档（使用者的要求：**前期简明扼要、有成果有成就感，后期再加知识量与复杂度**）：

- **基础**（`functions`，共 90 个）：界面默认只显示这些。每页只留最常用的几个函数，配「试一试」。
- **进阶**（`functions_more`，共 149 个）：译文与练习都已入库，界面默认折叠，侧栏「内容深度」切到「进阶」或点页首提示即可展开。

没列在这张表里的函数、没取的节不进课表，也不留占位。页序是学习顺序，不是手册章序。

| 页 | 手册章 | 取的节 | 基础函数 | 进阶函数 |
|---|---|---|---|---|
| numbers（数值类型与矩阵） | `numbers.txi` | Matrices、Ranges、Logical Values、Predicates for Numeric Objects | logical ismatrix isvector isscalar issquare issymmetric | double true false isnumeric islogical isfloat isreal iscomplex isrow iscolumn ishermitian isdefinite isdiag istril istriu |
| expr（表达式与运算符） | `expr.txi` | Index Expressions、Arithmetic Operators、Comparison Operators、Boolean Expressions、Assignment Expressions、Operator Precedence | sub2ind ind2sub mldivide isequal | mrdivide mpower mtimes times power rdivide transpose ctranspose and or not |
| matrix（矩阵的构造与变形） | `matrix.txi` | Finding Elements and Checking Conditions、Rearranging Matrices、Special Utility Matrices、Famous Matrices | any all find reshape sort diag eye ones zeros linspace magic | diff isinf isnan fliplr flipud flip rot90 cat horzcat vertcat permute circshift tril triu vec blkdiag repmat logspace rand randi randn hilb vander toeplitz pascal |
| arith（算术与初等函数） | `arith.txi` | Exponents and Logarithms、Complex Arithmetic、Trigonometry、Sums and Products、Utility Functions、Special Functions、Coordinate Transformations、Mathematical Constants | exp log sqrt abs sin cos tan sum prod cumsum floor round max min dot cross factorial mod e pi Inf NaN eps | log10 log2 nthroot arg conj imag real deg2rad rad2deg asin acos atan sinh cosh tanh atan2 sind cosd cumprod sumsq ceil fix hypot gradient factor gcd lcm rem primes sign gamma erf beta cart2pol pol2cart I |
| vectorize（向量化与广播） | `vectorize.txi` | Basic Vectorization、Broadcasting、Function Application、Miscellaneous Techniques、Examples | bsxfun arrayfun |  |
| plot（绘图） | `plot.txi` | Introduction to Plotting、High-Level Plotting | plot contour axis mesh surf meshgrid title legend xlabel grid subplot figure hold print | semilogx semilogy loglog bar hist stairs stem scatter contourf polar xlim fill area fplot ezplot meshc surfc plot3 view contour3 quiver sombrero peaks scatter3 waterfall text clabel colorbar clf close saveas |
| linalg（线性代数） | `linalg.txi` | Techniques Used for Linear Algebra、Basic Matrix Functions、Matrix Factorizations、Functions of a Matrix | det eig inv norm null orth rank trace rref chol lu qr svd | linsolve pinv rcond cond vecnorm schur expm logm sqrtm kron |
| poly（多项式与拟合） | `poly.txi` | Evaluating Polynomials、Finding Roots、Products of Polynomials、Derivatives / Integrals / Transforms、Polynomial Interpolation、Miscellaneous Functions | polyval roots conv polyder polyint polyfit | polyvalm compan deconv polygcd residue poly polyout polyreduce |
| interp（插值） | `interp.txi` | One-dimensional Interpolation、Multi-dimensional Interpolation | interp1 spline | interp2 |
| quad（数值积分） | `quad.txi` | Functions of One Variable、Functions of Multiple Variables | quad quadgk integral trapz | quadv quadl quadcc cumtrapz dblquad integral2 integral3 |
| diffeq（常微分方程） | `diffeq.txi` | Ordinary Differential Equations、Matlab-compatible solvers | ode45 odeset | lsode ode23 odeget |
| nonlin（方程求根与最优化） | `nonlin.txi` | Solvers、Minimizers | fsolve fzero fminsearch | fminbnd fminunc |

## 整章裁掉的内容与理由

- 与线代、高数无关：字符串、容器（cell、struct）、文件与输入输出、音频、图像、几何（Delaunay 等）、稀疏矩阵、信号处理、统计与随机分布、包管理、调试与测试、外部代码接口、GUI。
- 语言本身的细节（语句、函数与脚本、错误处理、求值、面向对象）：做项目时用得上，但不属于「学数学」，需要时查手册。
- 图形对象的底层结构（句柄与属性）与高级绘图：本应用只收高层绘图函数。

## 手册没覆盖、本应用也不补的

手册没有「教学顺序」：它不会告诉你先做什么再做什么。需要成体系的入门（如 Lachniet 的《Introduction to GNU Octave》，专为线代与微积分学生写的小册子）时，
把 PDF 放进 `upstream/` 另起应用（见主仓库 ADR 0163 与 `docs/HANDOFF.md`）。GeoGebra 同理，没有可入库的书。
