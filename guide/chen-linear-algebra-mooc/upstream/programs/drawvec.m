function [ handle ] = drawvec(v,color,s);
%
% DRAWVEC(v,color,s) 用第二个变元规定的颜色画出向量v。
% 如果没有第二个变元，则默认红色，向量的起点为原点，
% 向量的终点处画出一个箭头。
% 坐标轴的范围是[-s,s,-s,s].
% 如果第三个变元未做规定，其默认值为5。
%
% 
if nargin==1
   color = 'r';
end
if nargin < 3
   s=5;
end
handle = plot([0,v(1)],[0,v(2)],color);
axis([-s,s,-s,s])
axis('square')
hold on
[m,n]=size(v);
if n==1  % Change to row vector
   v=v'; 
end
atip=tip(v,s);
fill(atip(1,:),atip(2,:),color)
hold off
