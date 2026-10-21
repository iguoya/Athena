% 《实用大众线性代数（MATLAB版）》例题4.6.2程序pla462a
%  空间三点求平面方程及点到平面的距离
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear, close all
A=[-2,5,0,3;0,1,-2,-1;-5,-1,-1,-2]
B=ones(3,1), X=A(:,1:3)'\B
fprintf('\n      平面方程为：%f x + %f y + %f z = 1 \n',X(1),X(2),X(3));
C=[X',1]/X(3)
fprintf('\n      或：%f x + %f y + z = %f \n',C(1),C(2),C(4));
A1=[X';1/X(1),-1/X(2),0;1/X(1),0,-1/X(3)]
B1=[1;0;0], Xd=A1\B1
fprintf('\n     从原点引向此平面的垂足坐标为：[%f; %f; %f]\n',Xd(1),Xd(2),Xd(3));
l=norm(Xd);
fprintf('\n     从原点向此平面所引法线的长度为：%f \n',l);
A2=[X';1/X(1),-1/X(2),0;1/X(1),0,-1/X(3)]
B2=[1;A(1,4)/X(1)-A(2,4)/X(2);A(1,4)/X(1)-A(3,4)/X(3)]
Xd2=A2\B2
fprintf('\n     从点4引向此平面的垂足坐标为：[%f; %f; %f]\n',Xd2(1),Xd2(2),Xd2(3));
l2=norm(Xd2-A(:,4));
fprintf('\n     从点4向此平面所引法线的长度为：%f \n',l2);
disp('绘图')
ezmesh(' -3.5+0.75*x - 1.25*y')
%ezmesh('z=C(4) - C(1)*x - C(2)*y')
hold on,plot3(Xd(1),Xd(2),Xd(3),'*')
h1=line([0,Xd(1)],[0,Xd(2)],[0,Xd(3)])
set(h1,'color','g','linewidth',2)
plot3(A(1,1:3),A(2,1:3),A(3,1:3),'o')
plot3(0,0,0,'s')
plot3(Xd2(1),Xd2(2),Xd2(3),'*')
h2=line([A(1,4),Xd2(1)],[A(2,4),Xd2(2)],[A(3,4),Xd2(3)]) 
set(h2,'color','m','linewidth',3)
plot3(A(1,4),A(2,4),A(3,4),'d')
axis equal
axis([-5, 5, -5, 5, -5, 5])
set(gcf,'color','w')
