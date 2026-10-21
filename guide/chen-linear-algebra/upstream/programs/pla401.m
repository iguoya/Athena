% 《实用大众线性代数（MATLAB版）》例题4.01程序pla401
%  平面向量及其线性组合的绘制
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
u=[2;4],v=[3;-1]
drawvec(u),hold on
drawvec(v,'b'),hold on
drawvec(u+v,'g'),hold on
drawvec(u-v,'m'),hold off
grid on