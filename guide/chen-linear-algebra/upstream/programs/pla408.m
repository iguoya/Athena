% 《实用大众线性代数（MATLAB版）》图4.08程序pla408
%  弹簧刚度系数的超定方程解
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear, close all
A=[4,7,11]', b=[3,5,8]',
k=inv(A'*A)*A'*b,
e=A*k-b,norme=norm(e)
