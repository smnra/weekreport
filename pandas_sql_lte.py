﻿#coding=utf-8
from  datetime  import datetime
import os
import arrow
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import SMTPProxy
from sqlalchemy import create_engine
from matplotlib.dates import AutoDateLocator, DateFormatter


filename = []    #定义邮件附件文件名列表

def getDateRange():
    '''
    #获取参数(默认为当天)所在月份的第一个完整周 周一的日期
    '''
    now = arrow.now()                                                        #当前时间
    rangeDate={}                                                             #定义返回值  字典
    rangeDate['today'] = arrow.now().format('YYYYMMDD')                 #今日的日期

    lastMonth_1st_day = now.floor('month').replace(months = -1)             #上个月1号的日期
    thisMonth_1st_day = now.floor('month')                                  #这个月1号的日期
    nextMonth_1st_day = now.floor('month').replace(months = +1)             #下个月1号的日期
    lastWeek_Monday = now.replace(weeks = -1).floor('week')             #上一周周一的日期
    thisWeek_Monday = now.floor('week')                                 #这一周周一的日期
    if thisMonth_1st_day.isoweekday() == 1 :                                #如果这个月的1号是周一,
        thisMonth_1st_Monday = now.floor('month')                           #则这个月的第一个完整周 的 周一的日期 就是当月的1号的日期
    else :
        thisMonth_1st_Monday = now.floor('month').replace(weeks = +1).floor('week')      #否则这个月的第一个完整周 的 周一的日期 就是当月1号所在的下一周的周一的日期

    if thisWeek_Monday - thisMonth_1st_Monday == thisWeek_Monday - thisWeek_Monday :       #如果 这一周周一的日期  减去这个月的第一个完整周 周一的日期 如果结果等于0
        rangeDate['startDate'] = lastMonth_1st_day.format('YYYYMMDD')               #开始时间就是上个月1号
        rangeDate['endDate'] = thisMonth_1st_Monday.format('YYYYMMDDH')               #结束时间就是这个月的第一个完整周 周一的日期
    else :
        rangeDate['startDate'] = thisMonth_1st_day.format('YYYYMMDD')               #开始时间就是这个月1号
        rangeDate['endDate'] = nextMonth_1st_day.format('YYYYMMDD')                 #结束时间就是这个月的第一个完整周 周一的日期

    return rangeDate

tdate = getDateRange()


#tdate = ['20171201','20171211','20180101']

#用sqlalchemy创建引擎  
sql = "select * from city_lte_day where instr(地市,'FDD')>0  AND  日期>= '" + tdate['startDate'] + "' AND 日期 <  '" + tdate['endDate'] +  "'"
engine = create_engine('mysql+pymysql://root:10300@192.168.3.74:50014/4g_kpi_browsing?charset=utf8')
#df.to_sql('tick_data',engine,if_exists='append')#存入数据库，这句有时候运行一次报错，运行第二次就不报错了，不知道为什么  
df1 = pd.read_sql(sql,engine)    #read_sql直接返回一个DataFrame对象      设置多个index，只要将index_col的值设置为列表


filePath = os.getcwd()  +  '\\' + datetime.today().strftime("%Y%m%d") + '\\4G\\'        #拼接文件夹以当天日期命名
if os.path.exists(filePath):                                                   #判断路径是否存在
    print(u"目标已存在:",filePath)                                                 #如果存在 打印路径已存在,
else:
    os.makedirs(filePath)                                                           #如果不存在 创建目录

writer = pd.ExcelWriter(filePath + tdate['startDate'] + '_' + tdate['endDate'] + '_LTE.xlsx')       #保存表格为excel      文件名称为本月起始日期_结束日期_LTE.xlsx
df1.to_excel(writer,'Sheet1')                                                                  #保存表格为excel
writer.save()                                                                                   #保存表格为excel


plt.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体
plt.rcParams['axes.unicode_minus'] = False #解决保存图像是负号'-'显示为方块的问题


rrc = df1[['日期','地市','rrc建立成功率']]                            #取 '日期','地市','rrc建立成功率' 三列数据
rrcCity = rrc.pivot_table('rrc建立成功率', ['日期'], '地市')         # 数据列为 'rrc建立成功率', '日期' 列不变,把 '地市'这一列 按照内容转换为多列



class CreateChart:
    def createCharts(self,rrcCity,rowName,figIndex,yRange):
        self.rowName = rowName
        self.figIndex = figIndex
        self.yRange = yRange
        self.rrcCity = rrcCity
        self.rrcFig = plt.figure(self.figIndex,figsize=(8,4)) # Create a `figure' instance
        self.rrcAx = self.rrcFig.add_subplot(111) # Create a `axes' instance in the figure
        self.rrcAx.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))      #设置X时间显示格式
        self.rrcAx.set_xticks(pd.date_range(kpiCity.index[0],kpiCity.index[-1])) #设置x轴间隔
        self.rrcHandle = self.rrcAx.plot(self.rrcCity)    #根据dataFream rcCity 中的列 创建多条折线,其中X轴为索引  Y轴为多个列

        '''                                  #设置标签,迭代handles 每一条线 逐个添加标签
        i=0
        for handle in rrcHandle:
            handle.set_label(rrcCity.columns[i])
            i+=1
        '''
        #yRange = [98,100]

        self.rrcAx.spines["right"].set_color("none")                       #设置右轴颜色为none
        self.rrcAx.spines["top"].set_color("none")                       #设置上轴颜色为none
        self.rrcAx.set_title(self.rowName)                              #设置图表标题
        self.rrcFig.autofmt_xdate()                                      #设置x轴时间外观
        plt.ylim(self.yRange)                                            #Y轴 显示范围
        self.rrcAx.legend(self.rrcCity.columns,loc="best", ncol=1, shadow=True)  #设置显示图例 以及图例的位置,级是否有阴影效果
        self.pngName = filePath + tdate['startDate'] + '_' + tdate['endDate'] + '_LTE_' + rowName + '.png'
        self.rrcFig.savefig(self.pngName)    #保存为 本月起始日期_结束日期_LTE_KPI名称.PNG图片



#rrs = CreateChart()
#rrs.createCharts(rrcCity,'rrc建立成功率',"rrc",(99,100))

yRanges = ((98,100),(99,100),(0,1),(0,0.5),(0,1),(00,100),(80,100),(-120,-90),(1000,5000000),(0,100000000))


for i,kpiName in enumerate(df1.columns[2:]):                                #此种for语句 表示 遍历 列表df1.columns[2:],i为序号(1,2,3,4,5....)  kpiName 为列表df1.columns[2:]中的每一个元素
    df1[kpiName] = df1[kpiName].astype(np.float64)                          #类型转换,将列转换为 float64 类型
    kpi = df1[['日期','地市',kpiName]].fillna(0)                           #取 '日期','地市','rrc建立成功率' 三列数据
    kpiCity = kpi.pivot_table(kpiName, ['日期'], '地市').sort_index(ascending=True)           # 数据列为 'rrc建立成功率', '日期' 列不变,把 '地市'这一列 按照内容转换为多列
    kpiChart = CreateChart()
    filename.append(kpiChart.pngName)
    kpiChart.createCharts(kpiCity,kpiName,kpiName,yRanges[i])
    #plt.show()





mailreceiver = [ 'jing.2.zhang@huanuo-nsb.com']
mailcc = [ 'smnra@163.com']
mailTitle = 'LTE ' + tdate['startDate'] + '-' + tdate['endDate'] + ' 周报材料'
mailBody = 'LTE ' + tdate['startDate'] + '-' + tdate['endDate'] + ' 周报材料'
mailAttachments = [filename]

sendmail = SMTPProxy.SendMail(mailreceiver, mailcc, mailTitle, mailBody, mailAttachments)    #邮件发送
sendmail.senmail()
