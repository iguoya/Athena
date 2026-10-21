% 《实用大众线性代数（MATLAB版）》例题3.05程序pla305
%  求范德蒙矩阵的行列式
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
syms a1 a2 a3 a4
A=[ones(1,4);a1 a2 a3 a4;[a1 a2 a3 a4].^2;[a1 a2 a3 a4].^3]
D=det(A), simple(D)			% simple是符号处理中的化简函数
