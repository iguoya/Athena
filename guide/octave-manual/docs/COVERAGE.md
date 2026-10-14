# 覆盖表：Octave 手册 → 线代与高数

手册（钉 `release-8-4-0`）有 40 多章、上千个函数，是参考手册而不是教程。本应用按「用 Octave 学线性代数与高等数学」裁剪：
每页取手册某章的若干节，并**只收下表「函数」列里的函数说明**；没列的函数、没列的节不进课表，也不留占位。
页序是学习顺序，不是手册章序。各页的「试一试」数量随写作推进。

| 页 | 手册章 | 取的节 | 函数数 | 函数 |
|---|---|---|---|---|
| numbers（数值类型与矩阵） | `numbers.txi` | Matrices、Ranges、Logical Values、Predicates for Numeric Objects | 21 | double logical true false isnumeric islogical isfloat isreal iscomplex ismatrix isvector isrow iscolumn isscalar issquare issymmetric ishermitian isdefinite isdiag istril istriu |\n| expr（表达式与运算符） | `expr.txi` | Index Expressions、Arithmetic Operators、Comparison Operators、Boolean Expressions、Assignment Expressions、Operator Precedence | 15 | sub2ind ind2sub mldivide mrdivide mpower mtimes times power rdivide transpose ctranspose isequal and or not |\n| matrix（矩阵的构造与变形） | `matrix.txi` | Finding Elements and Checking Conditions、Rearranging Matrices、Special Utility Matrices、Famous Matrices | 36 | any all diff isinf isnan find fliplr flipud flip rot90 cat horzcat vertcat permute reshape circshift sort tril triu vec diag blkdiag eye ones zeros repmat linspace logspace rand randi randn magic hilb vander toeplitz pascal |\n| arith（算术与初等函数） | `arith.txi` | Exponents and Logarithms、Complex Arithmetic、Trigonometry、Sums and Products、Utility Functions、Special Functions、Coordinate Transformations、Mathematical Constants | 59 | exp log log10 log2 sqrt nthroot abs arg conj imag real deg2rad rad2deg sin cos tan asin acos atan sinh cosh tanh atan2 sind cosd sum prod cumsum cumprod sumsq ceil fix floor round max min hypot gradient dot cross factorial factor gcd lcm rem mod primes sign gamma erf beta cart2pol pol2cart e pi I Inf NaN eps |\n| vectorize（向量化与广播） | `vectorize.txi` | Basic Vectorization、Broadcasting、Function Application、Miscellaneous Techniques、Examples | 2 | bsxfun arrayfun |\n| plot（绘图） | `plot.txi` | Introduction to Plotting、High-Level Plotting | 45 | plot semilogx semilogy loglog bar hist stairs stem scatter contour contourf polar axis xlim fill area fplot ezplot mesh meshc surf surfc meshgrid plot3 view contour3 quiver sombrero peaks scatter3 waterfall title legend text xlabel clabel grid colorbar subplot figure hold clf close print saveas |\n| linalg（线性代数） | `linalg.txi` | Techniques Used for Linear Algebra、Basic Matrix Functions、Matrix Factorizations、Functions of a Matrix | 23 | det eig inv linsolve norm null orth pinv rank rcond trace rref cond vecnorm chol lu qr schur svd expm logm sqrtm kron |\n| poly（多项式与拟合） | `poly.txi` | Evaluating Polynomials、Finding Roots、Products of Polynomials、Derivatives / Integrals / Transforms、Polynomial Interpolation、Miscellaneous Functions | 14 | polyval polyvalm roots compan conv deconv polygcd residue polyder polyint polyfit poly polyout polyreduce |\n| interp（插值） | `interp.txi` | One-dimensional Interpolation、Multi-dimensional Interpolation | 3 | interp1 spline interp2 |\n| quad（数值积分） | `quad.txi` | Functions of One Variable、Functions of Multiple Variables | 11 | quad quadv quadl quadgk quadcc integral trapz cumtrapz dblquad integral2 integral3 |\n| diffeq（常微分方程） | `diffeq.txi` | Ordinary Differential Equations、Matlab-compatible solvers | 5 | lsode ode45 ode23 odeset odeget |\n| nonlin（方程求根与最优化） | `nonlin.txi` | Solvers、Minimizers | 5 | fsolve fzero fminbnd fminunc fminsearch |

## 整章裁掉的内容与理由

- 与线代、高数无关：字符串、容器（cell、struct）、文件与输入输出、音频、图像、几何（Delaunay 等）、稀疏矩阵、信号处理、统计与随机分布、包管理、调试与测试、外部代码接口、GUI。
- 语言本身的细节（语句、函数与脚本、错误处理、求值、面向对象）：做项目时用得上，但不属于「学数学」，需要时查手册。
- 图形对象的底层结构（句柄与属性）与高级绘图：本应用只收高层绘图函数。

## 手册没覆盖、本应用也不补的

手册没有「教学顺序」：它不会告诉你先做什么再做什么。需要成体系的入门（如 Lachniet 的《Introduction to GNU Octave》，专为线代与微积分学生写的小册子）时，
把 PDF 放进 `upstream/` 另起应用（见主仓库 ADR 0163）。GeoGebra 同理，没有可入库的书。
