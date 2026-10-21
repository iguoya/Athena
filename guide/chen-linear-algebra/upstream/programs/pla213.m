% 《实用大众线性代数（MATLAB版）》例题2.13程序pla213
%  lu分解与消元法等价 
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear, close all
format short, format compact
A=[2,-2,0,6;2,-1,2,4;3,-1,4,4;1,1,1,8]
[L,U]=lu(A)					% 用lu命令检验A=L*U
[L1,U1,P1]=lu(A)