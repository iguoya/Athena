% 《实用大众线性代数（MATLAB版）》例题4.03程序pla403
%  平面向量及其线性组合的绘制
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
u=[4;2],v=[-1.5;3],x0=[1;0],
u0=u/norm(u), v0=v/norm(v)
thetau=acos(u0'*x0),thetav=acos(v0'*x0),
thetauv=acos(u0'*v0)
plotangle(u,v);     % 此为本书专用绘图子程序
grid on
set(gcf,'color','w')
axis([-2 5 -1 6])