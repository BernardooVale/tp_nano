clear min
clear max

data = importdata('robustness_nand.csv');
vdd=data.data(:,1);
vss=data.data(:,2);
% Generate histogram
h1=histfit(vdd);
set(h1(1),'facecolor',[0.5 0.9 1]); set(h1(2),'color','black')
hold on;
h2=histfit(vss);
set(h2(1),'facecolor',[0.3 0.8 0.8]); set(h2(2),'color','black')
%title("Distribution of the Voltage at Power Rails",'FontSize',12)
xlabel("Voltage",'FontSize',10)
ylabel("# of Occurrences",'FontSize',10)


% vdd: Calculate the min, max, mean, median, and standard deviation
vdd_minx=min(vdd)
vdd_maxx=max(vdd)
vdd_mn=mean(vdd)
vdd_md=median(vdd)
vdd_stdv=std(vdd)

% vss: Calculate the min, max, mean, median, and standard deviation
vss_minx=min(vss)
vss_maxx=max(vss)
vss_mn=mean(vss)
vss_md=median(vss)
vss_stdv=std(vss)
