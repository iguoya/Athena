% 《实用大众线性代数（MATLAB版）》例567程序pla567
%  三角图形的运动描述
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
G0=[-1,1,0,-1;1,1,2,1;ones(1,4)]   % 将平面坐标改为三维齐次坐标
plot(G0(1,:),G0(2,:))		% 画出原始图形
axis([-2,4,-2,6]),
hold on,grid on,pause
Gf =[2,2,1,2;3,5,4,3;ones(1,4)]
K0=Gf/G0
% Gf=K0*G0 		% 求出两次变换后图形参数
fill(Gf(1,:),Gf(2,:),'g'),pause	% 画填充绿色图
axis equal
R=[0,-1,0;1,0,0;0,0,1],Gr=R*G0
fill(Gr(1,:),Gr(2,:),'r')
set(gcf,'color','w'),pause	% 转动后画填充红色图
% 下面是问题(b)的解
N=input('分N份，输入N= ')
if isempty(N), N=8, end
K=(K0)^(1/N);
for i=1:N-1
    ys=K^i*G0;pause(2/N);		% 求出转动后图形参数
    fill(ys(1,:),ys(2,:),'r');shg		% 画填充红色图
end
hold off
