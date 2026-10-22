function [L,U] = rrefdemo(A)
%
% rrefdemo函数用高斯消元法将方阵化简为下三角及对角矩阵，
% 过程中不进行主元的行交换和列交换 
% [L, U] = rrefdemo(A) 用高斯消元法找到一个下三角单位
% 矩阵 L 和一个上三角矩阵 U 并使 L*U = A.
% 如果出现了太小的主元，此运算将会中断.
% 线性方程组消元全过程显示
% 输入变元C为m行n列增广矩阵，要求n＝m+1
% 输出为方程组的解d的单列矩阵
%
% 陈怀琛编著，西安电子科技大学出版社，2014年7月
%
[m, n] = size(A);
p=input('要分步执行，按y，否则按任意键  ','s' )
for k = 1:m
%   if abs(A(k, k)) < sqrt(eps)
%      disp(['在第 ' int2str(k) '列中出现的主元太小.'])
%   end
   L(k, k) = 1;
   for i = k+1:m
      L(i,k) = A(i, k) / A(k, k);
      fprintf('将第%d行乘以%4.4f/%4.4f=%4.4f,从第%d行中减去\n',k,A(i,k),A(k,k),L(i,k),i)
%      for j = 1:k-1
%         A(i, j) = A(i, j) - L(i, k)*A(k, j)
%      end
      for j = 1:n
         A(i, j) = A(i, j) - L(i, k)*A(k, j);
      end,A,
      if p=='y' pause,else,end
   end
   for j = k:n
      U(k, j) = A(k, j);
   end
end
disp('消元运算中的乘数组成下三角单位矩阵L，其第一下标为基准行编号，第二下标为待变换行编号')
%L,U,L*U,inv(L),inv(L)*A
disp('消元运算中原矩阵变为上三角矩阵U，其主对角线上诸元素连乘积为系数方阵的行列式D=prod(diag(U))')
D=prod(diag(U))
% 回代过程
disp('以下进行回代过程，将系数方阵对角线主元上方的元素消为零，使系数矩阵对角化')
for k = m:-1:1
    for i = 1:k-1
      L(i,k) = A(i, k) / A(k, k);
      fprintf('将第%d行乘以%4.4f/%4.4f=%4.4f,从第%d行中减去\n',k,A(i,k),A(k,k),L(i,k),i)
      for j = 1:n
         A(i, j) = A(i, j) - L(i, k)*A(k, j);
      end,A,
      if p=='y' pause,else,end
    end
   for j = k:n
      U(k, j) = A(k, j);
   end
end

for k = 1:n-m
    x(k,m) = A(m,m+k)/A(m,m);
end
for k = 1:n-m
    for i = m-1:-1:1
        sum(k) = 0;
        for j = i+1:m
            sum(k) = sum(k) + A(i,j)*x(k,j);
        end
        x(k,i) = A(i,m+k) - sum(k);
        if (A(i,i) == 0)    % 检验矩阵系数是否奇异.
            disp('矩阵系数奇异');
            disp(A);
            break;
        end
        x(k,i) = x(k,i)/A(i,i);
    end
end

% 显示化成的对角形式.
disp('增广矩阵化成的对角形式:');
disp(A);
disp('将增广矩阵各行除以该行主元，得到行最简形为:');
disp(A./(diag(A)*ones(1,n)))
disp('当前排序下方程的解为:');
disp(A(:,n)./diag(A))
