% 《实用大众线性代数（MATLAB版）》图5.01程序pla501
%  两维线性变换的几何形象
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
x=[0,1,1,0;0,0,1,1];
subplot(2,3,1),
fill([x(1,:),0],[x(2,:),0],'r')
hold on,plot([0,1],[0,1],'k','LineWidth',2);
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(a) x=[0,1,1,0;0,0,1,1]')
A1=[-1,0;0,1]
y1=A1*x
subplot(2,3,2),
fill([y1(1,:),0],[y1(2,:),0],'g')
hold on,plot([0,1],[0,1],'k','LineWidth',2);
hold on,drawvec(A1(:,1));hold on,drawvec(A1(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(b)A1=[-1,0;0,1]')
A2=[1.5,0;0,1]
y2=A2*x
subplot(2,3,3),
fill([y2(1,:),0],[y2(2,:),0],'g')
hold on,plot([0,1],[0,1],'k','LineWidth',2);
hold on,drawvec(A2(:,1));hold on,drawvec(A2(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(c)A2=[1.5,0;0,1]')
A3=[1,0;0,0.5]
y3=A3*x
subplot(2,3,4),
fill([y3(1,:),0],[y3(2,:),0],'g')
hold on,plot([0,1],[0,1],'k','LineWidth',2);
hold on,drawvec(A3(:,1));hold on,drawvec(A3(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(d)A3=[1,0;0,0.5]')
A4=[1,0.5;0,1]
y4=A4*x
subplot(2,3,5),
fill([y4(1,:),0],[y4(2,:),0],'g')
hold on,plot([0,1],[0,1],'k','LineWidth',2);
hold on,drawvec(A4(:,1));hold on,drawvec(A4(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(e)A4=[1,0.5;0,1]')
t=pi/6,
A5=[cos(t),-sin(t);sin(t),cos(t)]
y5=A5*x
subplot(2,3,6),
fill([y5(1,:),0],[y5(2,:),0],'g')
hold on,plot([0,1],[0,1],'k','LineWidth',2);
hold on,drawvec(A5(:,1));hold on,drawvec(A5(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(f)A5=[0.866,-0.5;0.5,0.866]')
set(gcf,'color','w')
