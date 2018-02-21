#-*- coding:utf-8 -*-

"""boll分仓, 择时策略"""

import numpy as np
import pandas as pd, pylab as pl
import boll_pramid
import backtest_policy, stock, myenum, agl, account as ac, help, myredis, sign_observation as so, ui,jbm, stock_pinyin as jx
import os,warnings

agl.tic()

#ths = stock.createThs()
g_ths = stock.THS()	

class BollFenCangKline(boll_pramid.Strategy_Boll_Pre):
    """基于日线的boll分仓, 基本指标使用日线Boll以及日线Four"""
    def setParams(self, *args, **kwargs):
	self.base_num =	10000		#第一次买卖的数量    
	self.base_num_ratio = 0.1	#总资金的10%作为初始建仓, 与上一个变量两者可选， 注释该行使用绝对数量
	self.base_ratio	= 0.05		#盈亏区间的比率
	self.base_pramid_ratio = 3	#底部增仓比率
	self.base_rhombus_mid_ratio = 0.3	#仓位形态菱形的下部占比, 当资金不够时， 尽量保留一些资金
	self.base_four = [-0.5, 0.3]		#第一次买卖的技术指标阀值
	for k, v in kwargs.iteritems():
	    setattr(self, k, v)
    def OnFirstRun(self):
	self.key_sell_avg_price = 'BollFenCangKline.SellAvgPrice'+ str(os.getpid())
	self.key_sell_num = 'BollFenCangKline.SellNum'+ str(os.getpid())
	myredis.delKeys('BollFenCangKline')
	#只需要计算一次的数值
	df_jll = g_ths.df_jll
	code = self.data.get_code()
	with warnings.catch_warnings():
	    warnings.simplefilter("ignore")	
	    self.df_jll = df_jll[df_jll['code'] == code]
    def Run(self):
	account = self._getAccount()
	code = self.data.get_code()
	hisdat = self.data.get_hisdat(code)
	hisdat = hisdat.dropna()
	closes = hisdat['c'].dropna()
	if len(closes)<60:
	    return
	
	#基本面计算
	date = agl.datetime_to_date(self.getCurTime())
	history_quarter_syl = jbm.calc_history_syl(self.df_jll, hisdat, 'quarter')
	syl = history_quarter_syl.ix[:date].iloc[-1]
	self.jbm = history_quarter_syl
	
	#计算技术指标
	four = stock.FOUR(closes)
	boll_up, boll_mid, boll_low ,boll_w= stock.TDX_BOLL2(closes)
	adx = stock.TDX_ADX(hisdat['h'], hisdat['l'], closes)
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
	if so.assemble(four<self.base_four[0] ,len(df_stock_list) == 0 ,
	               adx[-1] > 60,
	               #price<boll_low[-1] ,
	               #boll_w[-1]>2,
	               #syl < 50,
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
		if canuse_money/total_money<self.base_rhombus_mid_ratio:
		    num = ac.ShouShu(canuse_money/2/price)
		    #这里开始就按上次交易的价格来作为判断, 最后一个买入
		    df_chengjiao = account.ChengJiao()
		    df_chengjiao = df_chengjiao[df_chengjiao['买0卖1'] == '0']
		    last_buy_price = float(df_chengjiao['成交价格'][-1])
		    if price > last_buy_price*(1-self.base_ratio):
			num = 0
		else:
		    num = changwei*self.base_pramid_ratio
		if num>0:
		    account.Order(0, code, price, num)
	    #当赚base_ratio%时加倍卖出	
	    chengben = float(df_stock_list['买入均价'].loc[0])
	    sell_avg_price = myredis.createRedisVal(self.key_sell_avg_price, chengben)
	    sell_num = myredis.createRedisVal(self.key_sell_num, 0)
	    if price>chengben*(1+self.base_ratio) and four>self.base_four[1]:	#第一次卖
		if sell_num.get() == 0:
		    account.Order(1, code, price, self.base_num)
		    sell_avg_price.set(price)
		    sell_num.set(self.base_num)				
	    #print '--',chengben, sell_avg_price.get()*(1+self.base_ratio)
	    if price > sell_avg_price.get()*(1+self.base_ratio):
		num = int(df_stock_list['可卖数量'].loc[0])
		num = min(sell_num.get() * self.base_pramid_ratio, num)
		num = ac.ShouShu(num)
		if num > 0:
		    account.Order(1, code, price, num)
		    #更新卖出均价
		    new_sell_avg_price = (sell_avg_price.get() * sell_num.get()+price*num)/(sell_num.get()+num)
		    sell_avg_price.set(new_sell_avg_price)
		    sell_num.set(sell_num.get()+num)

	#
    def Report(self):
	"""报告技术指标"""
	if not hasattr(self, 'tech'):
	    return
	closes, four, boll_up, boll_mid, boll_low ,boll_w, adx = self.tech
	assert(len(closes) == len(four))
	cur_pl = agl.where(self.pl, self.pl, pl)
	if hasattr(self, 'jbm'):
	    syl = self.jbm
	    df = pd.DataFrame(syl)    
	    df.columns = ['市盈率']
	    df.plot()
	    cur_pl.show()
	    cur_pl.close()
	df = pd.DataFrame(closes)
	df['boll_w'] = boll_w
	df = stock.GuiYiHua(df)
	df['four'] = four
	#df[df.columns[0]] = (df[df.columns[0]]-1)*2
	df.plot()
	cur_pl.show()
	cur_pl.close()
	#ui.DrawClosesAndVolumes(self.pl, closes, four)

#测试策略， 为了并行计算， 需要使用这种格式的函数定义		    
def Run(codes='', task_id=0):
    from pypublish import publish
    #设置策略参数
    def setParams(s):
	if 0: s = Strategy_Boll
	s.setParams(trade_num = 300, 
                    pl=publish.Publish(explicit=True),
	            base_four=[-0.6,0.1]
                    )
    if codes == '':
	codes = ['300033']
    #现在的5分钟线在2017-5-15之后才有
    backtest_policy.test_strategy(codes, BollFenCangKline, setParams, day_num=20, mode=myenum.hisdat_mode, 
                                  start_day='2016-10-20', end_day='2017-8-20'
                                  )    

def SelectCodes():
    df_year = stock.THS().df_year
    df_year = df_year.ix['2010':'2016']
    #历史平均市盈率小于25且净利润逐年上升
    codes = stock.get_codes()
    codes = jbm.find_avg_syl(codes, df_year, 25)
    df_year = df_year[df_year['code'].map(lambda x: x in codes)]
    codes = jbm.find_jll_increase(df_year)
    #codes = agl.array_shuffle(codes)
    #max_row = min(len(codes)-1, 5)
    return codes

def Select_code2():
    """选择某些固定板块"""
    bankuais = ['人工智能','人脸识别', '新能源汽车', '锂电池', '无人驾驶']
    codes = []
    for bankuai in bankuais:
	codes += stock.get_bankuai_codes(bankuai)
    codes = np.unique(np.array(codes))
    return list(codes)
    
def calcYinKui(price, chengben):
    return (price - chengben)/chengben

import unittest
class mytest(unittest.TestCase):
    def test_strategy(self):
	codes = stock.DataSources.getCodes()
	cpu_num = 5
	agl.startDebug()
	if agl.IsDebug():
	    codes = [codes[0]]
	    codes = [jx.XYCZ]
	    codes = [jx.LTGF.b]
	    codes = [jx.THS]
	#key = agl.getModuleName(__file__)+'.selectcodes'
	#myredis.delkey(key)
	#codes = myredis.createRedisVal(key, lambda : SelectCodes()).get()
	#codes = myredis.createRedisVal(key, lambda: select_code2()).get()
	#backtest_policy.MultiProcessRun(cpu_num, codes, Run, __file__)
	exec agl.Marco.IMPLEMENT_MULTI_PROCESS

if __name__ == "__main__":
    unittest.main()