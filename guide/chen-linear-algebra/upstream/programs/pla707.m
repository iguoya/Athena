% 《实用大众线性代数（MATLAB版）》第七章例7.07程序pla707
%  二自由度振动问题
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
m1=1; m2=9; k1 = 4; k2=2; 		% 输入各原始参数
c1=input('c1=');c2=input('c2=');				% 输入阻尼系数
x0 = [1;0]; xd0 = [0;-1]; tf= 20; dt=0.1;       % 给出初始条件及时间向量
M = [m1,0;0,m2]; K = [k1+k2, -k2; -k2, k2]; 	% 构成二阶参数矩阵
C = [c1+c2, -c2; -c2, c2];
A=[zeros(2,2),eye(2);-M\K,-M\C];	 	% 构成四阶参数矩阵
y0=[x0;xd0];						% 四元变量的初始条件
for i=1:round(tf/dt)+1 			% 设定计算点,作循环计算
    t(i)=dt*(i-1);
    y(:,i)=expm(A*t(i))*y0;		% 循环计算矩阵指数
end
subplot(2,1,1),plot(t,y(1,:)),grid		% 按两个分图绘制x1,x2曲线
subplot(2,1,2),plot(t,y(2,:)),grid
set(gcf,'color','w')