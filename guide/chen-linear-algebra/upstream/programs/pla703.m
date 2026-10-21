% 《实用大众线性代数（MATLAB版）》第七章例7.3程序pla703
%  离散傅里叶变换
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
xn=input('样本x=  ')
N=length(xn)
n = [0:1:N-1]; k = [0:1:N-1];   	% 设定n和k的行向量
WN = exp(-j*2*pi/N);         		% 设定Wn因子
nk = n'*k;              			% 产生一个含nk值的N乘N维的整数矩阵
WNnk = WN .^ nk;           			% 求出W矩阵
Xk = xn * WNnk;					% 求出离散傅里叶级数系数
plot(k,abs(Xk))