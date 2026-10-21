% 《实用大众线性代数（MATLAB版）》附录Ａ第2-3节演示程序demoA2~A3
% 矩阵的赋值
% 陈怀琛编著,清华大学出版社,2014年7月
%
echo on,format compact
disp('附录“MATLAB简介”矩阵的赋值A2~A3演示程序')
a=[1  2  3;4  5  6;7  8  9],pause
x=[-1.3,sqrt(3),(1+2+3)/5*4],pause
x(5)=abs(x(1)),pause
a(4,3)=6.5,pause 
a(5,:)=[5,4,3],pause
b =	a([2,4],[1,3]),pause
a([2,4,5],:)=[ ],pause
a',pause
f1=ones(3,2),pause
f2=zeros(2,3),pause
f3=magic(3),pause
f4=eye(2),pause
fb1=[f1,f3;f4,f2],pause
who,pause
whos,pause
0/0,pause
1/0,pause
0*Inf,pause
[m,n]=size(fb1),pause
X=[-1 0 1],pause  
Y=X-1,pause
pi*X,pause
X*Y',pause
X'*Y,pause
A = [6,3,4;-2,5,7;8,-4,-3],pause
B = [3;-4;-7],pause
x = A\B,pause
V=inv(A),pause
A*V,pause
V*A,pause

