% 《实用大众线性代数（MATLAB版）》例6.11程序pla611
%  三角形的动画运动
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
Q0=[-1,1,0,-1;1,1,2,1;ones(1,4)]   % 将平面坐标改为三维齐次坐标
plot(Q0(1,:),Q0(2,:))		% 画出原始图形
axis([-2,4,0,6]),
hold on,grid on,pause
Qf =[2,2,1,2;3,5,4,3;ones(1,4)]
K0=Qf(:,1:3)/Q0(:,1:3)
% Qf=K0*Q0 		% 求出两次变换后图形参数
fill(Qf(1,:),Qf(2,:),'g'),pause	% 画填充绿色图
axis equal
N=input('分N份，输入N= ')
if isempty(N), N=8, end
K=(K0)^(1/N);
for i=1:N-1
    Qs=K^i*Q0;pause(2/N);		% 求出转动后图形参数
    fill(Qs(1,:),Qs(2,:),'r');shg		% 画填充红色图
end
fill(Qf(1,:),Qf(2,:),'g'),pause	% 画填充绿色图
set(gcf,'color','w'),
hold off
