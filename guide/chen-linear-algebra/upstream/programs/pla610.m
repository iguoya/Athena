% 《实用大众线性代数（MATLAB版）》第六章例6.10程序pla610
%  圆截面的测量和拟合
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
x=[-3:3]'; y=[3.03,3.90,4.35,4.50,4.40,4.02,3.26]'; % 把x,y赋值为列向量
A=[2*x, 2*y, ones(size(x))] 				% 按式(6.6.1)求出系数矩阵
B=x.^2+y.^2, c=inv(A'*A)*A'*B,  			% 求超定方程的解，得出c
r=sqrt(c(3)+c(1)^2+c(2)^2)				% 由c求出r
% 绘制拟合圆
plot(x,y,'*')                       % 画出各测量点
axis equal, hold on, grid on
theta=0:0.01:2*pi;                  % 设定圆周角
xr=c(1)+r*cos(theta);               % 圆心为c(1),c(2),以半径r画圆
yr=c(2)+r*sin(theta);
plot(xr,yr)

