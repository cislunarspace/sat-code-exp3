B = xlsread('C:\Users\ouyan\课程资料\2026春航天任务分析与设计\航天任务课程实验资料汇总\大作业3\Planning\data\planningevents.xlsx');
b = JudgeAvoidAreaClash(B);
c = JudgeSolarClash(B);
