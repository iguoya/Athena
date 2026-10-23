clear,close all
ezplot('3-2*t+t^2')
grid on
hold on,plot([1,2,3],[2,3,6],'r*')
axis([0,4,1,10])
set(gcf,'color','w')