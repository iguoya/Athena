% 《实用大众线性代数（MATLAB版）》第五章演示程序plaf552
%  不同特征值的二次型曲面
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear
subplot(2,2,1)
ezmesh('3*y1^2+7*y2^2')
grid on
subplot(2,2,2)
ezmesh('3*y1^2-7*y2^2')
grid on
axis([-5,5,-5,5,-400,200])
subplot(2,2,3)
ezmesh('-3*y1^2-7*y2^2')
grid on
subplot(2,2,4)
ezmesh('3*y1^2')
grid on
