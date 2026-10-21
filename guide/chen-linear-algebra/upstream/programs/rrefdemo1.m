function d=rrefdemo1(C)
%
% rrefdemo函数用高斯消元法将方阵化简为下三角及对角矩阵，
% 过程中只进行行交换找最大主元 
% [L, U] = rrefdemo(A) 用高斯消元法找到一个下三角单位
% 矩阵 L 和一个上三角矩阵 U 并使 L*U = A.
% 线性方程组消元全过程显示
% 输入变元C为m行n列增广矩阵，要求n＝m+1
% 输出为方程组的解d的单列矩阵
%
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
disp('高斯消元法解线性方程组')
A=C;tol = 1e-16;
disp(' ');
disp('部分（行）交换找最大主元法')
[m,n] = size(A);
g=input('全部各步骤显示? y/n: ','s');
disp(' ')
disp('初始矩阵')
disp(A)

if g=='y';  % 选择显示全部步骤.
    disp('[按回车键进入下一步]')
    disp(' ')
    pause
end
if g == 'n';
    disp(' **正在计算** ');
    disp(' ');
end
%Initialize vector to keep track of column swaps.
for i = 1:m
    col(i) = i;
end

% 进行消元计算
for k = 1:m-1
    max = 0;
    isav = k;
    jsav = k;
    for i = k:m  % 寻找主元.
        for j=k
            mtest = A(i,j);
            if (abs(mtest)) > max
                max = abs(A(i,j));
                isav = i;
                jsav = j;
            end
        end
    end
    if( max < tol) % 检验是否是主元.
        disp('矩阵奇异');
        disp(A);
        break;
    end
    if (isav ~= k)
        % 行交换
        fprintf('进行行交换，使第%d列主元A((%d,%d))下方绝对值最大元素A(%d,%d)移到主元的位置\n',k,k,k,isav,k)
        for j = 1:n
            temp = A(k,j);
            temp1 = A(isav,j);
            A(k,j) = temp1;
            A(isav,j) = temp;
        end
        if g=='y'  % 选择显示全部步骤.
            fprintf('将第%d行与第%d行交换\n',k,isav)
            disp(A);
            pause;
        end
    end
%    if (jsav ~= k)
%       fprintf('进行列交换，使系数矩阵右下方%d行%d列中绝对值最大元素处于主元(%d,%d)的位置\n',m-k+1,m-k+1,k,k)
%        % 列交换
%        tempcol = col(jsav);
%        col(jsav) = col(k);
%        col(k) = tempcol;
%        fprintf('将第%d列与第%d列交换\n',k,jsav)
%        for i=1:m
%            temp = A(i,k);
%           temp1 = A(i,jsav);
%            A(i,jsav) = temp;
%            A(i,k) = temp1;
%        end
%        if g=='y'  % 选择显示全部步骤.
%            disp(A);
%            disp('变量现在的排序为: ');
%            disp(col');
%            pause;
%        end
%    end
    for j = k+1:m       % 使主元的下方的诸元素变为零.
        Ajk=A(j,k);Akk=A(k,k);
        mult(j,k) = A(j,k)/A(k,k);
        for i = 1:n
            A(j,i) = A(j,i) - mult(j,k)*A(k,i);
        end
        if g=='y'  % 选择显示全部步骤.
            fprintf('将第%d行乘以%4.4f/%4.4f,从第%d行中减去\n',k,Ajk,Akk,j)
            fprintf('使A(%d,%d)消成零元素\n',j,k)
            disp(A)
            pause;
        end
    end
end
% 消元计算完成.
if (A(m,m) == 0)         % 检验矩阵系数是否奇异.
    disp('矩阵系数奇异')
    disp(A);
    return;
end
% 显示化成的上三角形式.
disp('增广矩阵化成的上三角形式:');
disp(A);

% 做回代运算.
for k=m:-1:1
    for j =k-1:-1:1       % 使主元的上方的诸元素变为零.
        Ajk=A(j,k); Akk=A(k,k);
        mult(j,k) = A(j,k)/A(k,k);
        for i = 1:n
            A(j,i) = A(j,i) - mult(j,k)*A(k,i);
        end
        if g=='y' % 选择显示全部步骤.
            fprintf('将第%d行乘以%4.4f/%4.4f,从第%d行中减去\n',k,Ajk,Akk,j)
            fprintf('使A(%d,%d)消成零元素\n',j,k)
            disp(A)
            pause;
        end
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

% 若进行过列交换交换解的顺序.
%for i = 1:m
%    if(col(i) ~= i)
%        disp('变量现在的排序为: ');
%        disp(col');
%        break;
%    end
%end
if n==m
    disp('方程常数项不存在，增广矩阵不全，不可解'),d=[];return
else
    for j = 1:n-m
        for i = 1:m
            xo(j,col(i)) = x(j,i);
        end
    end

    % 显示方程组的解.
    disp('返回到变量原始的排序后，方程组的解为:');
    d=xo';
end