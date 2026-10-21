% 《实用大众线性代数（MATLAB版）》附录A4演示程序demoA4
% 矩阵的运算
% 陈怀琛编著,清华大学出版社,2014年7月
%
echo on,format compact
disp('附录“MATLAB简介”矩阵的运算A４演示程序')
t=[0:0.02:1],pause
theta = linspace(0,2*pi,9),pause
X =[1,2,3],Y=[4,5,6],pause
Z1=X.*Y,pause
Z2=X./Y,pause
Z3=X.^Y,pause
Z4=X.^2,pause
x=[0:0.1:pi/4]';[x,sin(x),cos(x),tan(x)],pause
disp('         x     sin(x)    cos(x)    tan(x) '),
disp([  x     sin(x)    cos(x)    tan(x) ]),pause

