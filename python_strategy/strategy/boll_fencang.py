#-*- coding:utf-8 -*-

"""boll分仓"""

import numpy as np
import pandas as pd
import boll_pramid
import backtest_policy, stock, myenum, agl, account as ac, help, myredis, sign_observation as so
import os
agl.tic()

#ths = stock.createThs()
	
class BollFenCangKline(boll_pramid.Strategy_Boll_Pre):
    """基于日线的boll分仓, 基本指标使用日线Boll以及日线Four"""
    def setParams(self, *args, **kwargs):
	self.base_num =	10000		#第一次买卖的数量    
	self.base_num_ratio = 0.1	#总资金的10%作为初始建仓, 与上一个变量两者可选， 注释该行使用绝对数量
	self.base_ratio	= 0.05		#盈亏区间的比率
	self.rhombus_mid_ratio = 0.3	#仓位形态菱形的下部占比
	self.four = [-0.5, 0.5]		#第一次买卖的技术指标阀值
	for k, v in kwargs.iteritems():
	    setattr(self, k, v)
    def OnFirstRun(self):
	self.key_sell_avg_price = 'BollFenCangKline.SellAvgPrice'+ str(os.getpid())
	self.key_sell_num = 'BollFenCangKline.SellNum'+ str(os.getpid())
	myredis.delKeys('BollFenCangKline')
    def Run(self):
	account = self._getAccount()
	code = self.data.get_code()
	hisdat = self.data.get_hisdat(code)
	closes = hisdat['c'].dropna()
	four = stock.FOUR(closes)
	four = four[-1]
	boll_up, boll_mid, boll_low ,boll_w= stock.TDX_BOLL2(closes)
	adx = stock.TDX_ADX(hisdat['h'], hisdat['l'], closes)
	price = hisdat.iloc[-1]['c']
	#print self.getCurTime(), four, price, boll_low[-1], boll_w[-1]
	#if four>0.1:
	    #self._getAccount().Order(1, code, price, 1000)
	
	#基于成本的交易, 不使用技术指标
	#基于价值回归及成本控制
	#缺点， 资金利用率低， 选股必须选好， 否则碰到一直下跌的情况就会造成亏损
	#优点, 成本在相对安全区域
	#当成本亏base_ratio%时加倍买入
	df_stock_list = account.StockList()
	df_stock_list = df_stock_list[df_stock_list['证券代码'] == code]
	#第一次买
	if so.assemble(four<self.four[0] ,len(df_stock_list) == 0 ,
	               #price<boll_low[-1] ,
	               #boll_w[-1]>2
	               ):  
	    if hasattr(self, 'base_num_ratio'):
		total_money = ac.AccountMgr(self._getAccount(), price, code).init_money()
		self.base_num = ac.ShouShu(total_money*self.base_num_ratio/price)
	    self._getAccount().Order(0, code, price, self.base_num)
	if len(df_stock_list) > 0:
	    chengben = float(df_stock_list['参考盈亏成本价'].loc[0])
	    changwei = int(df_stock_list['库存数量'].loc[0])
	    yinkui = calcYinKui(price, chengben)
	    #agl.Print( '盈亏:', chengben, yinkui, changwei, '频繁')
	    if price < chengben*(1-self.base_ratio):
		#如果仓位大于总资金的70%， 那么仓位为剩余资金的一半
		df_zhijing = account.ZhiJing()
		canuse_money = float(df_zhijing['可用'][-1])
		total_money = canuse_money + changwei*price
		if canuse_money/total_money<self.rhombus_mid_ratio:
		    num = ac.ShouShu(canuse_money/2/price)
		    #这里开始就按上次交易的价格来作为判断, 最后一个买入
		    df_chengjiao = account.ChengJiao()
		    df_chengjiao = df_chengjiao[df_chengjiao['买0卖1'] == '0']
		    last_buy_price = float(df_chengjiao['成交价格'][-1])
		    if price > last_buy_price*(1-self.base_ratio):
			num = 0
		else:
		    num = changwei*3
		if num>0:
		    account.Order(0, code, price, num)
	    #当赚base_ratio%时加倍卖出	
	    chengben = float(df_stock_list['买入均价'].loc[0])
	    sell_avg_price = myredis.createRedisVal(self.key_sell_avg_price, chengben)
	    sell_num = myredis.createRedisVal(self.key_sell_num, 0)
	    if price>chengben*(1+self.base_ratio) and four>self.four[1]:	#第一次卖
		if sell_num.get() == 0:
		    account.Order(1, code, price, self.base_num)
		    sell_avg_price.set(price)
		    sell_num.set(self.base_num)				
	    #print '--',chengben, sell_avg_price.get()*(1+self.base_ratio)
	    if price > sell_avg_price.get()*(1+self.base_ratio):
		num = int(df_stock_list['可卖数量'].loc[0])
		num = min(sell_num.get()*2, num)
		num = ac.ShouShu(num)
		if num > 0:
		    account.Order(1, code, price, num)
		    #更新卖出均价
		    new_sell_avg_price = (sell_avg_price.get() * sell_num.get()+price*num)/(sell_num.get()+num)
		    sell_avg_price.set(new_sell_avg_price)
		    sell_num.set(sell_num.get()+num)

#测试策略， 为了并行计算， 需要使用这种格式的函数定义		    
def Run(codes='', task_id=0):
    from pypublish import publish
    #设置策略参数
    def setParams(s):
	if 0: s = Strategy_Boll
	s.setParams(trade_num = 300, 
                    pl=publish.Publish()
                    )
    if codes == '':
	codes = ['300033']
    #现在的5分钟线在2017-5-15之后才有
    backtest_policy.test_strategy(codes, BollFenCangKline, setParams, day_num=20, mode=myenum.hisdat_mode, 
                                  start_day='2016-10-20', end_day='2017-10-1'
                                  )    

  
def calcYinKui(price, chengben):
    return (price - chengben)/chengben
if __name__ == "__main__":
    is_multi = 0
    is_multi = 1
    if not is_multi:
	Run()
    else:
	backtest_policy.MultiProcessRun(5, stock.DataSources.getCodes(), Run, __file__)
    agl.toc()