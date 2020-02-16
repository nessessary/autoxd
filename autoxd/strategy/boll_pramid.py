#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457


"""关于boll分仓策略的实现
只做上升通道， 下降通道暂时不做
1. 正负交易只做一次
2. 回撤到均线时就要回补, 用大的量来弥补
3. 超过限额就不要做波动了
"""
import sys
from autoxd.strategy import pd_help, qjjy
from autoxd import myredis, agl, help, stock, backtest_policy, ui, account as ac, sign_observation as so
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx

from autoxd.backtest_runner import BackTestPolicy
import datetime
import pandas as pd
import numpy as np
import talib
from autoxd.pypublish import publish

class Strategy_Boll_Pre(qjjy.Strategy):
    """boll分仓"""
    class enum:
        """保存上一次的交易状态"""
        nothing = -1
        boll_up = 0
        boll_up_mid = 1
        boll_mid = 2
        boll_down_mid = 3
        boll_down = 4
        zz_up = 5
        zz_down = 6
        zz_hui_bu = 7	#回补
    def setParams(self, *args, **kwargs):
        self.is_tick_report = False
        self.trade_num_use_money_percent = 0.02	    #区间交易数量, 初始资金占比
        self.trade_num_ratio = 3    #二档对于一档的倍数
        self.trade_ratio = 0.02    #区间的比率
        self.lowerhold = 0.5	    #底仓使用的资金
        self.trade_four=[-0.1, 0.3]
        self.is_compensate = False   #仓位补偿
        #必须实现
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        self.min_sell_price = 1000
        self.max_buy_price = 0
        self.trade_status = self.enum.nothing
    def AllowCode(self, code):
        #return False
        #self._log(code)
        return code == '300033'
    def OnFirstRun(self):
        """回测调用函数， 在第一个bar时调用， 先建立底仓"""
        assert(self.is_backtesting)
        code = self.data.get_code()
        df_fenshi = self.data.get_fenshi(code)
        #这里取不到开盘价， 用昨收盘代替
        price = float(df_fenshi.iloc[-1]['p'])
        account = self._getAccount()
        account_mgr = ac.AccountMgr(account, price, code)
        num = ac.ShouShu(account_mgr.total_money()*self.lowerhold/price)
        account._buy(code, price, num, self.getCurTime())    
    def Run(self):
        """
        """
        #self._log('Strategy_Boll_Pre')

        #以下为交易测试
        code = self.data.get_code()	#当前策略处理的股票
        self.code = code
        if not self.is_backtesting and not self.AllowCode(code):
            return

        df_hisdat = self.data.get_hisdat(code)	#日k线
        df_five_hisdat = self.data.get_hisdat(code, dtype='5min')	#5分钟k线
        df_fenshi = self.data.get_fenshi(code)	#日分时
        if len(df_fenshi) == 0:
            self.data.log(code+u"未取到分时数据")
            return
        account = self._getAccount()	#获取交易账户
        price = float(df_fenshi.tail(1)['p'])    #当前股价
        closes = df_hisdat['c']
        yestoday_close = closes[-2]	    #昨日收盘价
        zhangfu = stock.ZhangFu(price, yestoday_close)
        self._log('price=%.2f %s %s'%(price, str(df_fenshi.index[-1]), str(df_five_hisdat.iloc[-1])))
        account_mgr = ac.AccountMgr(account, price, code)
        trade_num = ac.ShouShu(account_mgr.init_money()*self.trade_num_use_money_percent/price)
        trade_num = max(100, trade_num)

        # 信号计算
        four = stock.FOUR(closes)
        four = four[-1]
        upper, middle, lower = stock.TDX_BOLL(df_five_hisdat['c'])
        highs, lows, closes = df_five_hisdat['h'], df_five_hisdat['l'], df_five_hisdat['c']
        adx = stock.TDX_ADX(highs, lows, closes)
        self._log('boll : %.2f,%.2f,%.2f'%(upper[-1], middle[-1],lower[-1]))
        boll_w = abs(upper[-1]-lower[-1])/middle[-1]*100
        #50个周期内最高值
        is_high = abs(price-max(df_five_hisdat[-1000:]['h']))/price < 0.005

        boll_poss = [
            upper[-1],
         (upper[-1] - middle[-1])/2+middle[-1],
         middle[-1],
         (middle[-1] - lower[-1])/2+lower[-1],	     
         lower[-1],
        ]
        self._log('boll_poss: %.2f, %.2f boll_w=%.2f adx=%.2f'%(boll_poss[0], boll_poss[1], boll_w, adx[-1]))

        #上一个成交的价位
        pre_price = account_mgr.last_chengjiao_price()
        pre_pre_price = account_mgr.last_chengjiao_price(index=-2)
        sell_count = account_mgr.queryTradeCount(1)
        buy_count = account_mgr.queryTradeCount(0)
        #买入均价

        adx = adx[-1]
        boll_up_ratio = 0.02
        #信号判断
        num = 0
        if so.assemble(
            price > boll_poss[1],
                        price > pre_price*(1+self.trade_ratio),
                       #price > boll_poss[2],
                       #price > self.max_buy_price*(1+self.trade_ratio),
                       #boll_w > 3.5,
                       #adx > 60,
                       #sell_count < 2,
                       #pr.horizontal(df_five_hisdat),
                       0,
                       ):
            num = -trade_num
            self.trade_status = self.enum.boll_up_mid
            #if self.order(1, code, price, num):
                #self._log(agl.utf8_to_ascii('一档卖出%s, %.2f, %d'%(code, price, num)))
        if so.assemble(price > boll_poss[0],
                       price > pre_price*(1+self.trade_ratio),
                       #price > self.max_buy_price*(1+self.trade_ratio),
                       #boll_w > 3,
                       adx>60,
                       is_high,
                       #four > self.trade_four[1],
                       #sell_count < 2,
                       #self.trade_status == self.enum.nothing,
                       #0,
                       ):
            num = -trade_num*3
            self.trade_status = self.enum.boll_up
            #if self.order(1, code, price, num):
                #self._log(agl.utf8_to_ascii('二档卖出%s, %.2f, %d'%(code, price, num)))
        if so.assemble(
            price < boll_poss[-2]*(1+boll_up_ratio),
            price < pre_price*(1-self.trade_ratio),
                       #price < boll_poss[2],
                       #price < self.min_sell_price*(1-0.03),
                       #boll_w > 3.5,
                       #adx>60,
                       #buy_count < 2,
                       #pr.horizontal(df_five_hisdat),
                       0,
                       ):
            num = trade_num
            self.trade_status = self.enum.boll_down_mid
            #if boll_w > 6:
                #num *= self.trade_num_ratio
            #if self.order(0, code, price, num):
                #self._log(agl.utf8_to_ascii('一档买入%s, %.2f, %d'%(code, price, num)))
        if so.assemble(price < boll_poss[-1],
                       price < pre_price*(1-self.trade_ratio),
                       #price < self.min_sell_price*(1-0.03),
                       #boll_w > 3,
                       #buy_count < 2,
                       #self.trade_status == self.enum.nothing,
                       #adx>70,
                       #four < self.trade_four[0],
                       #0,
                       ):
            num = trade_num*3
            #num = account_mgr.last_chengjiao_num()
            self.trade_status = self.enum.boll_down
            #if self.order(0, code, price, num):
                #self._log(agl.utf8_to_ascii('二档买入%s, %.2f, %d'%(code, price, num)))

        #成本区间
        if so.assemble(price < pre_price*(1-0.05),
                       four < -0.1,
                       self.trade_status == self.enum.boll_up,
                       0,
                       ):
            num = trade_num * self.trade_num_ratio
            self.trade_status = self.enum.nothing
        if so.assemble(price > pre_price*(1+0.05),
                       four > 0.1,
                       self.trade_status == self.enum.boll_down,
                       0,
                       ):
            num = -trade_num*self.trade_num_ratio
            self.trade_status = self.enum.nothing

        #zz顶抛出后回补
        if so.assemble(price < pre_price*(1-0.02),
                       #sell_count >= 2,
                       self.trade_status == self.enum.zz_up,
                       0,
                       ):
            #上次zz卖出的数量
            num = account_mgr.last_chengjiao_num()
            self.trade_status = self.enum.zz_hui_bu
        if so.assemble(price > pre_price*(1+0.02),
                       #sell_count >= 2,
                       self.trade_status == self.enum.zz_down,
                       0,
                       ):
            #上次zz卖出的数量
            num = account_mgr.last_chengjiao_num()
            self.trade_status = self.enum.zz_hui_bu

        #计算分时zz
        zz_sign = 0
        closes = df_five_hisdat['c'][-200:].values
        zz = stock.ZigZag(closes)
        if len(zz)>2:	
            zz_result = stock.analyzeZZ(zz)
            zz_line_ratio = zz_result[1]/zz_result[0]	#线段比率
            #扑捉大涨回头的信号
            if abs(zz_result[0])>0.05 and abs(zz_line_ratio)>0.05 and abs(zz_line_ratio)<0.2 and abs(zz_result[0])>0.04:
                zz_sign = agl.where(zz_result[1]>0, 1,-1)

        if num != 0:
            bSell = agl.where(num>0, 0, 1)
            num = abs(num)
            #if bSell:
                #num = self._compensate(num, bSell, code)
            #基本上每天的振幅都在1个点以上
            if abs(stock.ZhangFu(price, yestoday_close))>0.01:
                self.order(bSell, code, price, num)

        zz_pre_price = myredis.createRedisVal('policy_basesign_zz_pre_price', price)
        if so.assemble(zz_sign != 0,
                       0,
                       ):
            #print self.price, getZZPrePrice(self.price),abs(self.price-getZZPrePrice(self.price))/self.price
            num = trade_num*12
            bSell = agl.where(zz_sign>0, 0, 1)
            num = self._compensate(num, bSell, code)
            bCanOrder = False
            if so.assemble(bSell ,
                           price > zz_pre_price.get()*(1+0.03),
                           #price > pre_price*(1+self.trade_ratio),
                           ):
                bCanOrder = True
                self.trade_status = self.enum.zz_up
            if so.assemble((not bSell) ,
                           price < zz_pre_price.get()*(1-0.03),
                           #price < pre_price*(1-self.trade_ratio)
                           ):
                bCanOrder = True
                self.trade_status = self.enum.zz_down
            if bCanOrder:		
                self._getAccount().Order(bSell, code, price, num)
                zz_pre_price.set(price)


        #信号发生时语音播报, 并通知界面回显
        if not self.is_backtesting and (price > boll_poss[1] or price < boll_poss[-2]):
            codename = stock.GetCodeName(code)
            s = '%s, %.2f'%(codename, price)
            self.data.show(codename)    #通知界面显示
            self.data.speak2(s)	    #语音播报

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

        #看是否已经下单
        df = self._getAccount().WeiTuoList()
        if len(df) > 0:
            df = df[df['证券代码']==code]
            df = df[df['买0卖1']==str(bSell)]
            df = df[df['状态说明'] == tc.TCAccountCache.enum.yibao]
            bHaveWeiTuo = False
            chajia = self.trade_ratio/2
            for p in df['委托价格']:
                p = float(p)
                if abs(price - p)/price < chajia:
                    bHaveWeiTuo = True
                    return False

        #更新买入卖出限定价格
        if bSell:
            self.min_sell_price = min(self.min_sell_price, price)
            #print 'self.min_sell_price=', self.min_sell_price
        else:
            self.max_buy_price = max(self.max_buy_price, price)
            #print 'self.max_buy_price=', self.max_buy_price
        return self._getAccount().Order(bSell, code, price, num)


def Run(codes, task_id=0):
    #agl.LOG('sdf中')
    #codes = ['300033']
    def setParams(s):
        if 0: s = Strategy_Boll
        s.setParams(
            pl=publish.Publish(),
        )
    backtest_policy.test_strategy(codes, Strategy_Boll_Pre, setParams,
                                  start_day='2018-2-7', end_day='2018-3-16',
                                  #start_day='2017-7-26', end_day='2017-12-13'
                                  mode=BackTestPolicy.enum.tick_mode
                                  )
def test_strategy():
    assert(False & '已不支持')
    codes = stock.DataSources.getCodes()
    cpu_num = 5
    agl.startDebug()
    if agl.IsDebug():
        codes = [codes[0]]
        codes = [jx.XYCZ]
        codes = [jx.THS]
        #codes = [jx.LTGF.b]
    exec(agl.Marco.IMPLEMENT_MULTI_PROCESS)

if __name__ == "__main__":
    test_strategy()