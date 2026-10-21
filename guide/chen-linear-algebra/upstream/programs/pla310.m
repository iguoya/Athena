% 《实用大众线性代数（MATLAB版）》例题3.10程序pla310
%  方阵特征值和特征向量的解
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear, close all
format rat,
A=[1.5,0;0,1],  
c=poly(A),  
lambda=roots(c)
p(:,1)=null([A-lambda(1)*eye(2)],'r');
p(:,2)=null([A-lambda(2)*eye(2)],'r')
[p1,L1]=eig(A)
