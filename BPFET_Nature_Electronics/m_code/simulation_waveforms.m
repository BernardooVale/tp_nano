clear; clc;

data1 = importdata('xor_xnor_waveforms.csv');

 figure, subplot(5,1,1),plot(data1.data(:,1), abs(data1.data(:,2)), 'color',[0 0 0], 'LineWidth', 1.5)
 title('Waveforms for XOR/XNOR')
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,2),plot(data1.data(:,1), abs(data1.data(:,3)), 'color',[0 0 0], 'LineWidth', 1.5)
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,3),plot(data1.data(:,1), abs(data1.data(:,4)), 'color',[0 0 1], 'LineWidth', 1.5)
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,4),plot(data1.data(:,1), abs(data1.data(:,5)), 'color',[1 0 0], 'LineWidth', 1.5)
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,5),plot(data1.data(:,1), abs(data1.data(:,6)), 'color',[0 0 1], 'LineWidth', 1.5)
 ylim([0 3e-6])
 yticklabels({'0','1.6\muA'})
 hold on;
 subplot(5,1,5),plot(data1.data(:,1), abs(data1.data(:,7)), 'color',[1 0 0], 'LineWidth', 1.5)
 xlabel('Time (s)','FontSize',9)
 xlim([0e-6 30e-6])
 xticklabels({'0','','10\mu','','20\mu','','30\mu'})
 ha=get(gcf,'children');
 set(ha(1),'position',[.1 .2 .4 .1])
 set(ha(2),'position',[.1 .3 .4 .1])
 set(ha(3),'position',[.1 .4 .4 .1])
 set(ha(4),'position',[.1 .5 .4 .1])
 set(ha(5),'position',[.1 .6 .4 .1])
 
 set(findobj(gcf,'type','axes'),'FontName','Calibri','FontSize',9, ...
'LineWidth', 0.5,'layer','top');
arrayfun(@(x) grid(x,'on'), findobj(gcf,'Type','axes'));

data1 = importdata('nand_nor_waveforms.csv');

 figure, subplot(5,1,1),plot(data1.data(:,1), abs(data1.data(:,2)), 'color',[0 0 0], 'LineWidth', 1.5)
 title('Waveforms for NAND/NOR')
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,2),plot(data1.data(:,1), abs(data1.data(:,3)), 'color',[0 0 0], 'LineWidth', 1.5)
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,3),plot(data1.data(:,1), abs(data1.data(:,4)), 'color',[0 0 1], 'LineWidth', 1.5)
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,4),plot(data1.data(:,1), abs(data1.data(:,5)), 'color',[1 0 0], 'LineWidth', 1.5)
 xlim([0e-6 30e-6])
 ylim([0 1.5])
 yticks([0 0.8])
 yticklabels({'0','0.8V'})
 set(gca,'XTickLabel',[])
 subplot(5,1,5),plot(data1.data(:,1), abs(data1.data(:,6)), 'color',[0 0 1], 'LineWidth', 1.5)
 ylim([0 3e-6])
 yticklabels({'0','2.0\muA'})
 hold on;
 subplot(5,1,5),plot(data1.data(:,1), abs(data1.data(:,7)), 'color',[1 0 0], 'LineWidth', 1.5)
 xlabel('Time (s)','FontSize',9)
 xlim([0e-6 30e-6])
 xticklabels({'0','','10\mu','','20\mu','','30\mu'})
 ha=get(gcf,'children');
 set(ha(1),'position',[.1 .2 .4 .1])
 set(ha(2),'position',[.1 .3 .4 .1])
 set(ha(3),'position',[.1 .4 .4 .1])
 set(ha(4),'position',[.1 .5 .4 .1])
 set(ha(5),'position',[.1 .6 .4 .1])
 
 set(findobj(gcf,'type','axes'),'FontName','Calibri','FontSize',9, ...
'LineWidth', 0.5,'layer','top');
arrayfun(@(x) grid(x,'on'), findobj(gcf,'Type','axes'));


