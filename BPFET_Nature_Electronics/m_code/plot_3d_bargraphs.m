
%NAND
data = importdata('robustness_nand.csv');
x=data.data(:,1);
y=data.data(:,2);
z_00=data.data(:,3);
z_01=data.data(:,4);
z_10=data.data(:,5);
z_11=data.data(:,6);

figure


subplot(2,2,1),scatterbar3(x,y,z_00,0.02,0.02)
title('Input: 00')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,2),scatterbar3(x,y,z_01,0.02,0.02)
title('Input: 01')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,3),scatterbar3(x,y,z_10,0.02,0.02)
title('Input: 10')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,4),scatterbar3(x,y,z_11,0.02,0.02)
title('Input: 11')
caxis manual
caxis([-0.1 1.2]);

set(findobj(gcf,'type','axes'),'FontName','Calibri','FontSize',15, ...
'FontWeight','Bold', 'LineWidth', 1,'layer','top','ZLim',[-0.1 1.2]);
arrayfun(@(x) grid(x,'on'), findobj(gcf,'Type','axes'));

hp4 = get(subplot(2,2,4),'Position');
colorbar('Position', [hp4(1)+hp4(3)+0.03  hp4(2)  0.01  hp4(2)+hp4(3)*2.5])

xlh = xlabel('x label');
xlh.Position(2) = xlh.Position(2) - 0.1;

ax = findobj(gcf,'Type','Axes');
for i=1:length(ax)
    xlh = xlabel(ax(i),{'V_{DD}'},'fontweight','normal');
    ylh = ylabel(ax(i),{'V_{SS}'},'fontweight','normal')
    zlabel(ax(i),{'V_{OUT}'},'fontweight','normal')

    xlh.Position(2) = xlh.Position(2) + abs(xlh.Position(2) * 0.45);
    ylh.Position(1) = ylh.Position(1) + abs(ylh.Position(1) * 0.42);
    ylh.Position(2) = ylh.Position(2) - abs(ylh.Position(2) * 0.1);
end

s = suptitle('NAND Function');
set(s,'FontSize',24,'FontWeight','Bold')

%NOR
data = importdata('robustness_nor.csv');
x=data.data(:,1);
y=data.data(:,2);
z_00=data.data(:,3);
z_01=data.data(:,4);
z_10=data.data(:,5);
z_11=data.data(:,6);

figure
subplot(2,2,1),scatterbar3(x,y,z_00,0.02,0.02)
title('Input: 00')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,2),scatterbar3(x,y,z_01,0.02,0.02)
title('Input: 01')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,3),scatterbar3(x,y,z_10,0.02,0.02)
title('Input: 10')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,4),scatterbar3(x,y,z_11,0.02,0.02)
title('Input: 11')
caxis manual
caxis([-0.1 1.2]);

set(findobj(gcf,'type','axes'),'FontName','Calibri','FontSize',15, ...
'FontWeight','Bold', 'LineWidth', 1,'layer','top','ZLim',[-0.1 1.2]);
arrayfun(@(x) grid(x,'on'), findobj(gcf,'Type','axes'));

hp4 = get(subplot(2,2,4),'Position');
colorbar('Position', [hp4(1)+hp4(3)+0.03  hp4(2)  0.01  hp4(2)+hp4(3)*2.5])

ax = findobj(gcf,'Type','Axes');
for i=1:length(ax)
    xlh = xlabel(ax(i),{'V_{DD}'},'fontweight','normal');
    ylh = ylabel(ax(i),{'V_{SS}'},'fontweight','normal')
    zlabel(ax(i),{'V_{OUT}'},'fontweight','normal')

    xlh.Position(2) = xlh.Position(2) + abs(xlh.Position(2) * 0.45);
    ylh.Position(1) = ylh.Position(1) + abs(ylh.Position(1) * 0.42);
    ylh.Position(2) = ylh.Position(2) - abs(ylh.Position(2) * 0.1);
end

s = suptitle('NOR Function');
set(s,'FontSize',24,'FontWeight','Bold')

%XOR
data = importdata('robustness_xor.csv');
x=data.data(:,1);
y=data.data(:,2);
z_00=data.data(:,3);
z_01=data.data(:,4);
z_10=data.data(:,5);
z_11=data.data(:,6);

figure
subplot(2,2,1),scatterbar3(x,y,z_00,0.02,0.02)
title('Input: 00')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,2),scatterbar3(x,y,z_01,0.02,0.02)
title('Input: 01')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,3),scatterbar3(x,y,z_10,0.02,0.02)
title('Input: 10')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,4),scatterbar3(x,y,z_11,0.02,0.02)
title('Input: 11')
caxis manual
caxis([-0.1 1.2]);


set(findobj(gcf,'type','axes'),'FontName','Calibri','FontSize',15, ...
'FontWeight','Bold', 'LineWidth', 1,'layer','top','ZLim',[-0.1 1.2]);
arrayfun(@(x) grid(x,'on'), findobj(gcf,'Type','axes'));

hp4 = get(subplot(2,2,4),'Position');
colorbar('Position', [hp4(1)+hp4(3)+0.03  hp4(2)  0.01  hp4(2)+hp4(3)*2.5])

ax = findobj(gcf,'Type','Axes');
for i=1:length(ax)
    xlh = xlabel(ax(i),{'V_{DD}'},'fontweight','normal');
    ylh = ylabel(ax(i),{'V_{SS}'},'fontweight','normal')
    zlabel(ax(i),{'V_{OUT}'},'fontweight','normal')

    xlh.Position(2) = xlh.Position(2) + abs(xlh.Position(2) * 0.45);
    ylh.Position(1) = ylh.Position(1) + abs(ylh.Position(1) * 0.42);
    ylh.Position(2) = ylh.Position(2) - abs(ylh.Position(2) * 0.1);
end

s = suptitle('XOR Function');
set(s,'FontSize',24,'FontWeight','Bold')

%XNOR
data = importdata('robustness_xnor.csv');
x=data.data(:,1);
y=data.data(:,2);
z_00=data.data(:,3);
z_01=data.data(:,4);
z_10=data.data(:,5);
z_11=data.data(:,6);

figure
subplot(2,2,1),scatterbar3(x,y,z_00,0.02,0.02)
title('Input: 00')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,2),scatterbar3(x,y,z_01,0.02,0.02)
title('Input: 01')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,3),scatterbar3(x,y,z_10,0.02,0.02)
title('Input: 10')
caxis manual
caxis([-0.1 1.2]);
subplot(2,2,4),scatterbar3(x,y,z_11,0.02,0.02)
title('Input: 11')
caxis manual
caxis([-0.1 1.2]);


set(findobj(gcf,'type','axes'),'FontName','Calibri','FontSize',15, ...
'FontWeight','Bold', 'LineWidth', 1,'layer','top','ZLim',[-0.1 1.2]);
arrayfun(@(x) grid(x,'on'), findobj(gcf,'Type','axes'));

hp4 = get(subplot(2,2,4),'Position');
colorbar('Position', [hp4(1)+hp4(3)+0.03  hp4(2)  0.01  hp4(2)+hp4(3)*2.5])

ax = findobj(gcf,'Type','Axes');
for i=1:length(ax)
    xlh = xlabel(ax(i),{'V_{DD}'},'fontweight','normal');
    ylh = ylabel(ax(i),{'V_{SS}'},'fontweight','normal')
    zlabel(ax(i),{'V_{OUT}'},'fontweight','normal')

    xlh.Position(2) = xlh.Position(2) + abs(xlh.Position(2) * 0.45);
    ylh.Position(1) = ylh.Position(1) + abs(ylh.Position(1) * 0.42);
    ylh.Position(2) = ylh.Position(2) - abs(ylh.Position(2) * 0.1);
end

s = suptitle('XNOR Function');
set(s,'FontSize',24,'FontWeight','Bold')




