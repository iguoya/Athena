% 《实用大众线性代数（MATLAB版）》图5.01程序pla541
%  两维线性变换的几何形象
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
x=[0,1,1,0;0,0,1,1];
subplot(2,3,1),
fill([x(1,:),0],[x(2,:),0],'y')
hold on,drawvec([1;0]);hold on,drawvec([0;1]);
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(a) x=[0,1,1,0;0,0,1,1]')
A1=[-1,0;0,1],V1=inv(A1),y1=V1*x
subplot(2,3,2),
fill([y1(1,:),0],[y1(2,:),0],'g');
hold on,drawvec(V1(:,1));hold on,drawvec(V1(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(b)V1=[-1,0;0,1]')
A2=[1.5,0;0,1],V2=inv(A2)
y2=V2*x
subplot(2,3,3),
fill([y2(1,:),0],[y2(2,:),0],'g');
hold on,drawvec(V2(:,1));hold on,drawvec(V2(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(c)V2=[2/3,0;0,1]')
A3=[1,0;0,0.2],V3=inv(A3)
y3=V3*x
subplot(2,3,4),
fill([y3(1,:),0],[y3(2,:),0],'g');
hold on,drawvec(V3(:,1));hold on,drawvec(V3(:,2));
axis equal,axis([-1.5,3,-0.5,5.5]),grid on
title('(d)V3=[1,0;0,5]')
A4=[1,0.5;0,1],V4=inv(A4)
y4=V4*x
subplot(2,3,5),
fill([y4(1,:),0],[y4(2,:),0],'g');
hold on,drawvec(V4(:,1));hold on,drawvec(V4(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(e)V4=[1,-0.5;0,1]')
t=pi/6,
A5=[cos(t),-sin(t);sin(t),cos(t)],V5=inv(A5)
y5=V5*x
subplot(2,3,6),
fill([y5(1,:),0],[y5(2,:),0],'g');
hold on,drawvec(V5(:,1));hold on,drawvec(V5(:,2));
axis equal,axis([-1.5,1.5,-1,2]),grid on
title('(f)V5=[0.866;0.5;-0.5,0.866]')
set(gcf,'color','w')
