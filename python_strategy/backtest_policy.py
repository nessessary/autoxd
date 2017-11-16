#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os
import numpy as np
import pandas as pd
import sys, datetime
import live_policy,stock,agl,help,account
from dateutil.parser import parse
 
class Backtest(live_policy.Live, account.BackTestingDelegate):
    """兼容在线的回测"""
    def __init__(self):
        pass
    def get_code(self):
        return self.code
    def set_code(self, code, day, tick):
        """tick: 570等"""
        self.code = code
        self.day = day    #当前日期，字符串
        self.tick = stock.StockTime.s_ToStrTime(tick, day)   
    def createAccount(self, account_type, username, pwd):
        self.account = account.LocalAcount(self)
        return self.account
    def set_datasource(self, panel_hisdat, dict_fenshi, panel_fiveminhisdat):
        self.panel_hisdat = panel_hisdat
        if 0: self.panel_hisdat = pd.Panel()
        self.dict_fenshi = dict_fenshi
        if 0: self.dict_fenshi = dict()
        self.panel_fiveminhisdat = panel_fiveminhisdat
    def get_hisdat(self, code, dtype='day'):
        """
        dtype: str 5min|day
        return: df"""
        if dtype == '5min':
            return self.get_fiveminhisdat(code)
        return self.panel_hisdat.ix[code][:self.day]
    def get_fenshi(self, code):
        """
        col名字说明：t - 时间 ; b - 买卖 ; p - 价格; v - 手数; d - 多少账号在交易;
        return: pd.DataFrame
        """
        pre_day = help.MyDate.s_Dec(self.day, -10)
        df = self.dict_fenshi[code]
        df = df.ix[pre_day:self.tick]
        return df
    def get_fiveminhisdat(self, code):
        df = self.panel_fiveminhisdat[code]
        return df[:self.tick]
    def get_info(self, code):
        info = stock.StockInfo(code)
        return info
    def get_bankuaisort(self):
        a = np.zeros(500*200, dtype=np.int8)
        l = self.GetBankuaiSort(a)
        s = agl.ArrayToStr(a[:l])
        a = np.array(s.split("|"))[:-1]
        a=a.reshape((len(a)/2, 2))
        df = pd.DataFrame(a)
        df[1] = df[1].astype('float')
        return df
    def getTotalMoeny(self):
        return self.GetTotalMoney(self.account)
    def getCanUseMoney(self):
        return self.GetCanUseMoney(self.account)
    def get_stocklist(self, code):
        a= np.zeros(200, dtype=np.int8)
        l = self.GetStockList(self.account, code, a)
        s = agl.ArrayToStr(a[:l])
        return s.split('|')
    def buy(self, code, num, price):
        date = self.tick
        return self.account.buy(code, price, num, date)
    def sell(self, code, num, price):
        date = self.tick
        return self.account.sell(code, price, num, date)
    def IsWeituo(self, code, num, price):
        """对于模拟分时买入的判断， """
        order = self.account.getLastWeiTuo(code)
        if order.num == num and agl.Eq(order.price, price):
            return True
        return False
    def getLastWeituo(self, code):
        a= np.zeros(200, dtype=np.int8)
        l = self.GetLastWeituo(self.account, code, a)
        s= agl.ArrayToStr(a[:l])
        return s.split('|')
    #account.BackTestingDelegate
    def getCurTickTime(self):
        return self.tick
def main(args):
    print "end"

def MultiProcessRun(cpu, codes, fn_name, mod):
    """多进程执行, 并行
    cpu : CPU 数量
    codes : list 股票代码
    fn_name : 执行函数
    mod : 调用者__file__
    """
    from MultiSubProcess import MultiSubProcess
    multi = MultiSubProcess.MultiSubProcess()
    multi.Map(cpu, mod, fn_name, codes)
    multi.Run()	  
def test_strategy(codes, strategy_name, cbfn_setparams=None, day_num=20, mode=0, start_day='', end_day=''):	
    """strategy_name: str 通过策略名称来构造策略
    cbfn_setparams: callback function 回调函数 fn(strategy) 用该函数来重新设置参数
    day_num: 当前天或者数据集的最后一天向前推的天数， 同时会修正为数据集有效的第一天
    mode : enum/int tick/hisdat
    """
    import backtest_runner
    if mode == 0:
        mode = backtest_runner.BackTestPolicy.enum.tick_mode
    for code in codes:
        agl.Print( code, stock.GetCodeName(code))
        p = backtest_runner.BackTestPolicy(mode)
        p.SetStockCodes([code])
        backtesting = Backtest()
        account = backtesting.createAccount(account_type=None, username=None, pwd=None)
        #p.Regist(Strategy_basesign(backtesting, is_backtesting=True))
        strategy = strategy_name(backtesting, is_backtesting=True, mode=mode)
        #设置策略参数
        if cbfn_setparams is not None:
            cbfn_setparams(strategy)
        else:
            strategy.setParams()
        print(strategy.getParams())
        p.Regist(strategy)
        #p.Regist(Strategy_Trade(backtesting, is_backtesting=True))
        cur_day = agl.CurDay() 
        if end_day != '':
            cur_day = end_day
        d1, d2 = help.MyDate.s_Dec(cur_day, -20),cur_day
        if start_day != '':
            d1 = start_day
        def getTradeDay(d1, d2, dtype=backtest_runner.BackTestPolicy.enum.hisdat_mode):
            """确定是交易日
            return: (d1, d2)"""
            try:
                if dtype == backtest_runner.BackTestPolicy.enum.hisdat_mode:
                    df = stock.getHisdatDataFrameFromRedis(code, d1, d2)
                else:
                    df = stock.getFenshiDfUseRedis(code, d1,d2)
                if len(df) == 0:
                    #在指定日期内没有数据，应该是新股或次新股
                    return d2,d2
                d2 = agl.datetime_to_date(df.index[-1])
                if agl.DateTimeCmp(d1, agl.datetime_to_date(df.index[0])) <0:
                    d1 =  agl.datetime_to_date(df.index[0])
            except:
                pass
            return d1, d2
            #for i in range(10):
                #if d1 in df.index:
                    #return d1,d2
                #else:
                    #d1 = help.MyDate.s_Dec(d1, 1)
        d1,d2 = getTradeDay(d1,d2, mode)	
        if start_day == '':
            #再次修正为已有数据的20天
            d1 = help.MyDate.s_Dec(d2, -day_num)
        d1,d2 = getTradeDay(d1,d2, mode)	
        
        if d1 != d2:        
            print d1, d2
            p.Run(d1, d2)    
        else:
            print '没有数据'

if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)