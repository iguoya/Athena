% 《实用大众线性代数（MATLAB版）》例7.14程序pla714
%  用特征方程解Fibonacci数列问题
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
clear
A=[1,1;1,0],                % Fibonacci数列矩阵模型
[p,lamda]=eig(A)            % 模型的对角化
for k=[1,3,5,10,20,50,100]
    u=p*lamda^k*inv(p)*[1;0];	% 用矩阵公式计算
    sprintf('第%d项Fibonacci级数的值是%25.0f',k,u(2,:))		 	% 显示不同k值的Fibonacci数
end


