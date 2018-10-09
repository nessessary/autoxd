#-*- coding:utf-8 -*-

"""boll分仓, 择时策略"""
import sys
import numpy as np
import pandas as pd, pylab as pl
import boll_pramid
import backtest_policy, stock, myenum, agl, account as ac, help, myredis, sign_observation as so, ui
if sys.version > '3':
    import stock_pinyin3 as jx
else:
    import stock_pinyin as jx
import os,warnings
from stock import DataSources

agl.tic()

class BollFenCangKline(boll_pramid.Strategy_Boll_Pre):
    """基于日线的boll分仓, 基本指标使用日线Boll以及日线Four"""
    def setParams(self, *args, **kwargs):
        self.base_num =	100		#第一次买卖的数量    
        self.fenchang = [[-0.05,0.05, 0],
                         [-0.12, 0.07, 0],
                         [-0.2, 0.1, 0],
                         [-0.3, 0.1, 0],
                         [-0.4, 0.1, 0],
                         [-0.45, 0.2, 0],
                         [-0.5, 0.2, 0],
                         ]
                            #跌幅， 当前资金占比 
        self.base_four = [-0.4, 0.3]		#第一次买卖的技术指标阀值
        self.first_price = 0
        self.calc_tech = {}
        if sys.version > '3':
            for k, v in kwargs.items():
                setattr(self, k, v)
        else:
            for k, v in kwargs.iteritems():
                setattr(self, k, v)            
    def OnFirstRun(self):
        self.key_sell_avg_price = 'BollFenCangKline.SellAvgPrice'+ str(os.getpid())
        self.key_sell_num = 'BollFenCangKline.SellNum'+ str(os.getpid())
        myredis.delKeys('BollFenCangKline')
    def _Fire(self, yinkui):
        for i, (r1, r2, f) in enumerate(self.fenchang):
            if f==0 and yinkui < r1:
                self.fenchang[i][2] = 1
                return r2
        return 0
    def OnCalcTech(self, df_hisdat, df_five, df_fenshi):
        """df : kline
        后面两个参数可能为None
        """
        closes = df_hisdat['c']
        self.calc_tech['four'] = stock.FOUR(closes)
        self.calc_tech['boll'] = stock.TDX_BOLL2(closes)
        self.calc_tech['adx'] = stock.TDX_ADX(df_hisdat['h'], df_hisdat['l'], closes)
    def getCalcTech(self, name, l):
        v = self.calc_tech[name]
        if type(v) == tuple:
            v = list(v)
            for i, tuple_v in enumerate(v):
                v[i] = v[i][:l]
        else:
            v = v[:l]
        return v
    def Run(self):
        account = self._getAccount()
        code = self.data.get_code()
        hisdat = self.data.get_hisdat(code)
        #hisdat = hisdat.dropna()
        #closes = hisdat['c'].dropna()
        closes = hisdat['c']
        if len(closes)<60:
            return

        index = len(closes)
        #计算技术指标
        #four = stock.FOUR(closes)
        four = self.getCalcTech('four', index)
        #boll_up, boll_mid, boll_low ,boll_w= stock.TDX_BOLL2(closes)
        boll_up, boll_mid, boll_low ,boll_w = self.getCalcTech('boll', index)
        #assert(agl.array_equal(boll_up, boll_up2))
        #adx = stock.TDX_ADX(hisdat['h'], hisdat['l'], closes)
        adx = self.getCalcTech('adx', index)
        #assert(agl.array_equal(adx, adx2))
        #收集使用过的技术指标，为了报告使用
        self.tech = closes, four, boll_up, boll_mid, boll_low ,boll_w, adx

        four = four[-1]
        price = hisdat.iloc[-1]['c']
        #print self.getCurTime(), four, price, boll_low[-1], boll_w[-1]

        #基于价值回归及成本控制，加上技术指标择时
        #缺点， 资金利用率低， 选股必须选好， 否则碰到一直下跌的情况就会造成亏损
        #优点, 成本在相对安全区域
        #当成本亏base_ratio%时加倍买入
        df_stock_list = account.StockList()
        df_stock_list = df_stock_list[df_stock_list['证券代码'] == code]
        #第一次买
        if so.assemble(four<self.base_four[0] ,
                       len(df_stock_list) == 0 ,
                       #self.first_price == 0,
                       #adx[-1] > 60,
                       #price<boll_low[-1] ,
                       #boll_w[-1]>2,
                       #syl < 50,
                       ):  
            if hasattr(self, 'base_num_ratio'):
                total_money = ac.AccountMgr(self._getAccount(), price, code).init_money()
                self.base_num = ac.ShouShu(total_money*self.base_num_ratio/price)
            self._getAccount().Order(0, code, price, self.base_num)
            if self.first_price == 0:
                self.first_price = price
        if len(df_stock_list) > 0:
            chengben = float(df_stock_list['参考盈亏成本价'].loc[0])
            changwei = int(df_stock_list['库存数量'].loc[0])
            yinkui = calcYinKui(price, self.first_price)
            #agl.Print( '盈亏:', chengben, yinkui, changwei, '频繁')
            buchagn_ratio = self._Fire(yinkui)
            if buchagn_ratio != 0:#补仓
                df_zhijing = account.ZhiJing()
                canuse_money = float(df_zhijing['可用'][-1])
                total_money = canuse_money + changwei*price
                use_money = total_money*buchagn_ratio
                num = ac.ShouShu(use_money/price)
                if num>0:
                    account.Order(0, code, price, num)

            #当赚base_ratio%时加倍卖出	
            chengben = float(df_stock_list['买入均价'].loc[0])
            if four>self.base_four[1]:	#第一次卖
                account.Order(1, code, price, self.base_num)
            #print '--',chengben, sell_avg_price.get()*(1+self.base_ratio)
            if price > self.first_price * (1+abs(yinkui)):
                num = int(df_stock_list['可卖数量'].loc[0])
                num = num*0.1
                num = ac.ShouShu(num)
                if num > 0:
                    account.Order(1, code, price, num)

        #
    def Report(self):
        """报告技术指标"""
        if not hasattr(self, 'tech'):
            return
        closes, four, boll_up, boll_mid, boll_low ,boll_w, adx = self.tech
        assert(len(closes) == len(four))
        cur_pl = agl.where(self.pl, self.pl, pl)
        df = pd.DataFrame(closes)
        df['boll_w'] = boll_w
        df = stock.GuiYiHua(df)
        df['four'] = four
        #df[df.columns[0]] = (df[df.columns[0]]-1)*2
        #index转日期
        df.index = pd.DatetimeIndex(df.index)
        df.plot()
        cur_pl.show()
        cur_pl.close()
        #ui.DrawClosesAndVolumes(self.pl, closes, four)

#测试策略， 为了并行计算， 需要使用这种格式的函数定义		    
def Run(codes='', task_id=0):
    from pypublish import publish
    def fnSample(code):
        import tushare as ts
        df = ts.get_hist_data(code)[['high','low','open','close','volume']]
        df.columns = list('hlocv')
        df = df.sort_index()
        return df

    #设置策略参数
    def setParams(s):
        if 0: s = Strategy_Boll
        s.setParams(trade_num = 300, 
                    pl=publish.Publish(explicit=True),
                    )
    #现在的5分钟线在2017-5-15之后才有
    backtest_policy.test_strategy(codes, BollFenCangKline, setParams, mode=myenum.hisdat_mode, 
                                  start_day='2017-4-10', end_day='2018-9-15',
                                  datasource_mode=DataSources.datafrom.custom,
                                  datasource_fn=fnSample
                                  )    


def calcYinKui(price, chengben):
    return (price - chengben)/chengben

def test_strategy():
    codes = stock.get_codes(flag=myenum.randn, n=4)
    cpu_num = 2
    #codes = ['300434']
    agl.startDebug()
    if agl.IsDebug():
        codes = [jx.ZCKJ.b]
    #backtest_policy.MultiProcessRun(cpu_num, codes, Run, __file__)
    exec(agl.Marco.IMPLEMENT_MULTI_PROCESS)

if __name__ == "__main__":
    test_strategy()
    #import cProfile
    #cProfile.run('test_strategy()', sort="cumulative")