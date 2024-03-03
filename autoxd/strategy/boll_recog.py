#coding:utf8

from autoxd.strategy.five_chengben import Strategy_Boll_Pre
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd import backtest_policy
from autoxd import backtest_runner
from autoxd.backtest_runner import BackTestPolicy
from autoxd.stock import DataSources
from autoxd import myredis, agl, help, stock, backtest_policy, ui,account as ac, sign_observation as so
import pandas as pd
import numpy as np
import talib
import pylab as pl
from autoxd.live import get_detect_result
import os, cv2
from autoxd.mach_recog import detect_label
from autoxd.agl import LOG

class StrategyRecog(Strategy_Boll_Pre):

    def Run(self):
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

        # save boll to img
        df = df_five_hisdat
        trade_sign = 0
        if len(df) > 100:
            pl.figure()
            save_path = 'html'
            i = index
            get_detect_result.drawBoll(pl, get_detect_result.filter_close(df['h'].values[-100:], df['l'].values[-100:], middle[-100:]),\
                        upper[-100:], middle[-100:], lower[-100:])
            fname = os.path.join(save_path, "a%d.png" % (i))
            img = get_detect_result.fig_to_numpy()
            #pl.savefig(fname)
            pl.close()
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            #cv2.imwrite('html/a3.png', img)
            #fname = os.path.abspath(fname)
            #img = cv2.imread(fname)
            #LOG((i, self.getCurTime()))
            trade_sign = detect_label.get_Label(img)
            if trade_sign == 'u1':
                trade_sign = -1
            if trade_sign == 'd1':
                trade_sign = 1
            if trade_sign is None:
                trade_sign = 0
            #else:
                #cv2.imshow('image', img)
                #cv2.waitKey(0)
            
            
        #信号判断, recog boll img
        num = 0
        trade_price_pre = account_mgr.last_chengjiao_price()
        if trade_sign > 0:
            num = 200
        if trade_sign < 0:
            num = -200

        if so.assemble(abs(num)>0,
                       abs(trade_price_pre - price) /price>0.02
                       ):
            order = num <0 and 1 or 0
            self.order(order, code, price, abs(num))

        #tick report
        if self.is_backtesting and self.is_tick_report:
            self._getAccount().TickReport(df_five_hisdat, 'win')
        return	
        
    

def Run(codes, task_id=0):
    from autoxd.pypublish import publish
    
    def fnSample(code, dtype='5'):
        from autoxd import warp_pytdx as tdx
        if dtype=='5':
            df = tdx.getFive(code)
            df = df.sort_index()
            return df
        if dtype=='d':
            df = tdx.getHisdat(code)
            df = df.sort_index()
            return df
    
    def setParams(s):
        s.setParams(
            pl=publish.Publish(),
        )
    backtest_policy.test_strategy(codes, StrategyRecog, setParams,
                                  start_day='', end_day='',
                                  mode=BackTestPolicy.enum.hisdat_mode|BackTestPolicy.enum.hisdat_five_mode,
                                  datasource_mode=DataSources.datafrom.custom,
                                  datasource_fn=fnSample
                                  )

def main_run():        
    cpu_num = 3
    codes = stock.get_codes(n=cpu_num)
    #codes = [jx.THS同花顺]
    exec(agl.Marco.IMPLEMENT_MULTI_PROCESS)

if __name__ == "__main__":
    main_run()
    