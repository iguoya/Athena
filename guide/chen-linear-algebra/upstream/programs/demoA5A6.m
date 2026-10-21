% 《实用大众线性代数（MATLAB版）》附录Ａ第5,6节演示程序demoA5A6
% 基本绘图方法
% 陈怀琛编著,清华大学出版社,2014年7月
%
echo on,format compact
disp('附录“MATLAB简介”基本绘图方法A5~A6演示程序')
clear, close all,pause
disp('附录Ａ5演示程序')
y=[-1.4,-2.2,0.9,0.9,2.,-0.6,0.1,1.7,-2.3,-2.2],pause
plot(y),pause
title('my first plot'),pause 
xlabel('x'),ylabel('y'),grid on,pause
close,pause
t=0:0.5:4*pi,pause
y=exp(-0.1*t).*sin(t),pause
plot(t,y),hold on,pause
y1=exp(-0.1*t).*sin(t+1),pause
plot(t,y1,':'),pause
hold off, close,pause
% 生成两个方向的自变量向量
x=[-1:0.5:1]; y=[-1:0.5:1],pause 	
% 生成两维自变量网格坐标矩阵
[X,Y]=meshgrid(x,y),pause
plot(X,Y,'*'),pause
Z=2*X+3*Y+2,pause     % 按方程求出因变量Z矩阵数据
mesh(X,Y,Z),pause		% 画三维曲面
hold on,pause
Z1=X-2*Y,pause
mesh(X,Y,Z1),pause
hold off,pause
ezplot('sin(x)*cos(x)'),pause
ezplot('3*x1+2*x2+3',[-4,4]),pause
hold off,ezmesh('3*x1+2*x2+3'),pause 
hold on, ezmesh('x1-2*x2+1'),pause
close, pause
syms a b c d,pause
A=[a,b;c,d],pause
D=det(A),pause
V=inv(A),pause



