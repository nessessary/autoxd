#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os


"""在线策略入口"""
import numpy as np
import sys
import agl,stock,help,ui
import backtest_policy
import pylab as pl

_ISRUNING = False       #查询是否回测状态
class BackTestPolicy:
    """回测入口"""
    class enum:
        tick_mode = 0           #每个tick都处理
        hisdat_mode = 1         #只处理日线，close
        hisdat_five_mode = 2    #用&来判断
    def __init__(self, mode=0):
        global _ISRUNING
        _ISRUNING = True
        self.policys = []
        self.mode = mode    #回测模式
        self.panel_fiveminHisdat = None
    def Regist(self, policy):
        """添加策略"""
        self.policys.append(policy)
    def initData(self,start_day, end_day):
        #数据初始化, 生成数据面板
        days = (start_day, end_day)
        hisdat_start_day = help.MyDate.s_Dec(start_day, -100)
        self.panel_hisdat = stock.DataSources.getHisdatPanl(self.codes, 
                                                            (hisdat_start_day, end_day))

        if start_day == '':
            start_day = hisdat_start_day
        fenshi_start_day = help.MyDate.s_Dec(start_day, -5)
        fenshi_days = (fenshi_start_day, help.MyDate.s_Dec(end_day, 1))
        if self.mode & self.enum.hisdat_five_mode == self.enum.hisdat_five_mode:
            self.panel_fiveminHisdat = stock.DataSources.getFiveMinHisdatPanl(
                self.codes, fenshi_days)   

        if self.mode == BackTestPolicy.enum.tick_mode:
            self.dict_fenshi = stock.DataSources.getFenshiPanl(self.codes, fenshi_days)
        else:
            self.dict_fenshi = None
            #self.panel_fiveminHisdat = None
        for policy in self.policys:
            policy.data.set_datasource(self.panel_hisdat, self.dict_fenshi, \
                                       self.panel_fiveminHisdat)
        #修正日期
        if self.mode & self.enum.hisdat_mode == self.enum.hisdat_mode:
            if self.mode & self.enum.hisdat_five_mode == self.enum.hisdat_five_mode:
                df = self.panel_fiveminHisdat[self.codes[0]]
            else:
                df = self.panel_hisdat[self.codes[0]]
        else:
            df = self.dict_fenshi[self.codes[0]]
        if len(df) > 0:
            end_day = agl.datetime_to_date(df.index[-1])
        start_day = help.MyDate.s_Dec(start_day , 2)
                
        return start_day, end_day
    def Run(self, start_day, end_day, is_report=False):
        #try:
            #按照天来排
            #self._TravlDay('2014-5-1','2015-8-1')
            self._OnFirstRun(start_day)
            self._TravlDay(start_day, end_day)
            #生成一份收盘价给统计用
            list_closes = []
            for code in self.codes:
                df = self.panel_hisdat[code]
                assert(len(df)>0)
                list_closes.append((code, df.ix[-1]['c']))
            #输出账号结果
            for policy in self.policys:
                if 0: policy = qjjy.Strategy(data)
                #policy.get().account.Report()
                #policy.Report(start_day, end_day)
                close = self.panel_hisdat[self.codes[0]].iloc[-1]['c']
                self._Report(policy, start_day, end_day, close)
        #except Exception as e:
            #print str(e)
    def _IsKaiPan(self, code, day):
        """判断当前天是否开盘"""
        return day in self.panel_hisdat[code].index
    def _OnFirstRun(self, start_day):
        """允许策略在开始前有一个事件"""
        ts = list(range(570,690)) + list(range(779, 900+1))
        for code in self.codes:
            for strategy in self.policys:
                if self.mode == self.enum.tick_mode:
                    #分时遍历, 按分钟走
                    if hasattr(strategy, 'OnFirstRun'):
                        strategy.data.set_code(code, start_day, ts[0])
                        strategy.OnFirstRun()
                if self.mode & self.enum.hisdat_mode == self.enum.hisdat_mode:
                    if hasattr(strategy, 'OnFirstRun'):
                        strategy.data.set_code(code, start_day, ts[0])
                        strategy.OnFirstRun()         
                if hasattr(strategy, 'OnCalcTech'):
                    df_five = self.panel_fiveminHisdat[code] if self.panel_fiveminHisdat is not None else None
                    df_fenshi = self.dict_fenshi[code] if self.dict_fenshi is not None else None
                    strategy.OnCalcTech(self.panel_hisdat[code], df_five, df_fenshi)
    def _TravlTick(self, day):
        ts = [[570,690],[779,900]]
        ts = list(range(570,690)) + list(range(779, 900+1))
        #按照分钟来遍历
        for code in self.codes:
            #print code
            if not self._IsKaiPan(code, day):
                continue
            for strategy in self.policys:
                if self.mode == self.enum.tick_mode:
                    df = self.dict_fenshi[code].ix[day] #以时间为索引
                    #fenshi_length = len(df) #只迭代当天的
                    #分时遍历, 按分钟走
                    for t in ts:
                        strategy.data.set_code(code, day, t)
                        strategy.Run()
                if self.mode&self.enum.hisdat_mode == self.enum.hisdat_mode:
                    if self.mode & self.enum.hisdat_five_mode == self.enum.hisdat_five_mode:
                        #按5分钟遍历
                        for t in  range(575, 900, 5):
                            strategy.data.set_code(code, day, t)
                            strategy.Run()
                    else:
                        strategy.data.set_code(code, day, 900-1)
                        strategy.Run()
    def _TravlDay(self, start_day, end_day):
        """遍历天， 开始时间， 结束时间"""
        start_day = help.MyDate(start_day)
        #start_day.Add(3)    #否则取昨收盘会失败
        end_day = help.MyDate(end_day)
        while True:
            day = start_day.ToStr()
            #print day
            self._TravlTick(day)
            if start_day.Next() > end_day.GetDate():
                break
    def _Report(self, policy, start_day, end_day, last_close):
        policy._getAccount().Report(end_day, last_close, True)
        #绘制图形
        if hasattr(policy, 'Report'):
            policy.Report()
        #end_day = help.MyDate.s_Dec(end_day, 1)
        #bars = stock.CreateFenshiPd(self.code, start_day, end_day)
        if self.mode == 0:
            bars = self.dict_fenshi[self.codes[0]]
            if len(bars) == 0:
                return
            bars = bars.resample('1min').mean()
            bars['c'] = bars['p']
        else:
            #日线
            bars = self.panel_hisdat[self.codes[0]]
            if self.mode & self.enum.hisdat_five_mode == self.enum.hisdat_five_mode:
                bars = self.panel_fiveminHisdat[self.codes[0]]
        bars['positions'] = 0
        bars = bars.dropna()
        df = policy._getAccount().ChengJiao()
        df_zhijing = policy._getAccount().ZhiJing()
        init_money = df_zhijing.iloc[0]['资产']
        df_zhijing = df_zhijing[bars.index[0]:]
        df_changwei = policy._getAccount().ChengJiao()
        cols = ['买卖标志','委托数量']
        df_flag = df_changwei[cols[0]].map(lambda x: x == '证券卖出' and -1 or 1)
        df_changwei[cols[1]] *= df_flag
        changwei = df_changwei[cols[1]].cumsum()
        if self.mode == self.enum.hisdat_mode:
            df.index = df.index.map(lambda x: agl.datetime_to_date(x))
        bars.is_copy = False
        for i in range(len(df)):
            index = df.index[i]
            bSell = bool(df.iloc[i]['买卖标志']=='证券卖出')
            if index in bars.index:
                bars.at[index,'positions'] = agl.where(bSell, -1, 1)
        #同步资金到bar
        df_zhijing.is_copy = False
        df_zhijing['changwei'] = changwei
        if self.mode == self.enum.hisdat_mode:
            df_zhijing.index = df_zhijing.index.map(lambda x: agl.datetime_to_date(x))
        bars = bars.join(df_zhijing)
        bars = bars.fillna(method='pad')
        #同步价格的动态总资产
        bars['资产'] = bars['可用']+bars['changwei']*bars['c']
        zhican = (bars['资产']-init_money)/init_money*100
        zhican = zhican.fillna(0)
        if sys.version>'3':
            title = '%s %s'%(self.codes[0], stock.GetCodeName(self.codes[0]))
        else:
            title = '%s %s'%(self.codes[0], stock.GetCodeName(self.codes[0]).decode('utf8'))
        ui.TradeResult_Boll(agl.where(policy.pl, policy.pl, pl), bars,  \
                            stock.GuiYiHua(zhican),\
                            stock.GuiYiHua(bars['changwei']),
                            title=title)
        
        if policy.pl is not None:
            #if policy.pl.explicit:
                policy.pl.publish()
    def SetStockCodes(self, codes):
        """对这些codes进行回测"""
        self.codes = codes
    @staticmethod
    def Test():
        print(u'入口由策略自身执行')
        
def main(args):
    agl.tic()
    BackTestPolicy.Test()
    agl.toc()
    print("end")
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)