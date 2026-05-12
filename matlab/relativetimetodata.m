[num, txt] = xlsread('C:\Users\10737\Desktop\panduan\SolarAngle.csv');
B = xlsread('C:\Users\10737\Desktop\panduan\planningevents.xlsx');
strdate = txt(2 : end, 1);
t = datetime(strdate);
DateVector = datevec(t);
x = DateVector(1, 4);
A = zeros(size(DateVector, 1), 2);
PlanningEvents = zeros(size(DateVector, 1), 2);
A(1, 2) = 0;
starttime = zeros(size(B, 1), 6);
endtime = zeros(size(B, 1), 6);
for ii = 1 : size(DateVector, 1)
    DateVector(ii, 4) = 0;
    i = ii + 1;
    A(i, 2) = 86400 + A(ii, 2);
end

for ii = 1 : size(B, 1)
    for jj = 1 : size(A, 1) - 1
        j = jj + 1;
        if B(ii, 1) > A(jj, 2) && B(ii, 1) < A(j, 2)
            delta = B(ii, 1) - A(jj, 2);
            if delta >= 3600
                h_delta = (delta - mod(delta, 3600)) / 3600;
                if mod(delta, 3600) >= 60
                    min_delta = (mod(delta, 3600) - mod(mod(delta, 3600), 60)) / 60;
                    s_delta = mod(mod(delta, 3600), 60);
                elseif mod(delta, 3600) < 60
                    s_delta = mod(delta, 3600);
                end
            end

            if delta < 3600
                h_delta = 0;
                if delta >= 60
                    min_delta = (delta - mod(delta, 60)) / 60;
                    s_delta = mod(delta, 60);
                elseif delta < 60
                    s_delta = delta;
                end
            end
            starttime(ii, 1) = DateVector(jj, 1);
            starttime(ii, 2) = DateVector(jj, 2);
            starttime(ii, 3) = DateVector(jj, 3);
            starttime(ii, 4) = DateVector(jj, 4) + h_delta;
            starttime(ii, 5) = DateVector(jj, 5) + min_delta;
            starttime(ii, 6) = DateVector(jj, 6) + s_delta;
        end
    end
end

for ii = 1 : size(B, 1)
    for jj = 1 : size(A, 1) - 1
        j = jj + 1;
        if B(ii, 2) > A(jj, 2) && B(ii, 2) < A(j, 2)
            delta = B(ii, 2) - A(jj, 2);
            if delta >= 3600
                h_delta = (delta - mod(delta, 3600)) / 3600;
                if mod(delta, 3600) >= 60
                    min_delta = (mod(delta, 3600) - mod(mod(delta, 3600), 60)) / 60;
                    s_delta = mod(mod(delta, 3600), 60);
                elseif mod(delta, 3600) < 60
                    s_delta = mod(delta, 3600);
                end
            end

            if delta < 3600
                h_delta = 0;
                if delta >= 60
                    min_delta = (delta - mod(delta, 60)) / 60;
                    s_delta = mod(delta, 60);
                elseif delta < 60
                    s_delta = delta;
                end
            end
            endtime(ii, 1) = DateVector(jj, 1);
            endtime(ii, 2) = DateVector(jj, 2);
            endtime(ii, 3) = DateVector(jj, 3);
            endtime(ii, 4) = DateVector(jj, 4) + h_delta;
            endtime(ii, 5) = DateVector(jj, 5) + min_delta;
            endtime(ii, 6) = DateVector(jj, 6) + s_delta;
        end
    end
end

