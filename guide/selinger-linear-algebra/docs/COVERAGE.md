# 考纲覆盖表

范围原则（主仓库 ADR 0162）：按考研数学二线代考纲裁剪，**体系完整、重在理解**，不过分裁剪，也不让讲解重心偏离考纲太远。
课表里没有的节不放占位。页数估算：全书 608 页，按全书 页数/文件字节比（约 2.6 KB/页，含习题）折算，保留部分约 300 页上下。

## 考纲点 → 原书节

| 考纲（数学二·线性代数） | 原书节 | 覆盖 |
|---|---|---|
| 行列式的概念、性质，按行（列）展开，计算 | Determinants-TwoAndThree / MinorsCofactors / Triangular / RowOperations / Properties | ✓ |
| 伴随矩阵、逆矩阵公式；克拉默法则 | Determinants-Application-Inverse / Application-Cramer | ✓ |
| 矩阵的线性运算、乘法、转置及运算规律 | Matrices-Definition / Addition / ScalarMultiplication / Multiplication-* / Transpose | ✓ |
| 逆矩阵的概念、性质与求法 | Matrices-Inverses-* | ✓ |
| 初等变换、初等矩阵 | Matrices-ElementaryMatrices-*；SystemsofEquations-ElementaryOperations | ✓ |
| 矩阵的秩；等价矩阵 | SystemsofEquations-GaussianElimination / UniquenessRREF；SpanIndependenceBasis-ColumnRowNullSpace | ✓（秩在行/列空间一节正式定义） |
| 分块矩阵及其运算 | — | ✗ 原书（该部分）没有；需要时回 `postgraduate/mathematics` |
| 向量的线性组合与线性表示 | Vectors-LinearCombinations；SpanIndependenceBasis-Span | ✓ |
| 线性相关与线性无关 | SpanIndependenceBasis-LinearIndependence | ✓ |
| 极大线性无关组、等价向量组、向量组的秩 | SpanIndependenceBasis-Basis（基与维数）/ ColumnRowNullSpace | 部分：讲基与维数，没有「极大无关组」这个名字与等价向量组 |
| 线性方程组：高斯消元、解的结构 | SystemsofEquations-*（几何/代数视角、消元、齐次、RREF 唯一性） | ✓ |
| 基础解系、通解、解空间 | SystemsofEquations-HomogeneousSystems；SpanIndependenceBasis-Subspaces / ColumnRowNullSpace | ✓ |
| 特征值与特征向量的概念、性质、求法 | Eigenvalues-Definition / Finding / Properties / Geometric | ✓ |
| 相似矩阵、相似对角化 | Eigenvalues-Diagonalization（原书用「对角化」讲，相似关系在其中） | ✓ |
| 实对称矩阵的特征值、特征向量与正交相似对角化 | InnerProductSpaces-Diagonalization / OrthogonalMaps | ✓ |
| 施密特正交化、正交矩阵 | InnerProductSpaces-GramSchmidt / OrthogonalMaps；Vectors-DotProduct-* | ✓ |
| 二次型及其矩阵表示；用正交变换化标准形 | InnerProductSpaces-Application-QuadraticForms | ✓ |
| 正定二次型、正定矩阵 | InnerProductSpaces-Positive | ✓ |
| 合同变换与合同矩阵、惯性定理、规范形、配方法 | — | ✗ 原书没有；需要时回 `postgraduate/mathematics` |

## 考纲外但为体系与理解保留的节

- Vectors 章前半（点与向量、加法、数乘、长度）与 SystemsofEquations-Geometric：把方程组、向量、几何放在一起看，是理解「解集」的直觉来源。
- LinearTransformationsRn-Definition / Matrix：矩阵作为映射——考纲不单列线性变换，但它是理解乘法、可逆、相似的关键。
- InnerProductSpaces-Definition：一般实内积空间，保证正交与投影的讲法成体系。
- Eigenvalues-Application-Power：矩阵幂，对角化的直接用途。

## 被裁掉的内容

抽象向量空间专章与一般线性变换（VectorSpaces、LinearTransformationsGeneral）；叉积；直线与平面；矩阵的模 p 运算、密码学；
有限域；复数与复特征值、复内积、酉矩阵；傅里叶级数、最小二乘、主成分分析；线性变换的几何与性质、透视渲染；
特征值的递推/微分方程/矩阵指数应用、凯莱—哈密顿；化学方程配平、量纲、电阻网络等应用。
这些在原书里写得好，但离考纲太远；要读时直接看上游 PDF。

## 这份表怎么维护

`content/scope.json` 是范围的唯一来源；改范围时同步改本表。新增一节要写明它对应哪条考纲或为何保留；
原书没讲的考纲点（上表 ✗ 行）不在本应用里补写别的教材的内容（互不干扰，主仓库 ADR 0162）。
