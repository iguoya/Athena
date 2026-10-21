% 《实用大众线性代数（MATLAB版）》第五章演示程序plaf551
%  不同坐标系的二次型曲线
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,
subplot(2,2,1)
ezplot('5*x1^2-4*x1*x2+5*x2^2=48')
axis equal,grid on
subplot(2,2,3)
ezplot('3*y1^2+7*y2^2=48')
axis equal,grid on
subplot(2,2,2)
ezplot('x1^2-8*x1*x2-5*x2^2=16')
axis equal,grid on
subplot(2,2,4)
ezplot('-7*y1^2+3*y2^2=16')
axis equal,grid on
set(gcf,'color','w')
