function AvoidAreaClash = JudgeAvoidAreaClash(PlanningEvents)
%函数输入为事件的相对开始时间，相对结束时间
%输出为是否满足异常区约束

%读入异常区参数，C矩阵的第一列为异常区的相对开始时间，第二列为相对结束时间。
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
%判断事件是否在异常区内
AvoidAreaTime = 0;
for jj=1:size(PlanningEvents,1)
    for kk=1:size(C,1)
        StartTime=PlanningEvents(jj,2);
        EndTime= PlanningEvents(jj,3);
        if EndTime<C(kk,1)
            break
        end
        if StartTime>C(kk,2)
            continue
        end
        AvoidAreaStart=max(StartTime,C(kk,1));
        AvoidAreaEnd=min(EndTime,C(kk,2));
        if (AvoidAreaStart <= AvoidAreaEnd)
			AvoidAreaTime = AvoidAreaEnd - AvoidAreaStart+AvoidAreaTime;		
        end
    end
    if (AvoidAreaTime ~= 0)
        AvoidAreaClash=true;
    end
end
