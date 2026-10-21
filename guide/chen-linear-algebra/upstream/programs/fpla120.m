clear, close all
ezplot('3-2*t-2*t^2+t^3'),hold on
plot([0,1,2,3],[3,0,-1,6],'r*')
grid on
axis([-1,4,-2,8])
set(gcf,'color','w')
hold on,plot(1.5,-1.125,'bs')