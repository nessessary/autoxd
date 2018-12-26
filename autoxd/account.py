#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

import numpy as np
import pandas as pd
import time,warnings,unittest,datetime,dateutil
from abc import ABCMeta, abstractmethod

"""本地模拟A股卷商资金账户 v1.0 2016-5-15
v1.1	2017-10-30
v1.2    2017-11-5   添加股票列表的盈亏比率计算
v2.0    2018-10-9   优化速度
"""

class AccountDelegate(object):
    """交易接口, v1.0 包括七个接口"""
    __metaclass__ = ABCMeta
    def Order(self, bSell, code, price, num):
        raise NotImplementedError("Implement Interface")
    def StockList(self):
        raise NotImplementedError("Implement Interface")
    def ZhiJing(self):
        raise NotImplementedError("Implement Interface")
    def ChengJiao(self):
        raise NotImplementedError("Implement Interface")
    def WeiTuoList(self):
        raise NotImplementedError("Implement Interface")
    def CheDanList(self):
        raise NotImplementedError("Implement Interface")
    def CheDan(self, code, weituo_id):
        raise NotImplementedError("Implement Interface")
class BackTestingDelegate(object):
    """回测环境的回调接口"""
    __metaclass__ = ABCMeta
    def getCurTickTime(self):
        """return: str datetime"""
        raise NotImplementedError("Implement Interface")
class BackTesting(BackTestingDelegate):
    def getCurTickTime(self):
        """return: str datetime"""
        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))    
def ShouShu(num):
    """"""
    num = int(num /100.0 )*100
    return num
def sxf():
    """手续费, 万3的一般推算, 双向收取"""
    return 0.0016
#状态说明，包含 已成，已撤， 未成
class LocalAcount(AccountDelegate):
    """本地账户， 支持T+1, 无持续化"""
    stocklist_columns = '证券代码|证券名称|证券数量|库存数量|可卖数量|买入数量|参考成本价|买入均价|参考盈亏成本价|当前价|最新市值|参考浮动盈亏|盈亏比例(%)|在途买入|在途卖出|股东代码'
    zhijing_columns = '余额|可用|参考市值|资产|盈亏'
    chengjiao_columns = "成交日期|成交时间|证券代码|证券名称|买0卖1|买卖标志|委托价格|委托数量|委托编号|成交价格|成交数量|成交金额|成交编号|股东代码|状态数字标识|状态说明"
    def __init__(self, backtester, money=1000000, date='2000-1-1 9:30:00'):
        """
        date: 开户日期
        """
        self.backtester = backtester
        self.money = money	#可用资金
        #因为下单即认为成交, 因此只需要成交记录
        self.df_ChengJiao = pd.DataFrame( columns=self.chengjiao_columns.split('|'))
        self.df_stock = pd.DataFrame( columns=self.stocklist_columns.split('|'))
        for col in '证券数量|库存数量|可卖数量'.split('|'):
            self.df_stock[col] = self.df_stock[col].astype(int)
        self.df_zhijing = pd.DataFrame(np.array([money,money,0,money,0])).T
        self.df_zhijing.columns = self.zhijing_columns.split('|')
        self.df_zhijing.index = pd.DatetimeIndex([date])
    def _T1(self, date):
        """经过了一天， 重置stock表可卖数量
        date: str datetime"""
        #判断最后一个委托与当前时间是不是隔天
        if len(self.df_ChengJiao) == 0:
            return
        last_date = self.df_ChengJiao['成交日期'][-1]
        cur_date = date.split(' ')[0]
        if cur_date != last_date:
            #重置可卖数量
            for i in range(len(self.df_stock)):
                #self.df_stock.set_value(i,'证券数量', self.df_stock.iloc[i]['库存数量'])
                self.df_stock.at[i,'证券数量'] = self.df_stock.iloc[i]['库存数量']
                self.df_stock.at[i,'可卖数量'] = self.df_stock.iloc[i]['证券数量']
                if int(self.df_stock.iloc[i]['库存数量'])==0:
                    self.df_stock.at[i,'买入数量'] = 0
    def _insertChengJiaoRecorde(self, code, price, num, date, bSell):
        #成交记录
        row = {}
        for k in self.chengjiao_columns.split('|'):
            row[k] = ''
        row['成交日期'] = date.split(' ')[0]
        row['成交时间'] = date.split(' ')[1]
        row['证券代码'] = code
        row['买0卖1'] = str(bSell)
        row['买卖标志'] = bSell and '证券卖出' or '证券买入'
        #row['买卖标志'] = str(bSell)
        row['委托价格'] = row['成交价格'] = price
        row['委托数量'] = row['成交数量'] = num
        row['成交金额'] = float("%.2f"%(num*price))
        row['状态说明'] = '已成'
        self.df_ChengJiao.loc[len(self.df_ChengJiao)] = row
        self.df_ChengJiao.index = pd.DatetimeIndex(list(self.df_ChengJiao.index[:-1])+[date])
    def _updateStockChengBen(self, code, price, num, bSell,index):
        """更新买入成本"""
        #更新平均成本
        org_num = int(self.df_stock.iloc[index]['库存数量'])
        buy_num = int(self.df_stock.iloc[index]['买入均价'])
        buy_avg_price = float(self.df_stock.iloc[index]['买入均价'])
        num *= bSell and -1 or 1
        if int(bSell) == 0:
            new_price = (buy_num*buy_avg_price+price*num)/(buy_num+num)
            self.df_stock['买入均价'][self.df_stock['证券代码'] == code] = new_price
        #需要加上手续费作为成本
        if org_num+num > 0:
            new_price = (org_num*buy_avg_price+price*num + price*abs(num)*sxf())/(org_num+num)
            yinkui_ratio = float('%.2f'%((price - new_price)/new_price*100))
        else:
            new_price = 0
            yinkui_ratio = 0
        self.df_stock.at[index, '参考成本价'] = new_price
        self.df_stock.at[index, '参考盈亏成本价'] = new_price
        self.df_stock.at[index, '盈亏比例(%)'] = yinkui_ratio
        self.df_stock.at[index, '当前价'] = price
    def _insertZhiJing(self,code, price, num, bSell, date):
        """添加资金记录, 余额|可用|参考市值|资产|盈亏
        余额|盈亏 暂时没有使用
        """
        m = price*num
        if bSell:
            self.money += m*(1-sxf())
        else:
            self.money -= m*sxf()
            self.money -= m
        row = self.df_zhijing.iloc[-1].tolist()
        row[1] = self.money
        #市值
        #这里没有其它股票的价格， 因此只能知道当前股票的市值, 所以只能模拟一只股票的实时交易情况
        #如果要支持多个股票， 需要backtester提供价格查询接口
        row[2] = int(self.df_stock['库存数量'][self.df_stock['证券代码'] == code])*price
        row[3] = row[2]+row[1]    
        self.df_zhijing.loc[len(self.df_zhijing)] = row
        self.df_zhijing.index = pd.DatetimeIndex(list(self.df_zhijing.index[:-1])+[date])
    def _buy(self, code, price, num, date):
        self._T1(date)

        money = price * num
        if self.money < money:
            num = ShouShu(self.money / price)
        if num == 0:
            return 
        bSell = 0    
        self._insertChengJiaoRecorde(code, price, num, date, 0)
        #加入股票列表
        row = {}
        for k in self.stocklist_columns.split('|'):
            row[k] = ''
        row['证券代码'] = code
        for col in '证券数量|库存数量'.split('|'):
            row[col] = num
        row['可卖数量'] = 0
        row['买入数量'] = num
        for col in '买入均价|当前价|参考成本价|参考盈亏成本价'.split('|'):
            row[col] = price
        row['盈亏比例(%)'] = 0
        if (self.df_stock['证券代码'] == code).any():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")	
                index = self.df_stock[self.df_stock['证券代码'] == code].index[0]
                self._updateStockChengBen(code, price, num, bSell, index)
                #更新股票列表
                self.df_stock.at[index, '库存数量'] = self.df_stock.iloc[index]['库存数量'] + num
                self.df_stock.at[index, '买入数量'] = self.df_stock.iloc[index]['买入数量'] + num
        else:
            #第一次买入
            self.df_stock.loc[len(self.df_stock)] = row
        self._insertZhiJing(code, price, num, bSell, date)
    def _sell(self, code, price, num, date):
        self._T1(date)

        #查询能卖的数量
        if (self.df_stock['证券代码'] == code).any():
            bSell = 1
            can_sell_num = int(self.df_stock['可卖数量'][self.df_stock['证券代码'] == code])
            num = min(num, can_sell_num)
            if num <= 0:
                return
            self._insertChengJiaoRecorde(code, price, num, date, 1)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")	
                index = self.df_stock[self.df_stock['证券代码'] == code].index[0]
                self._updateStockChengBen(code, price, num, bSell,index)
                #更新数量
                self.df_stock.at[index, '可卖数量'] = self.df_stock.iloc[index]['可卖数量'] - num
                self.df_stock.at[index, '库存数量'] = self.df_stock.iloc[index]['库存数量'] - num
                self._insertZhiJing(code, price, num, bSell, date)
                #如果卖空了，删除记录
                if int(self.df_stock['库存数量'][self.df_stock['证券代码'] == code]) == 0:
                    self.df_stock = self.df_stock[self.df_stock['证券代码'] != code]

    def Order(self, bSell, code, price, num):
        """委托, 本地账户假定所有的委托都会成交
        return: str 成功则返回委托id号， 失败返回空"""
        assert(num % 100 == 0)
        assert(num > 0)
        sId=''
        if num == 0 :
            return sId
        date = self.backtester.getCurTickTime()
        if bSell:
            return self._sell(code, price, num, date)
        else:
            return self._buy(code, price, num,date)
    def StockList(self):
        """return : df 证券代码|证券名称|证券数量|库存数量|可卖数量|买入数量|参考成本价|买入均价|参考盈亏成本价|当前价|最新市值|参考浮动盈亏|盈亏比例(%)|在途买入|在途卖出|股东代码"""
        return self.df_stock
    def ZhiJing(self):
        """每次交易后对资金表加一条记录
        return: df 余额|可用|参考市值|资产|盈亏"""
        return self.df_zhijing
    def ChengJiao(self):
        """return: df 成交日期|成交时间|证券代码|证券名称|买0卖1|买卖标志|委托价格|委托数量|委托编号|成交价格|成交数量|成交金额|成交编号|股东代码|状态数字标识|状态说明"""
        return self.df_ChengJiao
    def WeiTuoList(self):
        """return: df"""
        return self.df_ChengJiao
    def CheDanList(self):
        assert(False)        
    def CheDan(self, code, weituo_id):
        assert(False)
        
    def Report(self, end_day, last_close, is_detail=False):
        from autoxd import stock,agl
        #成交记录
        df = self.df_ChengJiao.loc[:,['成交价格','成交数量','买卖标志','买0卖1','证券代码']]
        df.columns = ['price','num','flag','flag2','code']

        df['num'] = df['num'].astype(int)
        #只显示两位数
        df['price'] = df['price'].map(lambda x: agl.float_to_2(x))
        df['d'] = df.index.astype(str)
        df['d'] = df['d'].map(lambda x: str(dateutil.parser.parse(x) + \
                                            datetime.timedelta(minutes=5)))
        if is_detail:	
            agl.print_df(df)

        #计算股票市值, 暂时只能处理一只股票的情况
        shizhi = 0
        close = 0
        if len(self.df_stock)>0:
            code = self.df_stock.iloc[0]['证券代码']
            close = last_close
            num = self.df_stock.iloc[0]['库存数量']
            shizhi += float(close)*int(num)
        print(self.df_zhijing.tail(n=1))
        output_str = '市值:%f,总资产:%f'%(shizhi, self.money+shizhi)
        print(output_str)
        #如果持股不动，现在的资金
        #取第一次交易后的可用资金
        if len(self.df_zhijing)>1:
            money = self.df_zhijing.iloc[1]['可用']
        else:
            money = self.df_zhijing.iloc[0]['可用']
        #第一次股票数量到现在的市值
        num = 0
        if len(self.df_ChengJiao)>0:
            num = self.df_ChengJiao.iloc[0]['成交数量']
            code = self.df_ChengJiao.iloc[0]['证券代码']
            close = last_close
        shizhi = num*close
        print('如果持股不动 市值:%f,总资产:%f'%(shizhi, money+shizhi))

    #尝试使用tick ui
    def TickReport(self, df_five_hisdat, ShowStyle="all"):
        """ShowStyle: str 显示风格 all|win
        all=>显示全部	
        win=>显示一部分, 也就是切割数据，保留后面的一部分
        """
        import ui
        df = df_five_hisdat
        df_trade = self.ChengJiao()
        if ShowStyle == "win":
            if len(df) % 20 == 0:
                df = df[-50:]
                df_trade = df_trade[df.index[0]:]
                ui.AsynDrawKline.drawKline(df, df_trade)
        else:
            if len(df) % 50 == 0:
                ui.AsynDrawKline.drawKline(df, df_trade)

class AccountMgr(object):
    def __init__(self, account, price, code):
        if 0:self.account = LocalAcount
        self.account = account
        self.price = price
        self.code = code
    def getCanSellNum(self):
        """得到能卖的数量"""
        df = self.account.StockList()
        if len(df) == 0:
            return 0
        df = df[df['证券代码'] == self.code]
        if len(df) == 0:
            return 0
        return int(df.iloc[-1]['可卖数量'])
        
    def getCurCanWei(self):
        """得到当前仓位"""
        df = self.account.StockList()
        if len(df) == 0:
            return 0
        df = df[df['证券代码'] == self.code]
        if len(df) == 0:
            return 0
        return int(df.iloc[-1]['库存数量'])
    def last_chengjiao_price(self, index=-1,is_sell=-1):
        """上一个成交的价位
        is_sell : -1 不使用该flag
        """
        df_chengjiao = self.account.ChengJiao()
        if is_sell != -1:
            is_sell = str(is_sell)
            df_chengjiao = df_chengjiao[df_chengjiao['买0卖1'] == is_sell]
        if len(df_chengjiao) == 0:
            return 0
        if index == -2 and len(df_chengjiao)<2:
            return 0
        return float(df_chengjiao.iloc[index]['成交价格'])
    def last_chengjiao_num(self, index=-1, is_sell=1):
        df_chengjiao = self.account.ChengJiao()
        is_sell = str(is_sell)
        df_chengjiao = df_chengjiao[df_chengjiao['买0卖1'] == is_sell]
        if len(df_chengjiao) == 0:
            return 0
        if index == -2 and len(df_chengjiao)<2:
            return 0
        return int(df_chengjiao.iloc[index]['成交数量'])

    def get_BuyAvgPrice(self):
        """获取买入均价"""
        df = self.account.StockList()
        df = df[df['证券代码'] == self.code]
        if len(df) == 0:
            return np.nan
        return float(df.iloc[0]['买入均价'])
    def can_use_money(self):
        df_zhijing = self.account.ZhiJing()
        return float(df_zhijing.iloc[-1]['可用'])
    def total_money(self):
        from autoxd import agl
        df_zhijing = self.account.ZhiJing()
        df_stock = self.account.StockList()
        if len(df_stock) == 0:
            return self.can_use_money()
        num = agl.where(len(df_stock)>0, float(df_stock.iloc[-1]['库存数量']), 0)
        return float(df_zhijing.iloc[-1]['可用']) + num*self.price
    def init_money(self):
        df_zhijing = self.account.ZhiJing()
        if len(df_zhijing) == 0:
            return 100000.0
        return float(df_zhijing.iloc[0]['资产'])
    def yin_kui(self):
        """盈亏成本"""
        df_stock_list = self.account.StockList()
        df_stock_list = df_stock_list[df_stock_list['证券代码'] == self.code]
        if len(df_stock_list) > 0:
            yinkui = df_stock_list['参考盈亏成本价'].tolist()[0]
            return float(yinkui)
        return 0.0
    def getInitCanWei(self):
        """得到初始仓位"""
        df = self.account.ChengJiao()
        if len(df)==0:
            return 0
        return int(df.iloc[0]['成交数量'])
    def queryTradeCount(self, bSell):
        """查询同一交易方向的连续发生次数
        return: int"""
        df = self.account.ChengJiao()
        count = 0
        for i in range(len(df)-1, -1, -1):
            if int(df.iloc[i]['买0卖1']) == int(bSell):
                count += 1
            else:
                break
        return count

class mytest(unittest.TestCase):
    def _test_simple(self):
        """T+1测试"""
        import agl
        print(agl.getFunctionName())
        account = LocalAcount(BackTesting())
        code = '300033'
        account._buy(code, 70.3, 3000, '2016-5-10 9:33:00')
        account._buy(code, 73.7, 3000, '2016-5-10 10:35:00')
        account._sell(code, 74, 4000, '2016-5-10 10:35:00')
        account._buy(code, 75, 9000, '2016-5-11 13:35:00')
        account._sell(code, 73.5, 4500, '2016-5-11 14:35:00')
        account._sell(code, 73.2, 4500, '2016-5-11 14:55:00')
        account._sell(code, 73.2, 4500, '2016-5-11 14:56:00')
        account._sell(code, 72.2, 4500, '2016-5-12 14:55:00')
        account._buy(code, 71.2, 500, '2016-5-12 14:57:00')
        account.Report('2016-5-12')
        print(account.ZhiJing())
    def _test_buy_avg_price(self):
        from pypublish import publish
        pl = publish.Publish()
        #import os, psutil
        #print psutil.Process(os.getpid()).cmdline()
        code = '300033'
        account = LocalAcount(BackTesting())
        account._buy(code, 50, 1000, '2017-9-9 9:30:00')
        account._buy(code, 51, 500, '2017-9-12 9:30:00')
        account._buy(code, 53.4, 2000, '2017-9-15 9:30:00')
        account._sell(code, 50, 1000, '2017-9-19 9:30:00')
        account._buy(code, 49, 2000, '2017-9-20 10:00:00')
        df = account.StockList()
        self.assertEqual((50*1000+51*500+53.4*2000+49*2000)/(1000+500+2000+2000),
                         float(df[df['证券代码'] == code]['买入均价'].loc[0]))
        account._sell(code, 55, 10000, '2017-9-22 10:00:00')
        account._buy(code, 50, 500, '2017-9-22 14:00:00')
        df = account.StockList()
        print(df)
        mgr = AccountMgr(account, None, code)
        print(mgr.queryTradeCount(0))
    def _test_multi(self):
        account = LocalAcount(BackTesting())
        code = '300033'
        account._buy(code, 70.3, 3000, '2016-5-10 9:33:00')
        account._buy('300059', 33.7, 3000, '2016-5-10 10:35:00')
        account._sell(code, 74, 4000, '2016-5-10 10:35:00')
        account._sell('300059', 33.7, 3000, '2016-5-10 13:35:00')
        account._buy(code, 75, 9000, '2016-5-11 13:35:00')
        account._sell('300059', 73.5, 4500, '2016-5-11 14:35:00')
        account._sell(code, 73.2, 4500, '2016-5-11 14:55:00')
        account._sell(code, 73.2, 4500, '2016-5-11 14:56:00')
        account._sell(code, 72.2, 4500, '2016-5-12 14:55:00')
        account._buy(code, 71.2, 500, '2016-5-12 14:57:00')
        account.Report('2016-5-12')
        return account
    def _test_call(self):
        """调用"""
        account = LocalAcount(BackTesting())
        code = '300033'
        account.Order(0, code,70.3, 3000)
        account.Order(1, code,3, 3000)
        account.Order(0, code,4, 1000)
        print(account.StockList())
        print(account.WeiTuoList())
    def test_chengben(self):
        ac = LocalAcount(BackTesting())
        code = '300033'
        day = '2018-3-1 14:20:00'
        ac._buy(code, 10, 1000, day)
        #ac._buy(code, 9.8, 2000, day)
        ac._buy(code, 9.5, 3000, day)
        print(ac.StockList())
        ac.Order(1,code, 9.5*1.02, 4000)
        print (ac.ZhiJing())

if __name__ == "__main__":
    unittest.main()
