% 《实用大众线性代数（MATLAB版）》第六章例6.04程序pla604
%  双滑块动力学系统
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
m1=input('m1=【千克】 ');m2=input('m2=【千克】 ');
theta=input('theta【度】= ');
theta=theta*pi/180;g=9.81;
A = [ m1*cos(theta),-m1, -sin(theta), 0;...
      m1*sin(theta),  0,  cos(theta), 0;...
   	   		0			 , m2, -sin(theta), 0;...
         	0			 ,  0, -cos(theta), 1 ];
B = [ 0, m1*g, 0, m2*g]'; X=A\B;
a1=X(1),a2=X(2),N1=X(3),N2=X(4)


