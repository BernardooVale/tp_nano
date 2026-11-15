clear; clc;

data1 = importdata('nand_nor_robustness_data.csv');

x=data1.data(:,1);
y=data1.data(:,2);
z=data1.data(:,3);

figure(1)
stem3(x, y, z)
grid on
xv = linspace(min(x), max(x), 20);
yv = linspace(min(y), max(y), 20);
[X,Y] = meshgrid(xv, yv);
Z = griddata(x,y,z,X,Y);
figure(2)
surf(X, Y, Z);
grid on
set(gca, 'ZLim',[0 100])
shading interp