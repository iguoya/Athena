# 术语对照与译文约定

首次出现用「中文（English）」，之后用中文。代码标识符（函数名、选项字符串、变量名）一律不翻译。线代、高数术语用国内通行译法（同济《线性代数》《高等数学》）。

| English | 中文 | English | 中文 |
|---|---|---|---|
| matrix / matrices | 矩阵 | vector | 向量 |
| scalar | 标量 | element / entry | 元素 |
| row / column | 行 / 列 | diagonal | 对角线 |
| transpose / conjugate transpose | 转置 / 共轭转置 | identity matrix | 单位矩阵 |
| determinant | 行列式 | inverse | 逆（矩阵） |
| pseudoinverse | 伪逆 | rank | 秩 |
| null space | 零空间 | range / column space | 值域 / 列空间 |
| orthonormal basis | 标准正交基 | eigenvalue / eigenvector | 特征值 / 特征向量 |
| singular value (decomposition) | 奇异值（分解） | factorization | 分解 |
| Cholesky factorization | Cholesky 分解 | LU / QR factorization | LU / QR 分解 |
| norm | 范数 | condition number | 条件数 |
| positive definite | 正定 | symmetric / Hermitian | 对称 / 厄米（共轭对称） |
| triangular (upper / lower) | 三角（上 / 下） | sparse matrix | 稀疏矩阵 |
| linear system | 线性方程组 | least squares | 最小二乘 |
| matrix exponential | 矩阵指数 | Kronecker product | Kronecker 积 |
| polynomial | 多项式 | root | 根 |
| coefficient | 系数 | convolution / deconvolution | 卷积 / 解卷积 |
| derivative / integral | 导数 / 积分 | numerical integration / quadrature | 数值积分 |
| differential equation | 微分方程 | initial value problem | 初值问题 |
| interpolation | 插值 | spline | 样条 |
| curve fitting | 曲线拟合 | nonlinear equation | 非线性方程 |
| minimizer | 极小化求解器 | tolerance | 容差 |
| function handle | 函数句柄 | vectorization | 向量化 |
| broadcasting | 广播 | element-wise | 逐元素 |
| index / indexing | 下标 / 索引 | range (colon `a:b:c`) | 区间（冒号表达式） |
| logical | 逻辑（值） | precision | 精度 |
| plot | 绘图 / 图 | axes / axis | 坐标轴 |
| contour | 等高线 | mesh / surface | 网格面 / 曲面 |
| legend | 图例 | label | 标签 |

## 译文约定

- 公式、行内代码一律不动；中文标点用全角（，。；：？！），公式、代码与中文之间不强求空格。
- 不要出现「显然」「容易看出」「不难证明」等把难度推给读者的词（内容检查会拦）。
- 手册里的 "See also: `a`, `b`." 译成「另见：`a`、`b`。」，其中代码不动。
- "Programming Note(s)" 译「编程注记」，"Compatibility Note" 译「兼容性说明」，"Example" 译「例」，"Warning" 译「警告」。
- 对读者说话用「你」或「我们」。
