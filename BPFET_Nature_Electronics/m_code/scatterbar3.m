function scatterbar3(X,Y,Z,widthx,widthy)

[r,c]=size(Z);
for j=1:r,
    for k=1:c,
        if ~isnan(Z(j,k))
            drawbar(X(j,k),Y(j,k),Z(j,k),widthx/2,widthy/2)
        end
    end
end

zlim=[min(Z(:)) max(Z(:))];
if zlim(1)>0,zlim(1)=0;end
if zlim(2)<0,zlim(2)=0;end
axis([min(X(:))-widthx max(X(:))+widthx min(Y(:))-widthy max(Y(:))+widthy zlim])
caxis([min(Z(:)) max(Z(:))])

function drawbar(x,y,z,widthx,widthy)

h(1)=patch([-widthx -widthx widthx widthx]+x,[-widthy widthy widthy -widthy]+y,[0 0 0 0],'b');
h(2)=patch(widthx.*[-1 -1 1 1]+x,widthy.*[-1 -1 -1 -1]+y,z.*[0 1 1 0],'b');
h(3)=patch(widthx.*[-1 -1 -1 -1]+x,widthy.*[-1 -1 1 1]+y,z.*[0 1 1 0],'b');
h(4)=patch([-widthx -widthx widthx widthx]+x,[-widthy widthy widthy -widthy]+y,[z z z z],'b');
h(5)=patch(widthx.*[-1 -1 1 1]+x,widthy.*[1 1 1 1]+y,z.*[0 1 1 0],'b');
h(6)=patch(widthx.*[1 1 1 1]+x,widthy.*[-1 -1 1 1]+y,z.*[0 1 1 0],'b');
set(h,'facecolor','flat','FaceVertexCData',z)
%for k = 1:length(h)
%    zdata = h(k).ZData;
%    h(k).CData = zdata;
%    h(k).FaceColor = 'interp';
%end
set(h,'LineWidth', 0.00001);
