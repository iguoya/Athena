% 《实用大众线性代数（MATLAB版）》例5.6.2程序pla562
%  炮瞄雷达测量坐标与地面坐标的转换
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear,close all
syms s f r
format compact,
Q1=[cos(s),-sin(s),0;sin(s),cos(s),0;0,0,1]
Q2=[cos(f),0,-sin(f);0,1,0;sin(f),0,cos(f)]
Q=Q2*Q1,
Xm=r*Q(:,1)
Xmr=subs(Xm,[s,f,r],[30*pi/180,60*pi/180,10])
