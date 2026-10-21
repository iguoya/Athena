% 《实用大众线性代数（MATLAB版）》图4.09程序pla409
%  超定方程组1.2(d)的解及图
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear, close all
A=[1,1;1,-1;-1,2],b=[-1;3;-3]
xhat1=pinv(A)*b
xhat2=inv(A'*A)*A'*b
xhat3=A\b
norme=norm(A*xhat1-b)
ezplot('x+y+1')
hold on, grid on
ezplot('x-y-3'),hold  on
%plot(1.85,-0.71,'*')
set(gcf,'color','w')
ezplot('-x+2*y+3'),hold on
plot(xhat1(1),xhat1(2),'*')