#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457


"""基于形态识别
"""
from __future__ import print_function
import sys
import boll_fencang
import pd_help
import myredis, agl, help, stock, backtest_policy, ui,account as ac, sign_observation as so
if sys.version > '3':
    import stock_pinyin3 as jx
else:
    import stock_pinyin as jx
from backtest_runner import BackTestPolicy
#import tushare as ts
import datetime
import pandas as pd
import numpy as np
import talib
from stock import DataSources
from pypublish import publish
import pattern_recognition as pr

class Strategy_Boll_Pre(boll_fencang.BollFenCangKline):
    """boll分仓"""
    def setParams(self, *args, **kwargs):
        """定义策略参数"""
        self.trade_num = [0.02, 0.04]   #占总资金比率
        self.trade_ratio = 0.01    #价格区间的比率
        self.trade_four=[-0.06, 0.04]
        self.trade_adx = 40
        #必须实现
        if sys.version > '3':
            for k, v in kwargs.items():
                setattr(self, k, v)
        else:
            for k, v in kwargs.iteritems():
                setattr(self, k, v)        
        #系统开关
        self.is_tick_report = False     #显示中间过程
    def AllowCode(self, code):
        #return False
        #self._log(code)
        return code == '300033'
    def OnFirstRun(self):
        """回测调用函数， 在第一个bar时调用， 先建立底仓"""
        assert(self.is_backtesting)
        code = self.data.get_code()
        df_hisdat = self.data.get_hisdat(code)
        #这里取不到开盘价， 用昨收盘代替
        price = float(df_hisdat.iloc[-1]['c'])
        account = self._getAccount()
        account_mgr = ac.AccountMgr(account, price, code)
        num = ac.ShouShu(account_mgr.total_money()*0.5/price)
        account._buy(code, price, num, self.getCurTime())    
    def OnCalcTech(self, df_hisdat, df_five_hisdat, df_fenshi):
        self.calc_tech['four'] = stock.FOUR(df_five_hisdat['c'])
        self.calc_tech['boll'] = stock.TDX_BOLL(df_five_hisdat['c'])
        highs, lows, closes = df_five_hisdat['h'], df_five_hisdat['l'], df_five_hisdat['c']
        self.calc_tech['adx'] = stock.TDX_ADX(highs, lows, closes)        
        
    def Run(self):
        """
        """
        #self._log('Strategy_Boll_Pre')

        #以下为交易测试
        code = self.data.get_code()	#当前策略处理的股票
        self.code = code
        if not self.is_backtesting and not self.AllowCode(code):
            return

        self._log(self.getCurTime())
        df_hisdat = self.data.get_hisdat(code)	#日k线
        df_five_hisdat = self.data.get_hisdat(code, dtype='5min')	#5分钟k线
        if len(df_five_hisdat)<=30:
            return

        account = self._getAccount()	#获取交易账户
        price = float(df_five_hisdat.iloc[-1]['c'])    #当前股价
        closes = df_hisdat['c']
        yestoday_close = closes[-2]	    #昨日收盘价
        account_mgr = ac.AccountMgr(account, price, code)
        trade_num = ac.ShouShu(account_mgr.init_money()*self.trade_num[0]/price)

        # 指标计算
        index = len(df_five_hisdat)
        four = self.getCalcTech('four', index)
        upper, middle, lower = self.getCalcTech('boll', index)
        df_five_hisdat.is_copy = False
        df_five_hisdat['boll_up'] = upper
        df_five_hisdat['boll_mid'] = middle
        df_five_hisdat['boll_lower'] = lower
        adx = self.getCalcTech('adx', index)
        self._log('boll : %.2f,%.2f,%.2f'%(upper[-1], middle[-1],lower[-1]))
        boll_w = abs(upper[-1]-lower[-1])/middle[-1]*100
        #zz_up = stock.ZigZag(upper[-60:], percent=.1)
        #zz_low = stock.ZigZag(lower[-60:], percent=0.1)
        boll_poss = [
            upper[-1],
         (upper[-1] - middle[-1])/2+middle[-1],
         middle[-1],
         (middle[-1] - lower[-1])/2+lower[-1],	     
         lower[-1],
        ]
        self.tech = np.array(df_five_hisdat['c']), four, adx
        four = four[-1]
        adx = adx[-1]
        self._log('boll_poss: %.2f, %.2f boll_w=%.2f adx=%.2f'%(boll_poss[0], boll_poss[1], boll_w, adx))
        if np.isnan(four):
            return

        #形态识别
        #shape_is_matched = True
        shape_is_matched = False
        if price > boll_poss[2]:
            base_boll_up = pr.get_boll_up_base()
            recognizer = pr.Recognize_boll(base_boll_up, df_five_hisdat)
            shape_is_matched = recognizer.is_matched()
        else:
            base_boll_lower = pr.get_boll_lower_base()
            recognizer = pr.Recognize_boll(base_boll_lower, df_five_hisdat)
            shape_is_matched = recognizer.is_matched()
        
        #帐户信息
        pre_price = account_mgr.last_chengjiao_price(is_sell=-1) #上一个成交的价位
        pre_buy_price = account_mgr.last_chengjiao_price(is_sell=0)
        if np.isnan(pre_buy_price) :
            pre_buy_price = pre_price
        pre_sell_num = account_mgr.last_chengjiao_num()  #上次的成交数量
        pre_pre_price = account_mgr.last_chengjiao_price(index=-2)
        sell_count = account_mgr.queryTradeCount(1)
        buy_count = account_mgr.queryTradeCount(0)
        chen_ben = account_mgr.get_BuyAvgPrice()    #买入成本
        yin_kui = account_mgr.yin_kui()		    #盈亏成本
        canwei = account_mgr.getCurCanWei()

        #信号判断
        num = 0
        #卖
        if so.assemble(
            #price > boll_poss[1]*1.001,
                        price > pre_price*(1+self.trade_ratio),
                       #price > boll_poss[2],
                       #price > self.max_buy_price*(1+self.trade_ratio),
                       #boll_w > 3.5,
                       #adx > self.trade_adx,
                       #four > self.trade_four[1],
                       #sell_count < 2,
                       #pr.horizontal(df_five_hisdat),
                       shape_is_matched,
                       #0,
                       ):
            num = -trade_num
        #if so.assemble(price > boll_poss[0] , 
                       #price > pre_price*(1+self.trade_ratio),
                       ##price > self.max_buy_price*(1+self.trade_ratio), 
                       #boll_w > 3.5,∂
                       ##adx>60,
                       ##four > self.trade_four[1],
                       ##sell_count < 2,
                       ##self.trade_status == self.enum.nothing,
                       ##0,
                       #):
            #if pre_sell_num>0:
                #num = (pre_sell_num * self.trade_num_ratio)
            #else:
                #num = ac.ShouShu(account_mgr.getCurCanWei() * 0.5)
            #order = 1
 
        #买
        if so.assemble(
            #price < boll_poss[-2]*0.999,
            price < pre_price*(1-self.trade_ratio),
                       #price < boll_poss[2],
                       #price < self.min_sell_price*(1-0.03),
                       #boll_w > 3.5,
                       four < self.trade_four[0],
                       #adx>self.trade_adx,
                       #buy_count < 2,
                       #pr.horizontal(df_five_hisdat),
                       shape_is_matched,
                       #0,
                       ):
            num = trade_num
        #if so.assemble(
                       #price < pre_buy_price*(1-self.trade_ratio),
                       ##price < self.min_sell_price*(1-0.03),
                       ##boll_w > 3.5,
                       ##buy_count < 2,
                       ##self.trade_status == self.enum.nothing,
                       ##adx>70,
                       #four < self.trade_four[0]-0.02,
                       ##0,
                       #):
            ###加仓买入
            #num = self._compensate(trade_num, 0, code)
            ##order = 0

        if abs(num)>0:
            order = num <0 and 1 or 0
            self.order(order, code, price, abs(num))

        #tick report
        if self.is_backtesting and self.is_tick_report:
            self._getAccount().TickReport(df_five_hisdat, 'win')
        return	

    #----------------------------------------------------------------------
    def _getAccount(self):
        if self.is_backtesting:
            return self.data.account	#LocalAccount
        return tc.TcAccount(self.data)  
    def _compensate(self, num, bSell, code):
        """回归初始仓位, 补偿损失的仓位, 在大涨或大跌时调用
        return: int 新的交易数量"""
        account = self._getAccount()
        account_mgr = ac.AccountMgr(account, np.nan, code)
        #获取初始仓位
        initCanWei = account_mgr.getInitCanWei()
        #获取当前仓位
        curCanWei = account_mgr.getCurCanWei()
        if bSell:
            if curCanWei - num > initCanWei:
                num = curCanWei - initCanWei
                print(self.getCurTime(), '补偿数%d'%num, bSell)
        else:
            if curCanWei + num < initCanWei:
                num = initCanWei - curCanWei
                print(self.getCurTime(), '补偿数%d'%num, bSell)
        return num

    def order(self, bSell, code, price, num):
        """判断同一区间是否已经有委托, 同时计算区间交易部分的买入均价
        bSell: int 不能使用boolean
        return True 下单， 
        return False 但同一区域已经下单的， 放弃下单"""
        assert(not isinstance(bSell, bool))

        return self._getAccount().Order(bSell, code, price, num)
    def Report(self):
        """报告技术指标"""
        if not hasattr(self, 'tech'):
            return
        closes, four, adx = self.tech
        assert(len(closes) == len(four))
        cur_pl = self.pl
        #adx = stock.GuiYiHua(adx)
        df = pd.DataFrame(adx, columns=['adx'])
        #df['adx'] = adx
        df = stock.GuiYiHua(df)
        df['four'] = four*10
        df['close'] = stock.GuiYiHua(closes - np.min(closes))
        #df.index = pd.DatetimeIndex(df.index)
        df.plot()
        cur_pl.show()
        cur_pl.close()

def Run(codes, task_id=0):
    #agl.LOG('sdf中')
    #codes = ['300033']
    def fnSample(code, dtype='5'):
        import warp_pytdx as tdx
        if dtype=='5':
            df = tdx.getFive(code)
            df = df.sort_index()
            return df
        if dtype=='d':
            df = tdx.getHisdat(code)
            df = df.sort_index()
            return df
    
    def setParams(s):
        if 0: s = Strategy_Boll
        s.setParams(
            pl=publish.Publish(),
        )
    backtest_policy.test_strategy(codes, Strategy_Boll_Pre, setParams,
                                  start_day='2018-11-1', end_day='',
                                  #start_day='2017-12-2', end_day='2017-12-13', 
                                  mode=BackTestPolicy.enum.hisdat_mode|BackTestPolicy.enum.hisdat_five_mode,
                                  datasource_mode=DataSources.datafrom.custom,
                                  datasource_fn=fnSample
                                  )

def main_run():        
    cpu_num = 1
    codes = stock.get_codes(stock.myenum.randn, cpu_num)
    #agl.startDebug()
    if agl.IsDebug():
        codes = [jx.HCGD]
    exec(agl.Marco.IMPLEMENT_MULTI_PROCESS)

if __name__ == "__main__":
    main_run()