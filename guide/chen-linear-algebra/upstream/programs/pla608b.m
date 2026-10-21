% 《实用大众线性代数（MATLAB版）》例6.8程序pla608a
% 圆锥曲线的拟合问题
% 陈怀琛编著,清华大学出版社，2014年7月
%
clear, close all
x=[-1;0;2;2;0;1];y=[0;2;3;-2;-3;2]; 
A=[x.^2,x.*y,y.^2,x,y,ones(6,1)],
b=zeros(6,1),pause
%
K=A\b
%[X,Y]=meshgrid(-4:0.1:4);
%Z=2*X.^2-X.*Y+Y.^2-4*X+Y-6*ones(size(X));
%contour(X,Y,Z,[0 0]),hold on
plot(x,y,'s'),grid on
