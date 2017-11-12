#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os
def AddPath():
    from sys import path
    mysourcepath = os.path.abspath('..')
    if not mysourcepath in path:
        path.append(mysourcepath)    
AddPath()

"""区间交易法, 交易时对即时zz进行判断， 同时配合区间
当区间触发时， 并不急于下单， 而是需要继续观察下跌或上涨情况， 同时要观察大盘及板块的情况
一般的，还是使用zz的处理
使用方式， 修改set_param函数里的定义数组，来决定买入卖出时机
"""
import numpy as np
import pandas as pd
import sys, traceback, time
import live_policy, agl, pd_help, stock,help
import backtest_policy
import backtest_runner
import myenum, ui

class Strategy:
    def __init__(self, data, is_backtesting=False, mode=0):
	"""data: 运行时接口
	is_backtesting:bool 是否是回测
	mode: 回测使用, 允许模式， tick或hisdat
	"""
	self.pl	= None	#for publish
        self.data = data
	self.is_backtesting = is_backtesting
	self.mode = mode
        if 0:self.data = live_policy.Live()
	#使用系统初始化的交易账户, 不使用该句将不能调用交易账号
	self._setAccount(live_policy.enum.account_tc,'tdx', '')
	self._recordClassMember()
    def _setAccount(self, account_type, user, pwd):
	#注意， 现在只能支持一个账户
	if self.data != None:
	    self.data.createAccount(account_type, user, pwd)
    if 0:get = live_policy.Live()	
    def get(self):
	return self.data
    def _log(self, s):
	if self.is_backtesting:
	    return
	#s = str(s)
	if self.data != None:
	    self.data.log(s)
    def getCurTime(self):
	"""得到当前时间 return: str"""
	if self.is_backtesting:
	    return self.data.tick
	return agl.getCurTime()
    def getParams(self):
	"""输出主要参数, 由框架打印出来"""
	self._recordClassMember()
	return self.class_member
    def setParams(self, *args, **kwargs):
	"""设置策略参数, 由派生类实现"""
	pass
    def _recordClassMember(self):
	"""记录类成员"""
	#纪录类成员
	class_member = {}
	if not hasattr(self, 'class_member'):
	    self.class_member = {}
	for i,j in vars(self).items():
	    if i not in self.class_member.keys():
		class_member[str(i)] = j
	self.class_member = class_member
	
    def Run(self):
        code = self.data.get_code()
	#agl.LOG(code)
        #print code
	param = set_params(code)
	if len(param) == 0:
	    return
	self.data.log(code)
	#agl.LOG(code)
	#s_trace = traceback.extract_stack()
	#s_trace = agl.TraceToStr(s_trace)
	#agl.LOG(s_trace)    	
	#self.data.log("start run qjjy strategy.")
        df_hisdat = pd_help.Df(self.data.get_hisdat(code))
        df_fenshi = pd_help.Df(self.data.get_fenshi(code))
	#显示指数
	try:
	    stock_index_codes = ['999999', '399005']
	    def calcDec(df, df2):
		return float(df.iloc[-1]['p']) - df2.iloc[-2]['c']
	    display = []
	    for stock_index_code in stock_index_codes:
		df = self.data.get_fenshi(stock_index_code)
		df2 = self.data.get_hisdat(stock_index_code)
		display.append(df.iloc[-1]['p']) 
		display.append(calcDec(df, df2) )
	    self._log('shanghai: %.2f(%.2f), %.2f(%.2f)'%tuple(display) )
	except Exception as e:
	    self._log(str(e))
	
	#agl.LOG(code+str(len(df_fenshi.df)))
        #print df_hisdat.getLastDate()
        #print df_fenshi.getLastTime()
	if len(df_fenshi.df) == 0:
	    self.data.log(code+u"停牌")
	    return
	price = df_fenshi.getLastPrice()
	#为了测试分时获取的数据
	#if code == "002724":
	    #pl = Publish()
	    #title = str(code) + " " + str(price)
	    #ui.DrawTs(pl, df_fenshi.getCloses(), title=title)
	#self.data.log("test")
	#self.data.log(str( price))
	#return
	self._ExecPolicy(param, price)
	self._log("qjjy strategy")
    def _ExecPolicy(self, param, price):
	account = Qjjy_accout(param, self.data, self.is_backtesting)
	try:
	    account.buy(price)
	    account.sell(price)
	except Exception as e:
	    self._log(str(e))
	    #s_trace = traceback.extract_stack()
	    #s_trace = agl.TraceToStr(s_trace)
	    #self._log(s_trace)    	


def set_params(code):
    """定义区间交易的总买卖点，区间幅度等"""
    #注意：区间价格由买入价决定, 买入价会保存， 下次以实际买入价来确定区间
    params = [
        #code, 买入， 卖出, 买入数量, 区间价格比率, 区间数量比率
        ['002440', 18.6, 20, 1000, 0.02, 0.2],#闰土股份
        #['002614', 14.96, 15.20, 1000, 0.03, 0.2],#蒙发利
        #['600694', 63.05, 70.00, 2000, 0.02, 0.1],#大商股份
        #['002695', 29.9, 33.00, 1000, 0.02, 0.2],#煌上煌
        #['002638', 12.53, 13.00, 1000, 0.02, 0.2],#勤上光电
        #['002353', 33.35, 40.00, 1000, 0.02, 0.2],#杰瑞股份
        #['600844', 7.3, 9.1, 10000, 0.015, 0.2],#丹华科技
        #['002724', 36.8, 56.5, 1000, 0.015, 0.1],#海洋王
        #['000895', 32, 34, 2000, 0.015, 0.2],#双汇发展
        #['600624', 14.8, 18, 10000, 0.02, 0.2],#复旦复华
        #['600779', 11.98, 18, 10000, 0.02, 0.2],#水井坊
        #['601107', 6.5, 7, 100, 1, 1],#四川成渝
        
    ]
    for param in params:
	if param[0] == code:
	    return param
    return []

#该处原使用嵌套声明， 但会引起主模块重复调用， 估计是因为闭包设计引起的问题， 需要注意
#该问题只在VC中调用才有
class PrePriceList:
    """匹配区间价格, 记录已买的价格， 防止在一个价格上重复买"""
    def __init__(self):
	self.prices = np.array([])
    def find(self, price):
	return self._findMatchPrice(price, self.prices)
    def Add(self, price):
	if not self.find(price):
	    self.prices = agl.array_insert(self.prices, len(self.prices), price)
	    return True
	return False
    def Del(self, price):
	for i in range(len(self.prices)):
	    if self._findMatchPrice(price, [self.prices[i]]):
		self.prices = np.delete(self.prices, i)
		return True
	    return False
    def _findMatchPrice(self, price, price_list):
	delta = int(price*0.1)*0.01+0.01
	for p in (price_list):
	    if price > p-delta and price < p+delta:
		return True
	return False
	
class Qjjy_accout:
    """param: 描述
	account: 真实的交易账户"""    
    @staticmethod
    def _findMatchPrice(price, price_list, is_buy):
	"""因为每次tick是有一个时间间隔的， 那么价格区间锁的太死，会约过那个区间， 因此对于同一个方向，
	比如下跌， 超过区间值就应该买入
	分布预期(..)|(...............)
	is_buy: 是在buy函数里调用，还是在卖函数里调用
	return: 返回触发的区间价格， 即price_list里的价格"""
	delta = int(price*0.1)*0.01+0.01
	for i in range(len(price_list)):
	    p = price_list[i]
	    if is_buy:
		p_next = 0
		if i < len(price_list)-1:
		    p_next = price_list[i+1]
		if price < p + delta and price > p_next:
		    return p
	    #if price > p-delta and price < p+delta:
	    else:
		p_pre = price_list[0]
		if i>0:
		    p_pre = price_list[i-1]
		if price > p-delta and price < p_pre:
		    return p
	return -1
    def __init__(self, param, account, is_backtesting=False):
	"""回测时需要删除serial文件"""
	self.prices_traded = PrePriceList()    #类实例
	self.code,self.first_buy_price, self.end_sell_price, self.first_buy_num, \
	    self.qj_price_bilv, self.qj_num_bilv = param
	#重新根据记录来初始化参数
	self.fpath = help.getPythonPath() + "/datas/qjjy/"
	if is_backtesting:
	    self.fpath += "back/"
	else:
	    self.fpath += "live/"
	self.fpath += self.code+".serial"
	self.unserial()
	self._genQjPrice()
	self.account = account
	if 0: self.account = Strategy(data).data
    def _Buy(self, code, num, price):
        if not self.account.IsWeituo(code, num, price):
            return self.account.buy(code, num, price)
        return False
    def _Sell(self, code, num, price):
        if not self.account.IsWeituo(code, num, price):
            return self.account.sell(code, num, price)
        return False
    def _genQjPrice(self):
	"""根据买入价生成区间价格"""
	self.qj_prices = self.genPriceList(self.first_buy_price,
                                           self.qj_price_bilv)
	self.qj = self.first_buy_price * self.qj_price_bilv
    @staticmethod
    def DelSerial(code):
	"""当回测时需要先删除serial"""
	fpath = help.getPythonPath()+"/datas/qjjy/back/"+code+".serial"
	if help.FileExist(fpath):
	    help.FileDelete(fpath)
    def unserial(self):
	#强制重新开始
	if not help.FileExist(self.fpath):
	    self.pre_price = 0
	    return
	a = np.loadtxt(self.fpath, delimiter=',')
	if len(a) > 0:
	    #if len(a[0])>0:
		#print 'unserial', a[0]
	    self.prices_traded.prices = a[:-2]
	    self.pre_price  = a[-2]
	    self.first_buy_price = a[-1]
	else:
	    self.pre_price  = 0
    def serial(self):
	"""把上一次交易的价格放到已交易价格的最后, 形成一个ndarray"""
	n = self.prices_traded.prices
	n = agl.array_insert(n, len(n), self.pre_price)
	n = agl.array_insert(n, len(n), self.first_buy_price)
	#agl.SerialMgr.serial(n, self.fpath)
	np.savetxt(self.fpath, n, delimiter=',', fmt='%.3f')
    def _sxf(self, v):
	return v*0.992
    def buy(self,price):
	s = u"%s, 当前价%.2f, 上一个交易价%.2f, 第一次买入价%.2f"%(self.code,price, self.pre_price, self.first_buy_price)
	self.account.log(s)
	#第一次买
	if self.pre_price == 0 and price <= self.first_buy_price:
	    if self._Buy(self.code, self.first_buy_num, price):
		self.first_buy_price = price
		self.pre_price = price
		self._genQjPrice()
		self.serial()
	    return
	if price-self.pre_price <= -self.qj:
	    is_buy = True
	    #fire_qj_price = Qjjy_accout._findMatchPrice(price, self.qj_prices, is_buy)
	    fire_qj_price = price
	    if fire_qj_price > 0 and self.prices_traded.Add(fire_qj_price):
		num = stock.Account().ShouShu(self.first_buy_num*self.qj_num_bilv)
		if self._Buy(self.code, num, price):
		    print "_buy"
		    self.pre_price = price
		    self.serial()
    def sell(self,price):
	#全部卖出
	if price > self.end_sell_price :
	    if self._Sell(self.code, -1, price):
		self.pre_price = 0
		if os.path.isfile(self.fpath):
		    os.remove(self.fpath)
	    return
	#self.log("sell 0 "+str(self.qj) + " "+str(price-self.pre_price))
	if price-self.pre_price >= self.qj :
	    is_buy = False
	    #一定要匹配到锚点价格
	    #fire_qj_price = Qjjy_accout._findMatchPrice(price, self.qj_prices, is_buy)
	    fire_qj_price = price
	    if fire_qj_price > 0 :
		self.log("sell 2")
		num = stock.Account().ShouShu(self.first_buy_num*self.qj_num_bilv)
		if self._Sell(self.code, num, price):
		    self.log( "_sell")
		    self.prices_traded.Del(price)
		    self.pre_price = price
		    self.serial()
    def log(self, s):
	s = str(s)
	self.account.log(s)
    def genPriceList(self, first_price, bilv):
	"""产生区间价格列表, 上下各20个"""
	l = [first_price]
	for i in range(40):
	    l.append(first_price+i*bilv*first_price)
	for i in range(40):
	    l.append(first_price-i*bilv*first_price)
	l = np.array(l)
	l.sort()
	return l
    @staticmethod
    def Test():
	code, price_qj_bilv, num_qj_bilv = '600779', 0.03, 0.2
	param = set_params(code)
	account = Qjjy_accout(param, None)
	print account

def BackTesting():
    p = backtest_runner.BackTestPolicy()
    codes = stock.get_codes()
    codes = [u'002440']
    p.SetStockCodes(codes)
    backtesting = backtest_policy.Backtest()
    backtesting.createAccount(account_type=None, username=None, pwd=None)
    p.Regist(Strategy(backtesting, is_backtesting=True))
    p.Run('2014-11-1','2014-12-10')
def main(args):
    #Strategy(live_policy.Live()).Run()
    BackTesting()
    #Qjjy_accout.Test()
    #print "end"
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)