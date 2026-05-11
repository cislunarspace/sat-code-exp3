function SolarClash = JudgeSolarClash(PlanningEvents)
%函数输入为事件的相对开始时间，相对结束时间
%输出为是否满足轨道阳光角约束
%读入阳光角参数，SolerRelativetime矩阵的第一列为阳关角的数值，第二列为阳光角相对开始时间。
[num,txt] = xlsread('C:\Users\10737\Desktop\Planning\SolarAngle.csv');
strdate=txt(2:end,1);
t=datetime(strdate);
DateVector = datevec(t);
x=DateVector(1,4);
SolerRelativetime=zeros(size(DateVector,1),2);
SolerRelativetime(1,2)=0;
SolerRelativetime(2,2)=8*3600;
for ii=2:size(DateVector,1)-1
    i=ii+1;
    SolerRelativetime(i,2)=86400+SolerRelativetime(ii,2);
end
for ii=1:size(DateVector,1)
    SolerRelativetime(ii,1)=num(ii,1);
end
SolerRelativetime
%阳光角约束
SolarClash=false; 
for ii=1:size(SolerRelativetime,1)-1
    for jj=1:size(PlanningEvents,1)
        m_MinSolarAngle=PlanningEvents(jj,4);
        m_MaxSolarAngle=PlanningEvents(jj,5);
        StartTime=PlanningEvents(jj,2);
        EndTime= PlanningEvents(jj,3);
        %事件开始时间在两个阳光角之间
        if StartTime>=SolerRelativetime(ii,2) && StartTime<=SolerRelativetime(ii+1,2)
            Radio=(EndTime-SolerRelativetime(ii,2))/86400;
            StartAngle=(SolerRelativetime(ii+1,1)-SolerRelativetime(ii,1))*Radio+SolerRelativetime(ii,1);%当前事件开始时刻的阳光角
            EndAngle=SolerRelativetime(ii+1,1);%约束时间段最终阳光角
            %保证StartAngle<EndAngle
            if StartAngle>EndAngle
                minangle=EndAngle;
                EndAngle=StartAngle;
                StartAngle=minangle;
            end
            %判断[StartAngle,EndAngle]是否满足约束
            if m_MinSolarAngle==0%事件需求区间为[-m_MaxSolarAngle,m_MaxSolarAngle]
                if StartAngle<-m_MaxSolarAngle || EndAngle>m_MaxSolarAngle
                    SolarClash = true;
                end
            else%最小值不等于0
           %既不在区间[-m_MaxSolarAngle, -m_MinSolarAngle]也不在区间[m_MinSolarAngle, m_MaxSolarAngle]
                if (StartAngle < -m_MaxSolarAngle || EndAngle > -m_MinSolarAngle) && (StartAngle < m_MinSolarAngle || EndAngle > m_MaxSolarAngle)
                    SolarClash = true;
                    break
                end
            end
        elseif (EndTime>=SolerRelativetime(ii,2) && EndTime<=SolerRelativetime(ii+1,2))%换了时间区间
            Radio=(EndTime-SolerRelativetime(ii,2))/86400;
            StartAngle=SolerRelativetime(ii,1);%当前事件开始时刻的阳光角
            EndAngle=(SolerRelativetime(ii+1,1)-SolerRelativetime(ii,1))*Radio+SolerRelativetime(ii,1); %约束时间段最终阳光角
            %保证StartAngle<EndAngle
            if StartAngle>EndAngle
                minangle=EndAngle;
                EndAngle=StartAngle;
                StartAngle=minangle;
            end
            if m_MinSolarAngle==0%事件需求区间为[-m_MaxSolarAngle,m_MaxSolarAngle]
                if StartAngle<-m_MaxSolarAngle || EndAngle>m_MaxSolarAngle
                    SolarClash = true;
                end
            else%最小值不等于0
           %既不在区间[-m_MaxSolarAngle, -m_MinSolarAngle]也不在区间[m_MinSolarAngle, m_MaxSolarAngle]
                if (StartAngle < -m_MaxSolarAngle || EndAngle > -m_MinSolarAngle) && (StartAngle < m_MinSolarAngle || EndAngle > m_MaxSolarAngle)
                    SolarClash = true;
                    break
                end
            end
        elseif (StartTime<SolerRelativetime(ii,2) && EndTime>SolerRelativetime(ii+1,2))%换了时间区间
            Radio=(EndTime-SolerRelativetime(ii,2))/86400;
            StartAngle=SolerRelativetime(ii,1);%当前事件开始时刻的阳光角
            EndAngle=SolerRelativetime(ii+1,1); %约束时间段最终阳光角
            %保证StartAngle<EndAngle
            if StartAngle>EndAngle
                minangle=EndAngle;
                EndAngle=StartAngle;
                StartAngle=minangle;
            end
            if m_MinSolarAngle==0%事件需求区间为[-m_MaxSolarAngle,m_MaxSolarAngle]
                if StartAngle<-m_MaxSolarAngle || EndAngle>m_MaxSolarAngle
                    SolarClash = true;
                end
            else%最小值不等于0
           %既不在区间[-m_MaxSolarAngle, -m_MinSolarAngle]也不在区间[m_MinSolarAngle, m_MaxSolarAngle]
                if (StartAngle < -m_MaxSolarAngle || EndAngle > -m_MinSolarAngle) && (StartAngle < m_MinSolarAngle || EndAngle > m_MaxSolarAngle)
                    SolarClash = true;
                    break
                end
            end
        end
        
        %最后一个阳光角约束
	    lastangle = size(SolerRelativetime,1) - 1;
		if StartTime > SolerRelativetime(lastangle+1,2)%事件开始时刻大于最后一个阳光角约束的结束时间
			SolarClash = true;
        end
    end
end


