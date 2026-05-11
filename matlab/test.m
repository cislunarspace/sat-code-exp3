[num,txt] = xlsread('C:\Users\10737\Desktop\Planning\AvoidAeraWindow.csv');
strdate=txt(2:end,2);
t=datetime(strdate);
DateVector = datevec(t);
y=DateVector(1,2);
r=DateVector(1,3);
h=DateVector(1,4);
m=DateVector(1,5);
C=zeros(size(DateVector,1),2);
C(1,1)=m*60+h*3600;
C(1,2)=C(1,1)+num(1,4)*60;
AvoidAreaClash=false;
for ii=1:size(DateVector,1)-1
    i=ii+1;
    if DateVector(i,2)==DateVector(ii,2)
        C(i,1)=C(ii,1)+(DateVector(i,3)-DateVector(ii,3))*86400+(DateVector(i,4)-DateVector(ii,4))*3600+(DateVector(i,4)-DateVector(ii,4))*60;
    else
        C(i,1)=C(ii,1)+86400+(DateVector(i,4)-DateVector(ii,4))*3600+(DateVector(i,4)-DateVector(ii,4))*60;
    end
    C(i,2)=C(i,1)+num(i,4)*60;
end