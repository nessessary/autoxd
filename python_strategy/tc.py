#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os
import numpy as np
import pandas as pd
import sys,unittest
import live_policy,agl,stock,account,myredis,myenum
import win32con, win32gui
import ctypes
import ctypes.wintypes
#import tushare as ts
import math

def ComboArg(sArg=""):
    """用函数名和参数拼凑出字符串, 在模拟环境下，该函数不起作用"""
    #得到参数dict
    dict_arg = sys._getframe().f_back.f_locals
    #当前函数名称
    function_name = sys._getframe().f_back.f_code.co_name    
    sResult = function_name + '|'
    if sArg != "":
        sArg = sArg.replace(" ", "")
        args = sArg.split(",")
        for arg in args:
            sResult += str(dict_arg[arg])
            sResult += '|'
    print sResult
    
class TcAccount(account.AccountDelegate):
    """在虚拟环境里使用的新的tc接口"""
    stocklist_columns = '证券代码|证券名称|证券数量|库存数量|可卖数量|参考成本价|买入均价|参考盈亏成本价|当前价|最新市值|参考浮动盈亏|盈亏比例(%)|在途买入|在途卖出|股东代码'
    zhijing_columns = '余额|可用|可用2|参考市值|资产'
    chengjiao_columns = "成交日期|成交时间|证券代码|证券名称|买0卖1|买卖标志|委托价格|委托数量|委托编号|成交价格|成交数量|成交金额|成交编号|股东代码|状态数字标识|状态说明"
    weituo_columns = '操作日期|委托时间|股东代码|深0沪1|证券代码|证券名称|买0卖1|买卖标志|委托价格|委托数量|委托编号|成交数量|成交金额|撤单数量|状态说明|撤单标志|委托日期|备注|'
    chedanlist_columns = "操作日期|委托时间|股东代码|深0沪1|证券代码|证券名称|状态说明|"\
		"买卖标志|买0卖1|委托价格|委托数量|委托编号|成交数量|撤单数量|委托日期|"
    def __init__(self, live=None):
        if live == None:
            self.delegate = live_policy.Live()
        else:
            self.delegate = live
    def _str_to_df(self, s):
        """行分割{}, 列分割|
        return: df"""
	s = agl.ascii_to_utf8(s)
        a = s.split('{}')
        c = []
        for b in a:
            if b != '':
                c.append(b.split('|'))
        return pd.DataFrame(c)
    #一共七个交易接口
    def Order(self, bSell, code, price, num):
        """return: str 成功则返回委托id号， 失败返回空"""
	#self.delegate.log('-=-----------order')
        #s = ComboArg("bSell, code, price, num")
        s = "Order|"+str(bSell)+"|"+str(code)+"|"+str(price)+"|"+str(num)+"|"
        sReturn = self.delegate.handleRotuer(s)
        #'132493|A5001586|'
        sId = ''
        if agl.ascii_to_utf8(sReturn) != "超时":
            sId = sReturn.split('|')[0]
	    sSell = '卖出'
	    if not bSell:
		sSell = '买入'
	    sMsg = '委托下单 %s %s %s %s , 委托单号%s'%(sSell, str(code), agl.FloatToStr(float(price)), str(num), str(sId))
	    sMsg = agl.utf8_to_ascii(sMsg)
	    self.delegate.log(sMsg)
        return sId  
    def StockList(self):
        """return: df 证券代码|证券名称|证券数量|库存数量|可卖数量|参考成本价|买入均价|参考盈亏成本价|当前价|最新市值|参考浮动盈亏|盈亏比例(%)|在途买入|在途卖出|股东代码"""
        #s = ComboArg()
        s = "StockList|"
        sReturn = self.delegate.handleRotuer(s)
        if agl.ascii_to_utf8(sReturn) != "超时" and len(sReturn)>0:
	    #return sReturn
            df = self._str_to_df(sReturn)
	    df = df[df.columns[:15]]
            df.columns = self.stocklist_columns.split('|')
            return df
        return pd.DataFrame([])
    def ZhiJing(self):
        """return: df 余额|可用|参考市值|资产"""
        #s = ComboArg()
        s = "ZhiJing|"
        sReturn = self.delegate.handleRotuer(s)
        if agl.ascii_to_utf8(sReturn) != "超时":
            df = self._str_to_df(sReturn)
	    df = df[[1,2,4,5,6]]
            df.columns = self.zhijing_columns.split('|')
            return df
        return pd.DataFrame([])
    def ChengJiao(self):
        """return: df 成交日期|成交时间|证券代码|证券名称|1为卖出0为买入|买卖标志|委托价格|委托数量|委托编号|成交价格|成交数量|成交金额|成交编号|股东代码|状态数字标识|状态说明"""
        #s = ComboArg()
        s = "ChengJiao|"
        sReturn = self.delegate.handleRotuer(s)
        if agl.ascii_to_utf8(sReturn) != "超时" and len(sReturn)>0:
            df = self._str_to_df(sReturn)
	    df = df[df.columns[:16]]
            df.columns = self.chengjiao_columns.split('|')
            return df
        return pd.DataFrame([])
    def HistoryChengJiao(self):
        """return: df 成交日期|成交时间|证券代码|证券名称|1为卖出0为买入|买卖标志|委托价格|委托数量|委托编号|成交价格|成交数量|成交金额|成交编号|股东代码|状态数字标识|状态说明"""
        #s = ComboArg()
        s = "HistoryChengJiao|"
        sReturn = self.delegate.handleRotuer(s)
        if agl.ascii_to_utf8(sReturn) != "超时":
            df = self._str_to_df(sReturn)
	    df = df[df.columns[:16]]
            df.columns = self.chengjiao_columns.split('|')
            return df
        return pd.DataFrame([])    
    def HistoryWeiTuo(self):
	s = "HistoryWeiTuo|"
	sReturn = self.delegate.handleRotuer(s)
	if agl.ascii_to_utf8(sReturn) != "超时" and len(sReturn)>0:
	    df = self._str_to_df(sReturn)
	    df.columns = self.weituo_columns.split('|')
	    df['委托日期'] = df['撤单标志']
	    return df
	return pd.DataFrame([])    
    def WeiTuoList(self):
        """return: df """
        #s = ComboArg()
        s = "WeiTuo|"
        sReturn = self.delegate.handleRotuer(s)
        if agl.ascii_to_utf8(sReturn) != "超时" and len(sReturn)>0:
            df = self._str_to_df(sReturn)
	    df = df[df.columns[:19]]
            df.columns = self.weituo_columns.split('|')
            return df
        return pd.DataFrame([])        
    def CheDanList(self):
        """return: df """
        #s = ComboArg()
        s = "CheDanList|"
        sReturn = self.delegate.handleRotuer(s)
        if agl.ascii_to_utf8(sReturn) != "超时":
            df = self._str_to_df(sReturn)
            df.columns = self.chedanlist_columns.split('|')
            return df
        return pd.DataFrame([])    
    def CheDan(self, code, weituo_id):
        """return: str """
        #s = ComboArg(' code, weituo_id')
        s = "CheDan|"+str(code)+"|"+str(weituo_id)+"|"
        sReturn = self.delegate.handleRotuer(s)
        return sReturn

class TCAccountCache(TcAccount):
    """把查询的结果保存在redis中， 只有下单后再重新查询
    历史成交一天只需要查一次
    """
    class enum :
	yicheng = '已成'
	yiche = '已撤'
	yibao = '已报'
	feidan = '废单'
    def is_dirty(self):
	#return True
	key = 'dirty'
	key = self._genKey(key)
	o = myredis.get_obj(key)
	if agl.IsNone(o):
	    self.setDirty(True)
	    return True
	return o
    def setDirty(self, is_dirty):
	key = self._genKey('dirty')
	myredis.set_obj(key,is_dirty)
    def Order(self, bSell, code, price, num):
	TcAccount.Order(self, bSell, code, price, num)
	self.setDirty(True)
    def HistoryWeiTuo(self):
	key = 'HistoryChengJiao'
	key = self._genKey(key)
	if self.is_dirty():
	    df = TcAccount.HistoryWeiTuo(self)
	    myredis.set_obj(key, df)
	else:
	    return myredis.get_obj(key)
	return df
    def WeiTuoList(self):
	"""历史成交加当日委托
	主要用状态说明这个字段来判断, 通过枚举值来判断委托状态
	操作日期|委托时间|股东代码|深0沪1|证券代码|证券名称|买0卖1|买卖标志|委托价格|委托数量|委托编号|成交数量|成交金额|撤单数量|状态说明|撤单标志|委托日期|备注|
	return : df"""
	key = 'WeiTuoList'
	key = self._genKey(key)
	if self.is_dirty():
	    df = self.HistoryWeiTuo()
	    df2 = TcAccount.WeiTuoList(self)
	    df = pd.concat([df2, df])
	    #对报单时间排序
	    df.index = pd.DatetimeIndex(df['操作日期'] + ' '+df['委托时间'])
	    df = df.sort()
	    myredis.set_obj(key, df)
	    self.setDirty(False)
	    return df
	else:
	    return myredis.get_obj(key)
    def _genKey(self,key):
	return 'TCAccountCache_'+key
    def saveCloseInfo(self):
	"""保存收盘信息, 包括资金表和成交表"""
	df = self.ZhiJing()
	df.index = [agl.getCurTime()]
	df.index.name = 't'
	#myredis.set_obj('temp',df)
	db = mysql.Tc()
	df.columns = db.getZhiJinCols()
	db.save(df, tbl_name=mysql.Tc.enum.zhijin)
	df = self.ChengJiao()
	df = df[df[df.columns[-1]]==agl.utf8_to_ascii('普通成交')]
	df.index = df['成交日期'].map(lambda x: x[:4]+'-'+x[4:6]+'-'+x[-2:]) + ' ' + df['成交时间']
	df = df.loc[:,['证券代码','买0卖1','成交数量','成交价格','成交金额','成交编号']]	
	df.columns = db.getChenJiaoCols()
	df.index.name='t'
	db.save(df, tbl_name=mysql.Tc.enum.chenjiao)
	
#以下为了命令行使用的交易指令， 跨进程发送
class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ('dwData', ctypes.wintypes.LPARAM),
        ('cbData', ctypes.wintypes.DWORD),
        ('lpData', ctypes.c_char_p)
        #formally lpData is c_void_p, but we do it this way for convenience
    ]
SendMessage = ctypes.windll.user32.SendMessageW    
def Buy(code, price, num):
    """通知autoxd去买入"""
    bSell = 0
    #price = AdjustPrice(bSell, code, price)
    #print price
    SendOrder(bSell, code, price, num)    
def Sell(code, price, num):
    bSell = 1
    #price = AdjustPrice(bSell, code, price)
    #print price
    SendOrder(bSell, code, price, num)    
#def AdjustPrice(bSell, code, price):
    #"""为了市价成交， 调整为对应二档"""
    ##取五档买卖
    #try:
	#df = ts.get_realtime_quotes(code)	    #该接口不能频繁调用， 否则报urlopen超时
    #except:
	#return price
    ##价格在涨停板范围内，那么使用给定价格
    #if price>1 and abs(price - float(df['price'][0]))/price < 0.1:
	#return price
    #if bSell == 1:
	#b1_p, b1_v, b2_p, b2_v = float(df['b1_p'][0]), float(df['b1_v'][0]), float(df['b2_p'][0]),float(df['b2_v'][0])
	##直接卖在2档， 但2档跨度太大时， 使用一档减0.12%, 同时也不能卖的太便宜， 溢价不能超过0.2%
	##price = np.min([price*0.998,b1_p*0.9988, b2_p])
	#if b2_p < 0.1:#集合竞价
	    #b2_p = b1_p*(1-0.001)
	#price = np.min([b1_p, b2_p])
    #else:
	#b1_p, b1_v, b2_p, b2_v = float(df['a1_p'][0]), float(df['a1_v'][0]), float(df['a2_p'][0]),float(df['a2_v'][0])
	##price = np.max([price*1.002,b1_p*1.0012, b2_p])
	#if b2_p <0.1:
	    #b2_p = b1_p * 1.001
	#price = np.max([b1_p, b2_p])
    #return price
    
def FindMainWindow():
    win_caption = 'autoxd_frame'
    hwnd = 0
    for i in range(10):
	if hwnd == 0:
	    hwnd = win32gui.FindWindow(None, win_caption)
	    if win32gui.IsWindowVisible(hwnd) == True:
		break
	hwnd = win32gui.FindWindowEx(0, hwnd , None, win_caption)
	if win32gui.IsWindowVisible(hwnd) == True:
	    break
    return hwnd
def SendOrder(bSell, code, price, num):
    #用wm_copydata
    hwnd = FindMainWindow()
    cds = COPYDATASTRUCT()
    cds.dwData = 0
    s = "Order|"+str(bSell)+"|"+str(code)+"|"+str(price)+"|"+str(num)+"|"
    cds.cbData = ctypes.sizeof(ctypes.create_string_buffer(s))
    cds.lpData = ctypes.c_char_p(s)
    print s
    SendMessage(hwnd, win32con.WM_COPYDATA, 0, ctypes.byref(cds))
    myredis.set_obj('TCAccountCache_dirty', True)
def ShouShu(num):
    """"""
    num = int(num /100.0 )*100
    return num    
def sxf(code, num, price):
    """    沪A: 佣金（营业部柜台标准）+印花税（1‰）+过户费（1元/1000股）
    深A: 佣金（营业部柜台标准）+印花税（1‰）
    A股、封闭式基金：最低5元 
    过户费：最低1元"""
    bShangHai = stock.IsShangHai(code)
    yong_jing =	0.0003*2    #双向收取
    yin_hua_shui = 0.001
    sxf = (yong_jing + yin_hua_shui)*(num*price)
    if bShangHai:
	sxf += math.ceil(num / 1000.0)
    if sxf < 5:
	sxf = 5
    return sxf

def get_zhijing_from_redis(is_have_return=False):
    """获取资金列表"""
    key_df_stocklist = 'df_zhijing'
    if 0: df = pd.DataFrame()
    df = myredis.get_obj(key_df_stocklist)
    if is_have_return:
	return df
    if df is not None:
	from prettytable import PrettyTable
	cols = '余额|可用|参考市值|资产'
	cols = cols.split('|')
	table = PrettyTable(cols)
	for i,row in df.iterrows():
	    table.add_row(row[cols].tolist())
	print table    
def get_stocklist_from_redis(is_have_return=False):
    """临时函数， 因为策略basesign保存了列表， 因此可以直接取"""
    key_df_stocklist = 'df_stocklist'
    if 0: df = pd.DataFrame()
    df = myredis.get_obj(key_df_stocklist)
    if is_have_return:
	return df
    if df is not None:
	from prettytable import PrettyTable
	cols = '证券代码|证券名称|证券数量|库存数量|可卖数量|参考成本价|买入均价|参考盈亏成本价|当前价|最新市值|参考浮动盈亏|盈亏比例(%)'
	cols = cols.split('|')
	table = PrettyTable(cols)
	for i,row in df.iterrows():
	    table.add_row(row[cols].tolist())
	#table.sort_key("ferocity")
	#table.reversesort = True
	print table
    #return df
def get_weituo_from_redis(is_have_return=False):
    """输出为成交的委托列表"""
    key = 'df_weituo'
    if 0: df = pd.DataFrame()
    df = myredis.get_obj(key)
    if is_have_return:
	return df
    if df is not None:
	from prettytable import PrettyTable
	cols = '证券代码|证券名称|买卖标志|委托价格|委托数量|委托编号|成交数量|成交金额|撤单数量|状态说明'
	cols = cols.split('|')
	df = df[df['状态说明'] != '已成']
	df = df[df['买卖标志'] != '配售申购']
	table = PrettyTable(cols)
	for i,row in df.iterrows():
	    table.add_row(row[cols].tolist())
	#table.sort_key("ferocity")
	#table.reversesort = True
	print table    
def get_chengjiao_from_redis(is_have_return=False):
    """输出为成交的委托列表"""
    key = 'df_chengjiao'
    if 0: df = pd.DataFrame()
    df = myredis.get_obj(key)
    if is_have_return:
	return df
    if df is not None:
	from prettytable import PrettyTable
	cols = '成交时间|证券代码|证券名称|买卖标志|委托价格|委托数量|委托编号|成交价格|成交数量|成交金额|成交编号'
	cols = cols.split('|')

	table = PrettyTable(cols)
	for i,row in df.iterrows():
	    table.add_row(row[cols].tolist())
	#table.sort_key("ferocity")
	#table.reversesort = True
	print table    	
class mytest(unittest.TestCase):
    def _test_str_to_df(self):
        df = TcAccount()._str_to_df('0|500.13|500.13||9100.00|13004.13|||{}')
	print df
    def _test_cache(self):
	print TCAccountCache().ChengJiao()
    def _test_TradeCloseAnalyzer(self):
	analyzer = TradeCloseAnalyzer()
	analyzer.Report()
    def test_get_stocklist_from_redis(self):
	get_stocklist_from_redis()

def query_code_chengben(code, df_stocklist):
    """查询股票参考成本价"""
    col = '参考成本价'
    df = df_stocklist[df_stocklist['证券代码']==code]
    if len(df)>0:
	chengben = float(df[col].tolist()[0])
	return chengben
    return None
def main(args):
    #Buy("300126", 10.01, 100)
    #Sell("300033", 53, 100)
    #Sell(rqgf, 10.18,1000)
    #print hex(FindMainWindow())
    #print "end"
    unittest.main()

    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
