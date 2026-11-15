clear; clc;

data1 = importdata('nand_nor_waveforms.csv');

 P1 = subplot(6,1,1);
 plot(data1.data(:,1), abs(data1.data(:,2)), 'color',[0 0 0.5], 'LineWidth', 2)
 hold on;
 plot(data1.data(:,1), abs(data1.data(:,3)), 'color',[0.5 0 0.5], 'LineWidth', 2)
 grid;
 %ylim([0 3])
 %xlim([30e-6 160e-6])
 set(gca,'XTickLabel',[])
 
 P2 = subplot(6,1,2);
 plot(data1.data(:,1), abs(data1.data(:,4)), 'color',[0 0 0.5], 'LineWidth', 2)
 grid;
 %ylim([0 3])
 %xlim([30e-6 160e-6])
 set(gca,'XTickLabel',[])

 P4 = subplot(6,1,3);
 plot(data1.data(:,1), abs(data1.data(:,5)), 'color',[0 0.5 0], 'LineWidth', 2)
 grid;
 %ylim([0 3])
 %xlim([30e-6 160e-6])
 set(gca,'XTickLabel',[])
 
 P5 = subplot(6,1,4);
 plot(data1.data(:,1), data1.data(:,6), 'color',[0.5 0 0.5], 'LineWidth', 2)
 grid;
 %ylim([-20e-9 20e-9])
 %xlim([30e-6 160e-6])
 set(gca,'XTickLabel',[])
 
 P6 = subplot(6,1,5);
 plot(data1.data(:,1), abs(data1.data(:,7)), 'color',[0 0.5 0], 'LineWidth', 2)
 grid;
 %ylim([0 3])
 %xlim([30e-6 160e-6])
 set(gca,'XTickLabel',[])
 P7 = subplot(6,1,6);
 plot(data1.data(:,1), data1.data(:,8), 'color',[0.5 0 0.5], 'LineWidth', 2)
 grid;
 %ylim([-20e-9 20e-9])
 %xlim([30e-6 160e-6])

 
 set(get(P1,'Title'),'String','IN-MEMORY AND IN A 2x2 1-FeFET MEMORY ARRAY');
 set(get(P1,'YLabel'),'String','V(OUTC1)');
 set(get(P2,'YLabel'),'String','V(OUTC2)');
 set(get(P4,'YLabel'),'String','V(WLRW1)');
 set(get(P5,'YLabel'),'String','V(SLC1)');
 set(get(P6,'YLabel'),'String','V(WLRW2)');
 set(get(P7,'YLabel'),'String','V(SLC2)');
 set(get(P7,'XLabel'),'String','Time(s)');
 
 

 hold off


% p_data = importdata('results_P.printtr0');
% n_data = importdata('results_N.printtr0');
% 
%  P1 = subplot(1,2,1);
%  plot(p_data.data(:,2), abs(p_data.data(:,3)), 'r-', 'LineWidth', 1)
%  hold on
%  plot(n_data.data(:,2), abs(n_data.data(:,3)), 'b-', 'LineWidth', 1)
%  set(get(P1,'Title'),'String','Ids x Vsg-s (Linear)');
%  set(get(P1,'YLabel'),'String','Ids');
%  set(get(P1,'XLabel'),'String','Vsg-s');
%  grid;
%  set(gca, 'FontSize', 14) 
%  ylim([0 2E-6])
%  xlim([-3 3])
%  hold off
%  
%  P2 = subplot(1,2,2);
%  semilogy(p_data.data(:,2), abs(p_data.data(:,3)), 'r-', 'LineWidth', 1)
%  hold on
%  semilogy(n_data.data(:,2), abs(n_data.data(:,3)), 'b-', 'LineWidth', 1)
%  set(get(P2,'Title'),'String','Ids x Vsg-s (Log)');
%  set(get(P2,'YLabel'),'String','Ids');
%  set(get(P2,'XLabel'),'String','Vsg-s');
%  grid on;
%  set(gca, 'FontSize', 14) 
%  ylim([1E-20 1E-5])
%  xlim([-3 3])
%  hold off
