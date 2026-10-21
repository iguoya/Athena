% 《实用大众线性代数（MATLAB版）》第七章例7.11程序pla711
%  空间运动学中的应用
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear
% 飞行器的外形数据集
Gw=[-4,-3,0;4,-3,0;0,7,0;-4,-3,0]'; % 主翼的顶点坐标
Gt=[0,-3,0;0,-3,3;0,2,0;0,-3,0]';	   % 尾翼的顶点坐标
G=[Gw,Gt]		 		 % 整个飞行器外形的数据集
plot3(Gw(1,:),Gw(2,:),Gw(3,:),'r'),hold on
plot3(Gt(1,:),Gt(2,:),Gt(3,:),'g'),
grid on
% axis equal,axis off
set(gcf,'color','w')
% 飞行器转动时的变换矩阵生成
syms u w v
Y=[cos(u),sin(u),0;-sin(u),cos(u),0;0,0,1]
R=[1,0,0;0,cos(w),-sin(w);0,sin(w),cos(w)]
P=[cos(v),0,-sin(v);0,1,0;sin(v),0,cos(v)]
Q=Y*P*R
A=subs(Q,{u,v,w},{pi/4,0,pi/3})
% 转动后的飞行器外形数据集G1
