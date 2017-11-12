#coding:utf8
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457


"""关于boll分仓策略的预埋单的实现, 注意这是默认策略， 安装或升级会覆盖该文件
"""
import qjjy
import pd_help
import myredis, agl, help, stock, backtest_policy, ui
#import tushare as ts
import tc
import datetime
import pandas as pd
import numpy as np
import talib

#每天根据日线情况自行调整参数
#代码, 底仓, 基数1， 基数2, boll位置1， boll位置2， pre预埋单时机基于boll位置(计算t分钟内达到技术标准adx>60, w>2, boll>0.1), 
#chajia差价:买卖之间强制的差价
mydatas = [
{'symbol':'300033', 'lowerhold':5000, 'trade1':200, 'trade2':600, 'boll1':-0.1, 'boll2':0.2, 'pre':-0.3, 'chajia':0.5/100},
]
mydatas = pd.DataFrame(mydatas)
def pre_trade_jisu(closes, t, adx, w, boll):
    """预埋单判断时间"""
    if adx > 60 and boll > 0.1 and w > 2 and t > 5:
	return True
    return False

class Strategy_Boll_Pre(qjjy.Strategy):
    """为了实现预埋单"""
    def AllowCode(self, code):
	#return False
	#self._log(code)
	return code == mydatas['symbol'][0]
	codes = ['300033']	    #自己想交易的股票
	return code in codes
    def OnFirstRun(self):
	"""回测调用函数， 在第一个bar时调用， 先建立底仓"""
	code = self.data.get_code()
	df_fenshi = self.data.get_fenshi(code)
	#这里取不到开盘价， 用昨收盘代替
	open_price = float(df_fenshi.iloc[-1]['p'])
	#print o
	self._getAccount()._buy(code, open_price, mydatas['lowerhold'][0], self.getCurTime())    
    def Run(self):
	"""每个股票调用一次该函数, 调用后会释放， 因此不能使用简单的全局变量， 而需要使用redis来持续化
	另外， 交易接口要慎用， 比如列表查询， 可保存至redis，
	不要每进入函数都查询一下， 下单则无这种情况， 因为都是条件触发， 所以直接调即可
	"""
        #self._log('Strategy_Boll_Pre')
	account = self._getAccount()	#获取交易账户
	def run_stocklist():
	    try:
		df = account.ZhiJing()
		self._log(df.iloc[0])
		df = account.StockList()	#查询股票列表
		self._log(df.iloc[0])
	    except:
		pass
	agl.PostTask(run_stocklist,	100)	#每100秒执行一次
	
	
	#以下为交易测试
        code = self.data.get_code()	#当前策略处理的股票
	self.code = code
	if not self.is_backtesting and not self.AllowCode(code):
	    return

	df_hisdat = self.data.get_hisdat(code)	#日k线
	df_five_hisdat = self.data.get_hisdat(code, dtype='5min')	#5分钟k线
	#df_five_hisdat = df_five_hisdat.sort_index()
	#self._log(df_five_hisdat.tail())
	self._log(code)
	df_fenshi = self.data.get_fenshi(code)	#日分时
	if len(df_fenshi) == 0:
	    self.data.log(code+u"未取到分时数据")
	    return
	price = float(df_fenshi.tail(1)['p'])    #当前股价
        closes = df_hisdat['c']
	yestoday_close = closes[-2]	    #昨日收盘价
	self._log('price=%.2f %s %s'%(price, str(df_fenshi.index[-1]), str(df_five_hisdat.iloc[-1])))
	#self._log(yestoday_close)

	def Order_At_Boll():
	    upper, middle, lower = stock.TDX_BOLL(df_five_hisdat['c'])
	    
	    highs, lows, closes = df_five_hisdat['h'], df_five_hisdat['l'], df_five_hisdat['c']
	
	    adx = stock.TDX_ADX(highs, lows, closes)
	
	    self._log('boll : %.2f,%.2f,%.2f'%(upper[-1], middle[-1],lower[-1]))
	    boll_w = abs(upper[-1]-lower[-1])/middle[-1]*100

	    boll_poss = [
	     upper[-1],
	     (upper[-1] - middle[-1])/2+middle[-1],
	     middle[-1],
	     (middle[-1] - lower[-1])/2+lower[-1],	     
	     lower[-1],
	    ]
	    self._log('boll_poss: %.2f, %.2f boll_w=%.2f adx=%.2f'%(boll_poss[0], boll_poss[1], boll_w, adx[-1]))
	    
	    user_datas = mydatas[mydatas['symbol']==code]
	    if price > boll_poss[1]*1.001:
		num = int(user_datas['trade1'])
		if self.order(1, code, price, num):
		    self._log(agl.utf8_to_ascii('一档卖出%s, %.2f, %d'%(code, price, num)))
	    if price > boll_poss[0]*0.998:
		num = int(user_datas['trade2'])
		if self.order(1, code, price, num):
		    self._log(agl.utf8_to_ascii('二档卖出%s, %.2f, %d'%(code, price, num)))
	    if price < boll_poss[-2]*0.999:
		num = int(user_datas['trade1'])
		if self.order(0, code, price, num):
		    self._log(agl.utf8_to_ascii('一档买入%s, %.2f, %d'%(code, price, num)))
	    if price < boll_poss[-1]*1.001:
		num = int(user_datas['trade2'])
		if self.order(0, code, price, num):
		    self._log(agl.utf8_to_ascii('二档买入%s, %.2f, %d'%(code, price, num)))
	    #信号发生时语音播报, 并通知界面回显
	    if not self.is_backtesting and (price > boll_poss[1] or price < boll_poss[-2]):
		codename = stock.GetCodeName(code)
		s = '%s, %.2f'%(codename, price)
		self.data.show(codename)    #通知界面显示
		self.data.speak2(s)	    #语音播报
	Order_At_Boll()
	
	#tick report
	if self.is_backtesting:
	    self._getAccount().TickReport(df_five_hisdat, 'win')
	return	

    #----------------------------------------------------------------------
    def _getAccount(self):
	if self.is_backtesting:
	    return self.data.account	#LocalAccount
	return tc.TcAccount(self.data)  

    def order(self, bSell, code, price, num):
	"""bSell: int 不能使用boolean
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
	    chajia = float(mydatas['chajia'])
	    for p in df['委托价格']:
		p = float(p)
		if abs(price - p)/price < chajia:
		    bHaveWeiTuo = True
		    return False
	    
	#开放为实盘下单
	if self.is_backtesting:
	    #得到上一个交易价格， 确定当前价格与之前的价格有一个差距
	    df_chengjiao = self._getAccount().ChengJiao()
	    pre_price = df_chengjiao['成交价格'][-1]
	    chajia = mydatas['chajia'][0]
	    if abs(price-pre_price)/price > chajia:
		return self._getAccount().Order(bSell, code, price, num)
	return True

	    
def main(args):
    #agl.LOG('sdf中')
    codes = ['300033']
    backtest_policy.test_strategy(codes, Strategy_Boll_Pre)

if __name__ == "__main__":
    try:
	args = sys.argv[1:]
	main(args)
    except:
	main(None)	
	    