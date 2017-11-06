#-*- coding:utf-8 -*-

"""boll分仓"""

import boll_pramid
import backtest_policy, stock, myenum, agl, account as ac, help, myredis
agl.tic()

class BollFenCangKline(boll_pramid.Strategy_Boll_Pre):
    """基于日线的boll分仓, 基本指标使用日线Boll以及日线Four"""
    def getParams(self):
        return 1
    def setParams(self, *args, **kwargs):
	print agl.getFunctionName()
	myredis.delkey('BollFenCangKline.SellAvgPrice')
	myredis.delkey('BollFenCangKline.SellNum')
    def OnFirstRun(self):
	pass
    def Run(self):
	account = self._getAccount()
	code = self.data.get_code()
	hisdat = self.data.get_hisdat(code)
	closes = hisdat['c']
	#four = stock.FOUR(closes)
	#four = four[-1]
	#up, mid, low ,boll_w= stock.TDX_BOLL2(closes)
	#adx = stock.TDX_ADX(hisdat['h'], hisdat['l'], closes)
	#print self.getCurTime(), four
	price = hisdat.iloc[-1]['c']
	#if four>0.1:
	    #self._getAccount().Order(1, code, price, 1000)
	
	#基于成本的交易, 不使用技术指标
	#基于价值回归及成本控制
	#缺点， 资金利用率低， 选股必须选好， 否则碰到一直下跌的情况就会造成亏损
	#优点, 成本在相对安全区域
	base_num = 1000
	base_ratio = 0.1
	if agl.datetime_to_date(self.getCurTime()) == '2017-5-12':  #第一次买
	    self._getAccount().Order(0, code, price, base_num)
	#当成本亏base_ratio%时加倍买入
	df_stock_list = account.StockList()
	df_stock_list = df_stock_list[df_stock_list['证券代码'] == code]
	if len(df_stock_list) > 0:
	    chengben = float(df_stock_list['参考盈亏成本价'].loc[0])
	    changwei = int(df_stock_list['库存数量'].loc[0])
	    yinkui = calcYinKui(price, chengben)
	    print '盈亏:', chengben, yinkui, changwei
	    if price < chengben*(1-base_ratio):
		account.Order(0, code, price, changwei*3)
	    #当赚base_ratio%时加倍卖出	
	    chengben = float(df_stock_list['买入均价'].loc[0])
	    sell_avg_price = myredis.createRedisVal('BollFenCangKline.SellAvgPrice', chengben)
	    sell_num = myredis.createRedisVal('BollFenCangKline.SellNum', 0)
	    if price>chengben*(1+base_ratio):	#第一次卖
		if sell_num.get() == 0:
		    account.Order(1, code, price, base_num)
		    sell_avg_price.set(price)
		    sell_num.set(base_num)				
	    print '--',chengben, sell_avg_price.get()*(1+base_ratio/2)
	    if price > sell_avg_price.get()*(1+base_ratio):
		num = int(df_stock_list['可卖数量'].loc[0])
		num = min(sell_num.get()*2, num)
		num = ac.ShouShu(num)
		if num > 0:
		    account.Order(1, code, price, num)
		    #更新卖出均价
		    new_sell_avg_price = (sell_avg_price.get() * sell_num.get()+price*num)/(sell_num.get()+num)
		    sell_avg_price.set(new_sell_avg_price)
		    sell_num.set(sell_num.get()+num)
		    
    @staticmethod
    def test():
        
	def setParams(s):
	    if 0: s = Strategy_Boll
	    s.setParams(trade_num = 300)
	    
	codes = [u'300033']
	#现在的5分钟线在2017-5-15之后才有
	backtest_policy.test_strategy(codes, BollFenCangKline, setParams, day_num=20, mode=myenum.hisdat_mode, 
	                              start_day='2017-4-24', end_day='2017-9-1'
	                              )    
    
def getYinKui(myAccount, code):
    """获取股票资金帐户的盈亏
    return: float 盈亏百分比"""
    if 0: myAccount = account.LocalAcount
    df_stock_list = myAccount.StockList()
    df_stock_list = df_stock_list[df_stock_list['证券代码'] == code]
    if len(df_stock_list) > 0:
	yinkui = df_stock_list['参考盈亏成本价'].tolist()[0]
	return float(yinkui)
    return 0
def calcYinKui(price, chengben):
    return (price - chengben)/chengben
if __name__ == "__main__":
    BollFenCangKline.test()
    agl.toc()