% 《实用大众线性代数（MATLAB版）》例题4.05程序pla405
%  四维向量夹角的计算和绘制
%  陈怀琛编著，西安电子科技大学出版社，2014年7月
%
v1=[7;-4;-2;9]; v2=[-4;5;-1;-7]; v3=[9;4;4;-7]; 	% 输入参数
v10=v1/norm(v1), v20=v2/norm(v2), v30=v3/norm(v3),
theta12=acos((v1'*v2)/(norm(v1)*norm(v2)))
theta13=acos(v20'*v30), theta23= acos(v30'*v10)
[s12,t12]=plotangle(v1,v2),pause
[s13,t13]=plotangle(v1,v3),pause
[s23,t23]=plotangle(v2,v3)
