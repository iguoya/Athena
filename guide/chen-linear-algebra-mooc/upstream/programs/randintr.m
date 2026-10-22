function A = randintr(m,n,k,r)
%
% RANDINTR(m,n,k,r) 生成秩为r的mxn矩阵，其元素取
% [-k:k]范围内的整数值.
% 如果只输入三个变元，则k的默认值为9.
% 如果只输入一个变元，则矩阵为方阵。
% 如果最后的变元未给，则秩为任意值。
% 
if nargin < 3
   k=9;
end
if nargin == 1
   n=m;
end
test = 0; k = round(abs(k));
if nargin < 4
     A = floor((2*k+1)*rand(m,n) - k);
elseif r == 0 & k == 0
     A=zeros(m,n);
else
     r = round(r);
     if ( r < 1 | k < 1 | r>min(m,n))
	 error('No such matrix exists')
     end
     p = ceil(k/r);
     while test == 0
        A = randintr(m,r,p)*randintr(r,n,1);
	A = A.*(abs(A)<=k);
	if rank(A) == r 
	   test = 1;
	end
     end
end
