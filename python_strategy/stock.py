#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

import os
try:
    import mysql
except:
    pass
import help,agl
import time
import datetime, dateutil
import ui
import copy, warnings, unittest,struct, itertools
import simulator
import myenum,myredis
import talib
from talib import MA_Type
import numpy as np
import pylab as pl
import pandas as pd
#from talib.abstract import *
from sklearn.cluster import KMeans
import pickle,re,pyprind
#from pymemcache.client import Client
#import grabThsWebStockInfo
#import tushare as ts

#from pypublish import publish
#pl = publish.Publish()

def get_codes(flag=myenum.all, n=100):
    """获取有效的股票列表, enum现在改为myenum
    flag : enum.all 等枚举 , enum.exclude_cyb 排除创业板, enum.rand10 随机选10个
    n : enum.rand时使用
    return: list """
    key = myredis.enum.KEY_CODES    #更新ths F10时删除
    val = myredis.createRedisVal(key, [])
    codes = val.get()
    if len(codes) == 0:
        #从ths中取
        ths = createThs()
        codes = ths.getDf(0)['code'].tolist()
        if len(codes)>0:
            #默认去除大盘的代码
            dapans = ['399001', '999999','399005','399002','399006','510050']
            codes = [unicode(code) for code in codes if code not in dapans]
            #codes = filter(lambda x: x[:2] != '88', codes)
            val.set(codes)
    if flag == myenum.randn:
        from sklearn.utils import shuffle
        codes = shuffle(codes)
        return list(codes[:n])
    return codes

def get_bankuais():
    """获取同花顺的全部板块名称列表 return: list"""
    key = myredis.enum.KEY_BANKUAIS
    val = myredis.createRedisVal(key, lambda : list(createThs().getBankuais()))
    return val.get()
    
def getKlineLastDay():
    """得到日线库中的最后一天, return: str day"""
    sql = 'select max(kline.kline_time) from kline'
    t = mysql.createStockDb().ExecSql(sql)
    return str(t[0][0])
def getHisdatDataFrameFromRedis(code, start_day='', end_day=''):
    """得到日线df从redis, 如果是板块那么返回的是pd.Series 
    return: df ohlc"""
    df = myredis.get_obj(code)
    if agl.IsNone(df):
        #to call DumpToRedis
        msg = '%s, getHisdatDataFrameFromRedis no relust, %s, %s'%(code, start_day, end_day)
        #agl.LOG(msg)
        return pd.DataFrame([])
    if start_day != '' and end_day != '':
        df = df.ix[start_day:end_day]
    elif start_day != '':
        df = df.ix[start_day:]
    elif end_day != '':
        df = df.ix[:end_day]
    return df
def memcache_load():
    #client = Client(('localhost', 11211))
    #client.set('some_key', 'some_value')
    #result = client.get('some_key')
    #print result
    agl.tic()
    codes = get_codes(myenum.all)
    for code in codes:
        Guider(code).ToDataFrame()
    agl.toc()

class FenshiCodeCache:
    """用redis作为分时的cache"""
    keyhead = 'fenshicode_'
    def __init__(self, bankuai_name):
        self.bankuai_name = bankuai_name
    def _get_name(self):
        return self.keyhead+self.bankuai_name
    def getBankuaiFenshiZhishu(self):
        return myredis.get_obj(self._get_name())
    def set(self, zhishu):
        myredis.set_obj(self._get_name(), zhishu)
    def delKey(self):
        myredis.delkey(self._get_name())
    @staticmethod
    def clearAll():
        for key in myredis.getKeys():
            if key.find(FenshiBankuaiCache.keyhead)==0:
                myredis.delkey(key)	
def getFenshiDfUseRedis(code, start_day, end_day, rule='1min'):
    """数据更新跑fenshi_redis.py"""
    df_fenshi = FenshiCodeCache(code).getBankuaiFenshiZhishu()
    if df_fenshi is None:
        df_fenshi = CreateFenshiPd(code, start_day, end_day)
        if len(df_fenshi)>0:
            if rule == '1min':
                df_fenshi = df_fenshi.resample(rule).mean()
    return df_fenshi    


class LiveData:
    """获取在线数据"""
    def getHisdat(self, code):
        """return: df"""
        df = getHisdatDataFrameFromRedis(code)
        return df
    def getFenshi(self, code):
        """return: df"""
        key = 'live_f_'+code
        fenshi = myredis.get_Bin(key)
        if agl.IsNone(fenshi) or len(fenshi) == 0:
            return pd.DataFrame([])
        a = []
        n = 2+4+2+2+1
        for i in range(len(fenshi)/n):
            a.append(struct.unpack("=hfhhb", fenshi[n*i:n*(i+1)]))
        df = pd.DataFrame(a)
        df.columns = list('tpvdb')
        return df
    def getFiveMinHisdat(self, code):
        """return: df col=['hloc']"""
        key = 'live_h_five_'+code
        hisdat = myredis.get_Bin(key)
        if agl.IsNone(hisdat) or len(hisdat) == 0:
            return pd.DataFrame([])
        a = []
        n = (7+4*7)
        for i in xrange(len(hisdat)/n):
            e = list(struct.unpack("=hbbbbbfffffff", hisdat[n*i:n*(i+1)]))
            #e[0] = stock.StockTime.s_ToStrDate(e[0])
            if e[1] == 0:   #tdx时间转换为真实时间
                t = agl.curTime()
                tdx_t = e[0]
                e[0] = t.year
                e[1] = t.month
                e[2] = t.day
                e[3], e[4] = StockTime.ToTime(tdx_t)
                e[5] = 0
            t = datetime.datetime(e[0],e[1],e[2],e[3],e[4],e[5])
            a.append([t]+e[6:10])
        #510050只有当天数据， 从数据库中补充
        if code == '510050':
            end_day = agl.CurDay()
            #国庆等长假因素，需要多后退几天
            start_day = help.MyDate.s_Dec(end_day, -20) 
            df_five = mysql.getFiveHisdat(code, start_day)
        #a = np.array(a)
        df = pd.DataFrame(a)
        df = df.set_index(df.columns[0])
        df.index = pd.DatetimeIndex(df.index)
        df.columns = list('hloc')
        if code == '510050':
            df = pd.concat([ df_five,df])
        #数据如果太短， 从数据库中补充
        if len(df)<30:
            min_day = min(df.index)
            end_day = help.MyDate.s_Dec(min_day, -1)
            start_day = help.MyDate.s_Dec(end_day, -20)
            df_five = mysql.getFiveHisdat(code, start_day, end_day)
            df = pd.concat([df_five, df])
        return df
    def getCodes(self):
        key = 'live_codes'
        codes = myredis.get_Bin(key)
        l = len(codes)
        a = []
        n = 6
        for i in xrange(l/6):
            a.append(codes[n*i:n*(i+1)])
        return np.array(a)
    def getFrameHwnd(self):
        key = 'autoxd_frame_hwnd'
        hwnd_frame = myredis.get_Bin(key)
        hwnd_frame = struct.unpack('=i', hwnd_frame)
        return hwnd_frame[0]

#看股票基本面
########################################################################
class StockInfo:
    """"""
    code = ''
    name = ''
    ltgb = 0	#流通股本
    hy = ''	#行业
    zgb = 0	#总股本
    zzc = 0	#总资产
    mgsy = 0	#每股收益

    #----------------------------------------------------------------------
    def __init__(self, code):
        """Constructor"""
        db = mysql.createStockDb()
        vals = db.getGupiaoInfo(code)
        if len(vals)>0:
            index, self.code, self.name, self.ltgb, self.hy, self.zgb, self.zzc, self.mgsy = vals[0]
    @staticmethod
    def UpdateTable():
        """更新股票基本数据, 暂定一个季度跑一次
        1. 先手工跑一下通达信的插件选股， 把数据导出到log.txt
        2. 先清空数据gupiao表, 把log.txt的内容写入到数据库"""
        fpath = "C:\\jcb_zxjt\\plugin\\log.txt"
        d = np.loadtxt(fpath, dtype=str, delimiter=',')
        #db = mysql.StockMysql()
        db = mysql.createStockDb()
        db.ExecSql('TRUNCATE TABLE gupiao;')
        db.ExecSql('set names gb2312')
        for i in range(len(d)):
            sql = 'insert into gupiao (stock_code, stock_name,ActiveCapital,J_hy,J_zgb,J_zzc,J_mgsy) values ("%s","%s","%s","%s","%s","%s","%s")' % \
                tuple(d[i])
            db.ExecSql(sql)
        db.ExecSql('commit')
    #----------------------------------------------------------------------
    def myprint(self):
        """"""
        help.myprint(self.code, self.name, self.ltgb, self.hy, self.zgb, self.zzc, self.mgsy)
def calc_bankuai_zhishu(codes, date, end_day, ltgbs):
    """计算板块指数
    codes: list 代码
    date: 基准日
    end_day: 
    ltgbs: list 流通股本
    return: pd.Series 指数 name=zhishu """
    #cur_day = agl.CurDay()
    df = pd.DataFrame(index = pd.period_range(date, end_day).to_timestamp())
    df_hisdat_cur_code = None
    for i, code in enumerate(codes):
        #print 'calc_bankuai_zhishu ', code
        df_hisdat = myredis.get_obj(code)
        if df_hisdat is None:
            continue
        df_hisdat = df_hisdat.ix[date:end_day]
        if len(df_hisdat) == 0:
            continue
        ltgb = ltgbs[i]
        df_hisdat['shizhi'] = ltgb * df_hisdat['c']
        first_shizhi = df_hisdat.dropna().iloc[0]['shizhi']	
        if(first_shizhi < 0.1):
            print(code,'流通股本为0，因为下载是编码异常， 因此这里要做异常处理')
            continue
        assert(first_shizhi>0)
        df_hisdat['zhishu'] = df_hisdat['shizhi'] / first_shizhi
        df_hisdat = df_hisdat.fillna(0)
        if len(df.columns) == 0:
            df['shizhi'] = df_hisdat['shizhi']
            #基准市值
            df['jizhun'] = first_shizhi
        else:
            assert(first_shizhi > 0)
            df['shizhi'] = df['shizhi'].fillna(0)
            #不对停牌的股票进行统计
            df_zero = copy.deepcopy(df['shizhi'])
            df_zero[:] = 0
            df_zero = df_zero + df_hisdat['shizhi']
            df_first_shizhi = copy.deepcopy(df['shizhi'])
            df_first_shizhi[:] = first_shizhi
            df_first_shizhi[np.isnan(df_zero)] = 0
            df_zero = df_zero.fillna(0)
            df['shizhi'] = df['shizhi'] + df_zero
            df['jizhun'] = df['jizhun'] + df_first_shizhi
            #df['shizhi'] += df_hisdat['shizhi'].fillna(0)
            #df['jizhun'] += first_shizhi
    if df.empty:
        return pd.Series([])
    df = df[df['shizhi']>0]
    df['zhishu'] = df['shizhi'] / df['jizhun']
    return df['zhishu']
def test_calc_bankuai_zhishu():
    codes = ['600100', '600601', '600680', '600850', '600855', '603019', '000021', '000066', '000748', '000938', '000948', '000977', '000997', '002027', '002152', '002177', '002197', '002236', '002308', '002312', '002376', '002383', '002415', '002528', '002577', '300042', '300045', '300065', '300130', '300155', '300177', '300202', '300270', '300302', '300333', '300367', '300368', '300386']
    ltgbs = [20.7, 21.95, 2.57, 1.71, 3.3, 0.75, 14.7, 13.24, 3.76, 2.06, 2.31, 4.3, 5.08, 2.03, 8.63, 5.43, 2.11, 6.6, 8.36, 3.04, 4.88, 1.1, 31.5, 3.38, 2.83, 0.73, 1.55, 1.61, 0.74, 1.78, 2.36, 5.5, 0.63, 0.41, 0.81, 0.61, 0.35, 0.2]
    date = '2015-8-4'
    #calc_bankuai_zhishu(codes, date, agl.CurDay(), ltgbs)
    calc_bankuai_fenshi_zhishu(codes, date, agl.CurDay(), ltgbs)
def run_adx():
    code = '300033'
    df_five_hisdat = getFiveHisdatDf(code,'2016-1-1')
    highs, lows, closes = df_five_hisdat['h'], df_five_hisdat['l'], df_five_hisdat['c']    
    adx = TDX_ADX(highs, lows, closes)
    return adx    
class mytest(unittest.TestCase):
    def _test1(self):
        self.assertFalse(0)
    def _test_calc_bankuai_zhishu(self):
        codes, date, end_day, ltgbs = (['601268'], '2014-5-1', '2015-09-25', [16.9])
        calc_bankuai_fenshi_zhishu(codes, date, end_day, ltgbs)	
    def _test_calc_fuquan(self):
        code = '002407'
        ths = createThs()
        df = mysql.getHisdat(code)
        one = ths.createThsOneCode(code)
        #复权计算
        df_fenhong = one.get_fenhong()
        df = calc_fuquan_use_fenhong(df, df_fenhong)
        print(df)
    def _test_mgsy(self):
        ths = createThs()
        for code in ['002027']:
            price = getHisdatDataFrameFromRedis(code).iloc[-1]['c']
            one = ths.createThsOneCode(code, price)
            print(one.get_name(), one.get_mgsy(), one.get_syl())
    def _test_codes(self):
        #print get_codes(myenum.randn,100)
        #for bankuai in createThs().getBankuais():
            #print bankuai
        codes = get_codes()
        print(get_codes())
        print(len(codes))
        print(len(mysql.get_codes()))
    def _test_adx(self):
        code = '300033'
        df_five_hisdat = mysql.getFiveHisdat(code, start_day='2017-6-14')
        #df_five_hisdat = pd.read_csv('../test.csv')
        df_five_hisdat = df_five_hisdat.sort_index()
        #agl.print_df(df_five_hisdat)
        highs, lows, closes = df_five_hisdat['h'], df_five_hisdat['l'], df_five_hisdat['c']
        adx = ADX(highs, lows, closes)
        #ui.DrawTs(pl, ts=closes,high=adx)
        print(adx[-1])
        adx = TDX_ADX(highs, lows, closes)
        print(adx[-1], len(adx))
        print(adx[-5:])
        #经观测， 基本一致
        #ui.DrawTs(pl, ts=closes[-100:],high=adx[-100:])
    def _test_boll(self):
        code = '300113'
        df_five_hisdat = getFiveHisdatDf(code,'2017-5-1')
        #print(closes)
        #upper, middle, lower = BOLL(df_five_hisdat['c'])
        #print(upper[-1], lower[-1])
        upper, middle, lower = TDX_BOLL(df_five_hisdat['c'])
        print upper[-10:]
        print middle[-10:]
        print lower[-10:]
        #df_five_hisdat['upper'] = upper
        #df_five_hisdat['lower'] = lower
        #df_five_hisdat['mid'] = middle
        #df = df_five_hisdat[['upper', 'c', 'mid', 'lower']]
        #df.plot()
        #pl.show()
        upper, middle, lower, boll_w = TDX_BOLL2(df_five_hisdat['c'])
        print boll_w
    def _test_livedata(self):
        code = '300033'
        #print LiveData().getFiveMinHisdat('000043')
        print(LiveData().getFenshi(code))
    def _test_ths(self):
        agl.tic()
        ths = createThs()
        agl.toc()
        code1 = '002074'
        code1 = '600981'
        code1 = '600120'
        price = getHisdatDataFrameFromRedis(code1).iloc[-1]['c']
        code = ths.createThsOneCode(code1, price=price)
        print(code._get_mgsy_3())
        df = code.get_YinLi()
        #因为是倒序， 因此截断日期在后面
        print(df)
        print(df['2011-1-1':])
        print(code.get_syl())
    def _test_account(self):
        print('test account T+1')
        acount = Account(1000000)
        code = '600100'
        price = 13
        acount.buy(code, price, 3000,'2016-5-2 9:30:00')
        acount.sell(code, price, 300,'2016-5-2 9:40:00')
        acount.sell(code, price+0.1, 2000, '2016-5-3')
        acount.buy(code, price, 500,'2016-5-3 10:0:0')
        acount.sell(code, price, 500,'2016-5-3 10:2:0')
        acount.sell(code, price+0.1, 3000, '2016-5-3')
        print(acount.get_WeituoDf(day='2016-5-3'))
        acount.myprint([(code, 15)])
    def _test_fenshi_fuquan(self):
        #5-9除权
        code, start_day, end_day = '002560', '2016-3-1','2016-5-20'
        df = getHisdatDf(code, start_day, end_day, True)
        #df = FenshiEx(code, start_day, end_day, True).df
        print(df)
    def test_Bankuais(self):
        #myredis.delkey(myredis.enum.KEY_BANKUAIS)
        for bankuai in get_bankuais():
            print bankuai
        print filter(lambda x: x.find('360')>=0, get_bankuais())
    def _test_bankuai_analyze(self):
        StockInfoThs.Test_Bankuai_Zhishu()
    def _test_GetCodeName(self):
        print GetCodeName('603444')
    def _test_get_ths_codes(self):
        print getTHS_custom_codes()
def IsKaiPan():
    """确定当前是处于开盘时间 return: bool"""
    t = ['9:31:00','11:30:00','13:00:00', '15:03:00']	#后面的3分钟让策略执行一些收盘工作
    for i in range(len(t)):
        t[i] = dateutil.parser.parse(t[i]).time()
    cur_t = time.localtime()
    cur_t = datetime.time(cur_t.tm_hour, cur_t.tm_min, cur_t.tm_sec)
    if (cur_t >= t[0] and cur_t<= t[1]) or (cur_t>t[2] and cur_t <t[3]):
        return True
    return False
def calc_bankuai_fenshi_zhishu(codes, date, end_day, ltgbs):
    """计算板块分时指数,
    1.取大盘的开盘天数
    2.收盘后的3分钟集合竞价沪深不一样，开盘时间内的nan用前面的值填充
    codes: list 代码
    date: 基准日
    end_day: 
    ltgbs: list 流通股本
    cur_code: 当前股票的代码
    return: pd.Series 指数 name=zhishu """
    #开盘时间
    t = ['9:30:00','11:30:00','13:00:00', '15:00:00']
    for i in range(len(t)):
        t[i] = dateutil.parser.parse(t[i]).time()

    def get_kaipan_days():
        """return: list [Timestamp, ...]"""
        code = myenum.DaPan.shanghai
        kline = Guider(code, start_day=date, end_day=end_day)
        df = kline.ToDataFrame()
        days = df.index.tolist()
        return days
    def fill_fenshi_nan(df_fenshi, days):
        """把开盘时间内的nan用前一个值填充
        df_fenshi: df
        days: 开盘的日期, 与df_fenshi里的日期对应， 如果是停牌， 就用前一个收盘填充
        return: df 填充后的df"""
        if 0: df_fenshi = pd.DataFrame
        #对于分时， 判断时间范围内的nan， 并用前一个值填充
        nonan_row = None
        for i in xrange(len(df_fenshi)):
            row = df_fenshi.iloc[i]
            cur_t = row.name.time()
            if (cur_t >= t[0] and cur_t<= t[1]) or (cur_t>t[2] and cur_t <t[3]):
                #填充nan
                if np.isnan(row.p):
                    df_fenshi.set_value(df_fenshi.index[i], \
                                        df_fenshi.columns, \
                                        nonan_row.get(df_fenshi.columns))
                else:
                    nonan_row = row
        return df_fenshi
    days = get_kaipan_days()
    #cur_day = agl.CurDay()
    df = pd.DataFrame(index = pd.period_range(date, end_day,freq='1min').to_datetime())
    for i, code in enumerate(codes):
        #print 'calc_bankuai_zhishu ', code
        df_fenshi = getFenshiDfUseRedis(code, date, end_day)
        if len(df_fenshi) == 0:
            continue
        ltgb = ltgbs[i]
        df_fenshi['shizhi'] = ltgb * df_fenshi['p']
        first_shizhi = df_fenshi.dropna().iloc[0]['shizhi']	
        if first_shizhi<=0:
            continue
        df_fenshi['zhishu'] = df_fenshi['shizhi'] / first_shizhi
        #agl.print_df(df_fenshi)
        df_fenshi = fill_fenshi_nan(df_fenshi, days)
        df_fenshi = df_fenshi.fillna(0)
        #删除最后的2分钟
        #df_fenshi = df_fenshi[:-30]
        if len(df.columns) == 0:
            df['shizhi'] = df_fenshi['shizhi']
            #基准市值
            df['jizhun'] = first_shizhi
        else:
            assert(first_shizhi > 0)
            df['shizhi'] = df['shizhi'].fillna(0)
            #不对停牌的股票进行统计
            df_zero = copy.deepcopy(df['shizhi'])
            df_zero[:] = 0
            df_zero = df_zero + df_fenshi['shizhi']
            df_first_shizhi = copy.deepcopy(df['shizhi'])
            df_first_shizhi[:] = first_shizhi
            df_first_shizhi[np.isnan(df_zero)] = 0
            df_zero = df_zero.fillna(0)
            df['shizhi'] = df['shizhi'] + df_zero
            df['jizhun'] = df['jizhun'] + df_first_shizhi
            #df['shizhi'] += df_hisdat['shizhi'].fillna(0)
            #df['jizhun'] += first_shizhi
    if df.empty:
        return pd.Series([])
    df = df[df['shizhi']>0]
    df['zhishu'] = df['shizhi'] / df['jizhun']
    return df['zhishu']
def summary_bankuai_zhangfu(codes, end_day):
    """统计板块各个股的涨幅分布, 返回板块涨幅区间归属
    区间范围为 (-0.11,-0.097, -0.06,-0.03,-0.01,0, 0.01, 0.03, 0.06, 0.097,0.11,0.5)
    return: df col=zhangfu, type"""
    if end_day == '':
        end_day = getKlineLastDay()
    start_day = help.MyDate.s_Dec(end_day, -10)
    zhangfus = []
    for code in codes:
        df_hisdat = getHisdatDataFrameFromRedis(code, start_day, end_day)
        if len(df_hisdat)>=2:
            zhangfu = ZhengFu(df_hisdat['c'].iloc[-2], df_hisdat['c'].iloc[-1])
            zhangfus.append(zhangfu)
    #根据分割区间， 填写到type字段    
    df = pd.DataFrame(zhangfus)
    if len(df) == 0:
        return df
    df.columns = ['zhangfu']
    df['type'] = ''
    intervals = (-0.11,-0.097, -0.06,-0.03,-0.01,0, 0.01, 0.03, 0.06, 0.097,0.11,0.5)
    for j in range(len(df)):
        for i in range(len(intervals)-1):
            s =  intervals[i:i+2]
            v = df.iloc[j][0]
            if v>=s[0] and v<s[1]:
                df.iloc[j] = df.iloc[j].set_value('type', str(s))
    return df
def test_summary_bankuai_zhangfu():
    codes = ['600100', '600601', '600680', '600850', '600855', '603019', '000021', '000066', '000748', '000938', '000948', '000977', '000997', '002027', '002152', '002177', '002197', '002236', '002308', '002312', '002376', '002383', '002415', '002528', '002577', '300042', '300045', '300065', '300130', '300155', '300177', '300202', '300270', '300302', '300333', '300367', '300368', '300386']    
    day = '2015-3-1'
    summary_bankuai_zhangfu(codes, end_day=day)
def BETA(df, df_dp, pl=None):
    """指数相关性, 调整大盘或板块指数，然后计算标准差，即为beta 
    df: 个股pd.Series, 带index
    df_dp: 指数 pd.Series
    return: df 标准差beta 调整后的指数 df.columns=beta,stock,zhishu"""
    #同步df与df_dp, 去除数据缺失
    for i in range(2):
        if len(df) > len(df_dp):
            df = df[df.index.map(lambda x: x in df_dp.index)]
        else:
            df_dp = df_dp[df_dp.index.map(lambda x: x in df.index)]
    assert(len(df) == len(df_dp))	    
    if len(df) == 0:
        raise myenum.FenshiBetaTinPaiException

    df = GuiYiHua(df)
    df_dp = GuiYiHua(df_dp)

    #移动df_dp, 发现方差最小，且数据重合最多的位置, 最后把df_dp移动到重叠的位置， 再算一次标准差
    temp = max(np.max(df_dp), np.max(df)) * 100 
    if np.isnan(temp): temp = 0
    high = int(temp)
    temp = min(np.min(df), np.min(df_dp)) * 100
    if np.isnan(temp): temp = 0
    low = int(temp)

    fang_chas = []
    for i in range(low, high):
        df_dp_1 = df_dp - (df_dp.iloc[0] - float(i)/ 100.0)
        fang_cha = np.sum(np.abs(df_dp_1 - df)) ** 2
        #print i, fang_cha
        fang_chas.append(fang_cha)
    fang_chas = np.array(fang_chas)
    if len(fang_chas)>0:
        i = np.argmin(fang_chas)
        i = range(low, high)[i]
        #print i
        df_dp = df_dp - (df_dp.iloc[0] - float(i)/ 100.0)
    df_result =  df - df_dp
    if pl != None:
        pl.figure
        #df.plot()
        df.plot()
        df_dp.plot()
        df_result.plot()
        pl.legend(['stock','zhishu','beta'], loc='upper left')
        pl.show()    
        pl.close()
    df2 = pd.DataFrame([])
    df2['beta'] = df_result
    df2['stock'] = df
    df2['zhishu'] = df_dp
    return df2
def get_onecode_beta(code, day, pl=None):
    """计算一个股票与大盘指数之间的beta关系
    return: None or df df.columns=beta,stock,zhishu"""
#day = '2013-4-1'
    df = Guider(code, day).ToDataFrame()
    if len(df) == 0:
        return None
    code_dapan = getDapanCode(code)
    df_dp = Guider(code_dapan, day).ToDataFrame()
    return BETA(df['c'], df_dp['c'], pl)
def test_beta():
    pl = publish.Publish()
    days = pd.period_range(start='2014-8-1', end='2015-4-28', freq='Q' )
    codes = get_codes(myenum.randn, 5)
    codes = ['603005']
    for code in codes:
        for day in days.to_datetime():
            day = str(day.date())
            get_onecode_beta(code, day, pl)
def calc_fuquan_use_fenhong(df, df_fenhong):
    """获取复权后的历史数据, 用分红表来计算复权 , 前复权
    df: 日k线
    df_fenhong: 分红表
    return: df"""
    if len(df_fenhong) == 0:
        return df
    #有些分红表先把未来的日期写上了
    #用df的最后日期截断分红表
    end_day = agl.datetime_to_date(df.index[-1])
    df_fenhong = df_fenhong[df_fenhong[2].map(lambda x: help.DateToInt(x)<=help.DateToInt(end_day))]
    #日期早的在前面
    df_fenhong = df_fenhong.sort_values(by=2)
    for i in range(len(df_fenhong)):
        gu, money, date = df_fenhong.iloc[i]
        if len(df.ix[:date]) < 2:
            continue
        date = agl.df_get_pre_date(df, date)
        if money > 0:
            money = money * 0.1
            df['o'].ix[:date] -= money
            df['h'].ix[:date] -= money
            df['c'].ix[:date] -= money
            df['l'].ix[:date] -= money
        if gu > 0:
            # x = cur / (1+y/10)
            gu = 1+gu/10
            df['o'].ix[:date] /= gu
            df['h'].ix[:date] /= gu
            df['c'].ix[:date] /= gu
            df['l'].ix[:date] /= gu
    return df	    
def test_calc_fuquan_use_fenhong():
    ths = createThs()
    code = get_codes(myenum.randn, 1)[0]
    print(code)
    df = mysql.getHisdat(code)
    one = ths.createThsOneCode(code)
    df_fenhong = one.get_fenhong()
    print(df_fenhong)
    print(calc_fuquan_use_fenhong(df, df_fenhong))

def test_get_yjyb():
    ths = StockInfoThs()
    df = ths.getDf(1)
    #for code in df['code']:
        #print ths.createThsOneCode(code).get_mgsy()
    code = '002195'
    print(ths.createThsOneCode(code).get_mgsy())
g_ths = None
if 0: createThs = StockInfoThs
def createThs():
    """注意：在stock中执行的，别的模块不认， 因此需要在bankuai_zhishu.py中执行
    返回一个序列化的类, 单件, return: StockInfoThs"""
    def create():
        return StockInfoThs()
    global g_ths
    if g_ths is None:
        g_ths = agl.SerialMgr.serialAuto(create)
    return g_ths

class StockInfoThs:
    """基于同花顺的F10"""

    def __init__(self):
        self.pl = None
        self.d = grabThsWebStockInfo.getThsResults()
        self._ChangeDf()
        self._calcHySyl()
    def _ChangeDf(self):
        """调整df"""
        #把财务预测的时间索引提前一年
        name = '盈利预测'
        if name in self.d.keys():
            df = self.d[name]
            df_year = df[0].map(lambda x: str(int(x)+1))
            df.index = pd.DatetimeIndex(df_year)
            df.columns = ['年', '每股收益','利润(亿元)','预测','code','name']
            self.d[name] = df	

        #市盈率为--认为是亏损
        name = '概要'
        if name in self.d.keys():
            df = self.d[name]
            #df = df.dropna()
            def StrConvert(x):
                try:
                    y = float(x)
                except:
                    x = '10000'
            #df['市盈率动态'] = df['市盈率动态'].map(lambda x: x.replace('--','10000'))
            df['市盈率动态'] = df['市盈率动态'].map(StrConvert)
            #用最新的预报替换当前的市盈率
            df['市盈率动态'] = df['code'].map(lambda x: self.createThsOneCode(x, True).get_syl())
            self.d[name] = df
    def _calcHySyl(self):
        """把每个行业的2,3级市盈率计算出来， 放到一张新表中"""
        def getHySyl(df, bankuai):
            """求行业平均市盈率, 不统计超过1000的市盈率
            df: 数据源， 概要表
            bankuai: 板块
            return: list [平均市盈率, 第一个聚类, kmeans_2,percent1,  percent2, total_num]"""
            codes = self.getBankuaiCodes(bankuai)	    
            df_hy = df[df['code'].map(lambda x: x in codes)]
            df_hy = df_hy['市盈率动态']
            df_hy = df_hy.dropna()
            df_hy = df_hy.map(lambda x: float(x))
            df_hy = df_hy[df_hy< 1000]		   
            total = len(df_hy)
            if len(df_hy) == 0:
                return [np.nan, np.nan, np.nan, np.nan, np.nan]
            avg = np.average(np.array(df_hy))
            if len(df_hy)<3:
                return [avg, help.p(avg), '100%', np.nan, np.nan, total]
            #计算聚类
            results_n = np.zeros((len(df_hy),2))
            results_n[:,0] = 1
            results_n[:,1] = np.array(df_hy)
            k = KMeans(n_clusters=2)
            k.fit(results_n)
            a = (k.cluster_centers_[0,1], help.getPercentString(float(len(k.labels_[k.labels_==0]))/total) )
            b = (k.cluster_centers_[1,1], help.getPercentString(float(len(k.labels_[k.labels_==1]))/total) )
            #范围大的放前面
            if len(k.labels_[k.labels_==0]) < len(k.labels_[k.labels_==1]):
                c = a
                a = b
                b = c
            return [help.p(avg), help.p(a[0]),a[1], help.p(b[0]), b[1], total]
        df = self.getDf(0)
        d = {}
        bankuais = self.getBankuais()
        for bankuai in bankuais:
            d[bankuai] = getHySyl(df, bankuai)
        df = pd.DataFrame(d.values())
        df['key'] = d.keys()
        #df[1] = df[1].map(lambda x: agl.get_string_digit(str(x).split(',')[0]))
        df[1] = df[1].astype(float)
        df = df.sort_values(by=1)
        df.columns = ['平均市盈率','低位聚类市盈率','percent1', 'kmean2','percent2', '数量','行业及概念']
        #agl.print_df(df)
        self.d['平均市盈率'] = df
    def getDf(self, table_id):
        """取一个表 return: df"""
        df = self.d[StockInfoThs._getGrabThsTableNames()[table_id]]
        return df
    def getYcTable(self):
        """return : df 盈利预测"""
        df = self.d['盈利预测']
        return df
    def getPjSylTable(self):
        """return: df 平均市盈率"""
        return self.d['平均市盈率']
    def getHySyl(self, hy):
        """获取平均市盈率表中的行业市盈率 return: float"""
        df = self.getPjSylTable()
        return df[df['行业及概念'] == hy]['低位聚类市盈率'].get_values()[0]
    def size(self):
        return len(self.d.keys())
    def getDf_Code(self, table_id, code):
        """一个表中code记录, 一行 return: df"""
        df = self.getDf(table_id)
        return df[df['code'] == code]
    @staticmethod
    def _getGrabThsTableNames():
        table_names = ['概要','新闻','解禁','盈利预测','机构推荐',\
                       '财务主要指标_汇报期','财务主要指标_年','财务主要指标_单季度','分红融资']
        try:
            table_names = grabThsWebStockInfo.GrabThsWeb.table_names
        except:
            pass        
        return table_names
    def getCodeDict(self, code):
        d = {}
        for i,k in enumerate(StockInfoThs._getGrabThsTableNames()):
            d[k] = self.getDf_Code(i, code)
        return d
    def getBankuais(self):
        """获取全部的板块和概念 return: np.ndarray"""
        codes = get_codes()
        bankuais = []
        for code in codes:
            bankuai = self.createThsOneCode(code).get_bankuai()
            bankuais += bankuai.tolist()
        bankuais = np.unique(np.array(bankuais))
        bankuais = bankuais[bankuais != '']
        return bankuais
    def getBankuaiCodes(self, bankuai):
        """得到同板块的其他股票
        bankuai: str 板块名称
        return: np.darray [code]"""
        codes = []
        names = ['所属行业', '涉及概念','概念强弱排名']
        df = self.getDf(0)
        for i in range(len(df)):
            r = df.iloc[i]
            code = r['code']
            bankuai_cur = ''
            for name in names:
                if name in df.columns:
                    bankuai_cur += str(r[name])
            if bankuai_cur.find(bankuai) >= 0:
                codes.append(code)
        return np.array(codes)
    def analyze_bankuai_beta(self, code, start_day, end_day, is_report=False):
        """分析个股中板块相关度最高的那个板块， 并求出beta
        return: (int beta[-1], str bankuai_name, df 板块涨幅分布col=zhangfu,type)"""
        if not hasattr(StockInfoThs, 'pl'):
            self.pl = None
        if is_report:
            if self.pl == None:
                self.pl = publish.Publish()
            else:
                del self.pl
                self.pl = publish.Publish()	
        else:
            self.pl = None
        one = self.createThsOneCode(code)
        if is_report:
            print(code, one.get_name(), '关联的行业指数')
            print('从', start_day, '开始 到', end_day)
        hy = one.get_bankuai()
        df_hisdat = getHisdatDataFrameFromRedis(code, start_day, end_day)
        df_bankuai = pd.DataFrame(columns=['bankuai', 'beta', 'val'])	#把板块名称和beta值记录起来
        i = 0
        for s in hy:
            if len(s) == 0:
                continue
            df_zhishu = getHisdatDataFrameFromRedis(s, start_day,end_day)
            assert(df_zhishu is not None)
            df = pd.DataFrame([])
            df['zhishu'] = df_zhishu
            df['stock'] = df_hisdat['c']
            df = GuiYiHua(df)
            if is_report:
                ui.drawDf(self.pl, df, title=s)
            df_betas = BETA(copy.deepcopy(df['stock']), copy.deepcopy(df['zhishu']), self.pl)
            #集成板块名称和beta结果
            df_bankuai.loc[i] = [s, df_betas['beta'].var(), df_betas['beta'].tolist()[-1]]
            i += 1
        if pd.isnull(df_bankuai['beta']).all() == True:
            raise myenum.FenshiBetaTinPaiException
        bankuai = df_bankuai.iloc[np.argmin(df_bankuai['beta'])]['bankuai']
        if is_report:
            print(df_bankuai.sort(columns=['beta']))
            print('result: ', bankuai)
        #涨幅分布
        codes = self.getBankuaiCodes(bankuai)
        codes = codes[codes!=code]
        if len(codes) == 0:
            codes = [code]
        #end_day = getKlineLastDay()
        df = summary_bankuai_zhangfu(codes, end_day)
        if is_report:
            if len(df)>0:
                print(df.describe())
                print(df['type'].value_counts())

        return (df_bankuai.iloc[np.argmin(df_bankuai['beta'])]['val'], bankuai,df)
    @staticmethod
    def getHyAvgSyl(df, hy):
        """获取行业平均市盈率
        df: 概要表, 已计算four技术指标的概要表
        hy: 行业名称
        return: float 平均市盈率, df 过滤后的df"""
        df_hy = df[df['所属行业'].map(lambda x: x.find(hy)>=0)]
        return np.average(np.array(df_hy['市盈率动态'], dtype=float)), df_hy
    @staticmethod
    def getGnAvgSyl(df, gn):
        """获取概念平均市盈率
        df: 概要表, 已计算four技术指标的概要表
        gn: 概念名称, 或者是正则表达式
        return: float 平均市盈率, df 过滤后的df"""
        def re_hy(x):
            x = str(x)
            return re.search(gn, x) != None
        #df_hy = df[df['涉及概念'].map(re_hy)]
        #if len(df_hy) == 0:
        df_hy = df[df['概念强弱排名'].map(re_hy)]
        # df_hy[['code','name','市盈率动态', 'four','流通A股']]
        if len(df_hy) == 0:
            return np.nan, df_hy
        return np.average(np.array(df_hy['市盈率动态'], dtype=float)), df_hy
    @staticmethod
    def genCodeNameTbl():
        """在redis中创建一份代码名称dict"""
        ths = createThs()
        df = ths.getDf(0)
        df = df[['code', 'name']]
        return df
    class ThsOneCode:
        def __init__(self, d, price=0):
            self.d = d
            self.price = price
        if 0: getDf = pd.DataFrame
        def getDf(self, table_id):
            """取一个表 return: df"""
            df = self.d[StockInfoThs._getGrabThsTableNames()[table_id]]
            return df	
        def get_name(self):
            """return: str 股票名称"""
            return self.getDf(0)['name'].tolist()[0]
        def get_syl(self):
            """return: float 市盈率"""
            syl = SYL(self.price, self.get_mgsy())
            if syl < 0:
                syl = 10000
            return syl
        def _get_mgsy_3(self):
            """获取每股收益及其预报的时间
            return: 年度净利润, 利润预告时间, 该预告是否有效(在披露之前)"""
            quarters = ['03-31','06-30','09-30','12-31']
            mgsy , quarter = self.get_mgsy_2()
            quarter -= 1
            year = str(agl.curTime().year)
            cur_quarter = int(agl.curTime().month / 3)
            is_valid = abs(cur_quarter - quarter ) < 2
            return mgsy*self.get_zgb(), year+'-'+quarters[quarter], is_valid
        def get_mgsy_2(self):
            """最新的每股收益
            df: 某code的新闻表
            return: float 每股收益, int 季度"""
            df = self.getDf(1)
            if len(df) == 0:
                return 0, 4
            assert(len(df)>0 and len(df.columns))
            #已披露的业绩
            #print df[1]
            df_pilu = df[df[1].map(lambda x: str(x).find('业绩披露') >=0)]
            #预告业绩
            df = df[df[1].map(lambda x: str(x).find('业绩预告')== 0)]
            def getQuarter(s):
                quarter = 0
                #计算当前现实季度
                quarter = agl.getQuarter(agl.curTime())
                if s.find('03-31')>=0 or s.find('一季报')>=0:	#确认是第一季报
                    quarter = 1
                if s.find('06-30')>=0 or s.find('中报')>=0 or s.find('二季报')>=0:
                    quarter = 2
                if s.find('09-30')>=0 or s.find('三季报')>=0:
                    quarter = 3
                if s.find('12-31')>=0 or s.find('年报')>=0:
                    quarter = 4	
                assert(quarter>0)
                return quarter
            def getYuBaoDate(s):
                """获取预报日期"""
                quarters = ['一季报','中报','三季报','年报']
                dates = ['03-31','06-30','09-30','12-31']
                for date in dates:
                    pos = s.find(date)
                    if pos > 0:
                        d = s[pos-5:pos+len(date)]
                        return d
                #文字里只写了季度
                s = s[:50]
                for i,date in enumerate(quarters):
                    pos = s.find(date)
                    if pos > 0:
                        cur_year = agl.CurYear()
                        cur_day = agl.CurDay()
                        yubao_date = str(cur_year) + '-'+dates[i]
                        #解决跨年预报问题, 在上半年预报当年年报业绩不太可能
                        if i>2 and help.StrToDate(cur_day)<help.StrToDate(cur_year+'-6-30'):
                            cur_year = str(int(cur_year)-1)
                            yubao_date = cur_year + '-' + dates[i]
                        return yubao_date
                return ''
            def getPiLuDate(s):
                """获取披露的日期"""
                quarters = ['一季报','中报','三季报','年报']
                dates = ['03-31','06-30','09-30','12-31']
                for i,date in enumerate(quarters):
                    pos = s.find('年'+date)
                    if pos > 0:
                        d = s[pos-4:pos] + '-' + dates[i]
                        return d
                return ''
            #业绩预告：预计2014-01-01到2014-12-31业绩：净利润8000万元至8500万元,增长幅度为1915.72%至2041.71%,上年同期业绩:...
            def IsYugaoBeforePilu():
                """预告的内容时间大于当前披露的业绩， 比如已经披露三季报， 
                但预告的是12-31年报的业绩
                return : bool"""
                if len(df) == 0: return False
                #找到最大的预报时间
                yubao_date = '2015-1-1'
                for s in df[1].tolist():
                    date = getYuBaoDate(s)
                    if date != '':
                        if help.StrToDate(date) - help.StrToDate(yubao_date) > datetime.timedelta(0):
                            yubao_date = date
                #找到最大的披露时间
                pilu_date = '2015-1-1'
                for s in df_pilu[1].tolist():
                    date = getPiLuDate(s)
                    if date != '':
                        if help.StrToDate(date) - help.StrToDate(pilu_date) > datetime.timedelta(0):
                            pilu_date = date
                if pilu_date == '2015-1-1':
                    return True
                return help.StrToDate(yubao_date) - help.StrToDate(pilu_date) > datetime.timedelta(0)
            #预告在披露的时间之前
            is_yugao_first = IsYugaoBeforePilu()
            if is_yugao_first or (len(df) > 0 and (len(df_pilu)>0 and df.index[0] > df_pilu.index[0])):
                for s in df[1].tolist():
                    #先把多余的切割掉
                    s1 = agl.find_str_use_re('^(.*)上年同期业绩(.*)$', s, 0)
                    if s1 != '':
                        s = s1		
                    s1 = agl.find_str_use_re('^业绩预告(.*)净利润([-.\d]+)万元至([-.\d]+)万元(.*)$', s, 1)
                    s2 = agl.find_str_use_re('^业绩预告(.*)净利润([-.\d]+)万元至([-.\d]+)万元(.*)$', s, 2)

                    #对于季报，预测是要做相应的处理， 比如第一季度，那么要*4
                    quarter = 1
                    quarter = getQuarter(s)
                    #...等半年报时再来处理...
                    if s1 != "" and s2 != "":
                        #不取中间值， 按黄金分割
                        v = [float (s1), float(s2)]
                        s = agl.calcGoldCut(v, ratio=0.5)
                        return (s/10**4)/self.get_zgb()*(4.0/quarter), quarter
                    #新版写法2016-10-2
                    s1 = agl.find_str_use_re('^业绩预告(.*)净利润([-.\d]+)亿元至([-.\d]+)亿元(.*)$', s, 1)
                    s2 = agl.find_str_use_re('^业绩预告(.*)净利润([-.\d]+)亿元至([-.\d]+)亿元(.*)$', s, 2)
                    if s1 != "" and s2 != "":
                        #不取中间值， 按黄金分割
                        v = [float (s1), float(s2)]
                        s = agl.calcGoldCut(v, ratio=0.5)
                        return (s)/self.get_zgb()*(4.0/quarter), quarter
                    jtsyl = agl.get_string_digit(self.d['概要']['市盈率静态'][1])
                    if jtsyl < 0:
                        jtsyl = 10000
                    s1 = agl.find_str_use_re('^业绩预告(.*)下降幅度为([-.\d]+)%至([-.\d]+)%(.*)$', s, 1)
                    if s1=='':
                        s1 = agl.find_str_use_re('^业绩预告(.*)下降幅度为([-.\d]+)%(.*)$', s, 1)
                    if s1 != "":
                        s = -float (s1)/100
                        #(now-yes)/yes = up => now = (up+1)*yes
                        return (s+1.0)/jtsyl, quarter
                    s1 = agl.find_str_use_re('^业绩预告(.*)增长幅度为([-.\d]+)%至([-.\d]+)%(.*)$', s, 1)
                    if s1=='':
                        s1 = agl.find_str_use_re('^业绩预告(.*)增长幅度为([-.\d]+)%(.*)$', s, 1)
                    if s1 != "":
                        s = float (s1)/100
                        return (s+1.0)/jtsyl, quarter

            #通过财务报表取每股收益, 因为有分红转增， 所以还是要用概要里的，季节可由财务汇报中获得
            str_mgsy = self.d['概要']['每股收益'].tolist()[0]
            str_mgsy = str(str_mgsy)
            #b_fhzz = str_mgsy.find("分红")>=0  #是否有分红转增
            mgsy = agl.get_string_digit(str_mgsy)
            quarter= getQuarter(str(self.d['财务主要指标_汇报期'].index[0]))

            pre_year = str(agl.curTime().year-1)
            if len(df_pilu):
                for s in df_pilu[1].tolist():
                    if s.find(str(mgsy))>0:
                        if s.find('一季报')>0 :
                            #在公告里的才是真正的一季度收益
                            str_content = s
                            s = agl.find_str_use_re('^(.*)每股收益([-.\d]+)元(.*)$', str_content, 1)
                            #如果有除权， 那么还是用原来的
                            if s != "" :
                                mgsy = float(s)
                            quarter = np.max([1, quarter])
                        if s.find('中报')>0:
                            quarter = np.max([2, quarter])
                        if s.find('三季报')>0:
                            quarter = np.max([3, quarter])
                        if s.find('年报')>=0:
                            quarter = np.max([4, quarter])
            #每股收益/4*季度=当前的季报 => 每股收益=当前季报*4/季度
            mgsy = mgsy * 4 / quarter
            return mgsy, quarter
        def get_mgsy(self):
            mgsy , quarter = self.get_mgsy_2()
            return mgsy
        def get_YinLi(self):
            """获取盈利 , 把季度利润反推为年度利润
            return: np.array"""
            df = self.getDf(6)[u'净利润万元']
            yinli , yugao_date, is_valid = self._get_mgsy_3()
            yinli = float(yinli)*10**4
            df = df.astype(float)
            df[df.index.map(lambda x: str(x).find('3-31')>0)] = df[df.index.map(lambda x: str(x).find('3-31')>0)]*4
            df[df.index.map(lambda x: str(x).find('6-30')>0)] = df[df.index.map(lambda x: str(x).find('6-30')>0)]*2
            df[df.index.map(lambda x: str(x).find('9-30')>0)] = df[df.index.map(lambda x: str(x).find('9-30')>0)]*4.0/3.0
            #添加预告业绩
            if len(df[yugao_date]) == 0 and is_valid:
                df = df.append(pd.Series([yinli], index=pd.DatetimeIndex([yugao_date])))
            df = df.sort_index()
            return df
        def get_zgb(self):
            """总股本, 单位， 亿股
            return : float"""
            df = self.getDf(0)
            return agl.get_string_digit(df['总股本'].tolist()[0])
        def get_ltgb(self):
            """流通股本, 亿股 return: float"""
            return agl.get_string_digit(self.d['概要']['流通A股'].tolist()[0])
        def get_bankuai(self):
            """获取当前股票的所属行业和概念板块
            return: np.ndarray 按，分割的字符串"""
            names = ['所属行业', '涉及概念','概念强弱排名']
            df = self.getDf(0)
            if len(df) == 0:
                return np.array([])
            hy = df[names[0]]
            if not isinstance(hy, str):
                hy = hy.tolist()[0]
                hy = hy.split(',')[1:]
            #现在概念标题既有使用‘涉及概念'的也有使用’概念强弱排名‘的
            if names[2] in df.columns:
                gn = df[names[2]]
                if isinstance(gn.iloc[0], str):
                    s = gn.iloc[0]
                    s = s.replace('详情>', '')
                    s = s.replace('...', '')
                    gn = s.split('，')
                    hy += gn
            hy = np.unique(np.array(hy))
            if len(hy) > 0:
                hy = hy[hy != '']
            return hy
        def get_fenhong(self):
            """获取分红记录 (说明, 股， 派现，除权日)
            分红表有时候更新不及时， 可能需要等待
            return: df columns('股，现金, 日期')"""
            df = self.getDf(-1)
            #获取分红表
            df_fenhong = pd.DataFrame([])#股，现金, 日期
            for i in range(len(df)):
                #方案说明
                content = df.iloc[i]['分红方案说明']
                #content = '送1.2转增2.4股派3.45元'
                #取派股信息
                gu = agl.find_str_use_re('^(.*)送([\d.]+)(.*)$', content, 1)
                if gu == '': gu=0
                gu = float(gu)
                gu2 = agl.find_str_use_re('^(.*)转([\d.]+)(.*)$', content, 1)
                if gu2 == '':
                    gu2 = agl.find_str_use_re('^(.*)转增([\d.]+)(.*)$', content, 1)
                if gu2 == '': gu2 = 0
                gu2 = float(gu2)
                gu = gu + gu2
                money = agl.find_str_use_re('^(.*)派([\d.]+)元(.*)$', content, 1)
                if money == '':
                    money = agl.find_str_use_re('^(.*)现金([\d.]+)元(.*)$', content, 1)
                if money == '': money = 0
                money = float(money)
                #print gu, money
                if gu > 0 or money > 0:
                    date = df.iloc[i]['A股除权除息日']
                    if agl.is_valid_date(date):
                        df_fenhong = pd.concat([df_fenhong, pd.DataFrame([gu, money, date]).T])
            return df_fenhong	    
    def createThsOneCode(self, code, use_price_for_syl=False, price=0.0):
        d = self.getCodeDict(code)
        if use_price_for_syl:
            db = mysql.createStockDb()
            price = db.getCurrentPrice(code)
        return self.ThsOneCode(d, price)
    @staticmethod
    def TestMecchache():
        """测试失败， 同时网上有文章说不能超过1M"""
        from pymemcache.client import Client

        client = Client(('localhost', 11211))
        client.set('some_key', 'some_value')
        result = client.get('some_key')
        print(result)
    @staticmethod
    def Test_Bankuai_Zhishu():
        """由一个股票计算出其所属全部板块的指数, 并显示当前板块涨幅分布"""
        #个股与板块相关性beta的判断,  下面是两个个股的相关性排序，从结果看基本准确
        codes = ['002236', '600048']
        codes = get_codes(myenum.randn, 2)
        codes = ['603357']
        date  = '2014-4-1'
        end_day = getKlineLastDay()
        p = createThs()
        for code in codes:
            beta, bankuai,df = \
                p.analyze_bankuai_beta(code, start_day=date, \
                                       end_day=end_day, is_report=True)
    @staticmethod
    def Test2():
        """测试单个股票的每股收益获取， 即市盈率计算"""
        code = '002346'
        def ReadPart():
            p = StockInfoThs()
            return p.getCodeDict( '002346')
        d = agl.SerialMgr.serialAuto(ReadPart)
        print( d)
        d = StockInfoThs.ThsOneCode(d)
        print( d.get_mgsy(), d.get_zgb(), SYL(getHisdatDf(code)['c'][-1], d.get_mgsy()))
def getHisdatDf(code, start_day='',end_day='',is_fuquan=False ):
    """从数据库获取日线, 复权 return: df"""
    df = mysql.getHisdat(code, start_day, end_day)
    one = createThs().createThsOneCode(code)
    df_fenhong = one.get_fenhong()
    df = calc_fuquan_use_fenhong(df, df_fenhong)    
    return df
def getFiveHisdatDf(code, start_day='', end_day=''):
    """return: df col('ohlcu')"""
    return mysql.getFiveHisdat(code,start_day,end_day)
def IsShangHai(code):
    """判断股票代码属于那个市场
    code: 个股代码"""
    if code[0] == '6' and code[1] == '0':
        return 1
    return 0
def GetCodeName(code):
    """从redis中取出名称 return: str"""
    if code=='510050':
        return '50ETF'
    key = myredis.enum.KEY_CODENAME
    if key not in myredis.getKeys():
        df = StockInfoThs.genCodeNameTbl()
        myredis.set_obj(key, df)
    else:
        df = myredis.get_obj(key)
    assert(len(df)>0)
    assert(df is not None)
    try:
        return df[df['code'] == code]['name'].tolist()[0]
    except:
        return '新股'
def load_ths_custom_codes():
    '先用ths导出自选股到桌面 获取自选股列表 return: list'
    fname = 'C:/Users/Administrator/Desktop/table.txt'
    codes = []
    if os.path.isfile(fname):
        f = open(fname, 'r')
        for l in f.readlines():
            if l[:2] == 'SH' or l[:2] == 'SZ':
                code = l[2:8]
                if code != '510050':
                    codes.append(code)
        f.close()	
    return codes
def getTHS_custom_codes():
    s = '510050'
    for code in load_ths_custom_codes():
        s += '|'
        s += code
    return s
    
########################################################################
class Hisdat:
    """"""

    high = ''
    low = ''
    close = ''
    open = ''
    volume=''
    #datetime.date
    date= ''

    #----------------------------------------------------------------------
    def __init__(self, ary):
        """Constructor"""
        self.date = ary[2]
        self.open = ary[3]
        self.high = ary[4]
        self.low = ary[5]
        self.close = ary[6]
        self.volume = ary[7]

    def getHigh(self):        
        return self.high

    #    
    #

    #----------------------------------------------------------------------
    def __eq__(self, other):
        """"""
        if 0: other = Hisdat
        return self.date == other.date and self.high == other.high and self.low == other.low \
               and self.close == other.close and self.volume == other.volume \
               and self.open == other.open

    def ToMat(self):
        return [self.date, self.open, self.high, self.low, self.close, self.volume]
    #----------------------------------------------------------------------
    def myprint(self):
        """"""
        help.myprint(self.date, self.open, self.high, self.low, self.close, self.volume)	
        #print "["+str(self.date)+" "+str(self.open)+" "+str(self.high)+" "+str(self.low)+" "+str(self.close)+" "+str(self.volume)+"]" 


########################################################################
class Kline:
    """"""
    hisdats=[]
    code =''
    class enum:
        period_day = 4
        period_30 = 2
        period_1 = 1	    #一分钟
        period_month = 8    #月线
    #----------------------------------------------------------------------
    def __init__(self, code, start_day='', end_day='', period_type=4):
        """Constructor"""
        self.code = code
        self.hisdats = []
        self.period = period_type
        if code == '':
            return
        #db = mysql.StockMysql()
        db = mysql.createStockDb()
        if period_type == 4 or period_type==1 or period_type == self.enum.period_month:
            hisdats = db.getKline(code, start_day, end_day)
        if period_type == 2:
            hisdats = db.getKline30(code, start_day, end_day)
        #hisdats = db.getFuQuanKline(code, start_day, end_day)


        assert(len(self.hisdats) == 0)
        for row in hisdats :
            self.hisdats.append(Hisdat(row))


    if 0: getData = Hisdat
    def getData(self,index):
        return self.hisdats[index]

    if 0: getLastData = Hisdat
    def getLastData(self):
        index = self.getSize() - 1
        return self.getData(index)


    def getSize(self):
        return len(self.hisdats)


    #
    #----------------------------------------------------------------------
    def resizeIndex(self, start_index=0, end_index=-1):
        """"""
        if end_index == -1:
            end_index = self.getSize()
        # 结尾其自己会加1 [0:size]
        self.hisdats = self.hisdats[start_index: end_index]

    #----------------------------------------------------------------------
    if 0: resizeIndexToGuider = Guider
    def resizeIndexToGuider(self, start_index=0, end_index=-1):
        """"""
        new_guider = copy.deepcopy(self)
        new_guider.resizeIndex(start_index, end_index)
        return new_guider

    #----------------------------------------------------------------------
    if 0: resizeToGuider = Guider
    def resizeToGuider(self, date):
        """"""
        new_guider = copy.deepcopy(self)
        new_guider.resize(date)
        return new_guider


    #----------------------------------------------------------------------
    def resize(self, date):
        """调整数组长度"""
        assert(isinstance(date, str) or isinstance(date, datetime.date))
        index = self.DateToIndex(date)
        if index >= 0:
            self.hisdats = self.hisdats[:index+1]

    #----------------------------------------------------------------------
    def DateToIndex(self, date):
        """"""
        assert(isinstance(date, datetime.date))
        for i in range(0, self.getSize()):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            assert(isinstance(hisdat.date, datetime.date))
            if date == hisdat.date:
                return i
            if date < hisdat.date:
                return -1
        return -1

    #
    #获取收盘价集合
    #----------------------------------------------------------------------
    def getCloses(self):
        """"""
        y = []
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            if isinstance(hisdat,np.ndarray):
                y.append(hisdat[-1])
            else:
                y.append(hisdat.close)
        return np.array(y)

    def getVolumes(self):
        """"""
        y = []
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            y.append(hisdat.volume)
        return np.array(y)
    #
    #----------------------------------------------------------------------
    def getHighs(self):
        """"""
        y = []
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            y.append(hisdat.high)
        return np.array(y)

    #----------------------------------------------------------------------
    def getLows(self):
        """"""
        y = []
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            y.append(hisdat.low)
        return np.array(y)

    #----------------------------------------------------------------------
    def getFenshiCloses(self):
        """得到分时的价格集合"""
        #
        closes = []
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            cur_fenshi = Fenshi(self.code, hisdat.date)
            cur_fenshi.mean()
            for order in cur_fenshi.orders:
                if 0: order = Order
                closes.append(order.GetPrice())
        return closes


    #----------------------------------------------------------------------
    def getYestodayClose(self, index):
        """"""
        #assert(index>0)
        if index == 0:
            return 0
        return self.hisdats[index-1].close

    #
    if 0: getDataFromDate = Hisdat
    def getDataFromDate(self, date):
        for hisdat in self.hisdats:
            if hisdat.date == date:
                return hisdat
        return 0

    def getClose(self, date):
        """根据日期取close"""
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            if hisdat.date == date:
                return hisdat.close
        return 0

    ####################
    @staticmethod
    def getCodes():
        """获取全部股票代码， 包括板块的， 从cache文件中获取"""
        fname = "datas/tdx_codes.csv"
        return np.loadtxt(fname,delimiter='\n', dtype=str)
    # 技术指标
    #----------------------------------------------------------------------
    def MA(self):
        """"""
        closes = self.getCloses()
        return talib.MA(closes)

    #
    #----------------------------------------------------------------------
    def RSI(self):
        """相对强弱指标， 30以下超卖， 70以上超买"""
        closes = self.getCloses()
        return talib.RSI(closes)

    def WILLR(self):
        """与KDJ相反, 0到-20超买， 80到-100超卖"""
        closes = self.getCloses()
        highs = self.getHighs()
        lows = self.getLows()
        return talib.WILLR(highs,lows,closes)

    #----------------------------------------------------------------------
    def OBV(self):
        """能量潮, 分析成交量变化的趋势"""
        volumes = self.getVolumes()
        closes = self.getCloses()
        return talib.OBV(closes, volumes)

    #----------------------------------------------------------------------
    def MACD(self):
        """通过快慢均线交叉来判断交易信号
        MACD: (12-day EMA - 26-day EMA)	    慢线， 黑色
        Signal Line: 9-day EMA of MACD	    快线, 红色
        MACD Histogram: MACD - Signal Line  直方图, 柱状图
        return : macd, macdsignal, macdhist(柱状)"""
        closes = self.getCloses()
        return talib.MACD(closes)
    def BOLL(self):
        """BOLL"""
        return talib
    ##########################

    #
    @staticmethod
    def FromFile():
        #a = []
        ##return np.fromfile("alldata.mat")
        fname = "alldata.txt"
        #if os.path.isfile(f_name):
            #f = open(f_name)
            #a = pickle.load(f)
            #f.close()
        #return np.array(a)
        return np.loadtxt(fname,delimiter=',')

    @staticmethod
    def getAllKlineDf():
        """把所有codes日线读成df"""
        def genAllDf():
            codes = simulator.ISimulator.getGupiaos(myenum.all)
            df = pd.DataFrame()
            for code in codes:
                df2 = Guider(code).ToDataFrame()
                df2['code'] = code
                df = pd.concat([df, df2])
            return df
        return agl.SerialMgr.serialAuto(genAllDf)	
    #----------------------------------------------------------------------
    @staticmethod
    def DumpToFile():
        """把所有收盘记录复制到矩阵中, 然后存盘
        记录顺序是
        [
        [open,
         high,
         low,
         close, 
         vol,
         ...
        ]
        ...
        ]
        """
        date_win = ["2014-1-1","2014-8-18"]
        date = help.MyDate(date_win[0])
        codes = simulator.ISimulator.getGupiaos(enum.all)
        #codes = simulator.ISimulator.getGupiaos(enum.rand10)
        datas = np.zeros((len(codes)*5, (help.MyDate(date_win[1]).d-date.d).days))	
        for i, code in enumerate(codes):
            print( code)
            guider = Guider(code, period_type=Kline.enum.period_day)
            j = 0
            date = help.MyDate(date_win[0])
            while date.d < help.MyDate(date_win[1]).d:
                date.Next()
                #print date.echo()
                hisdat = guider.getDataFromDate(date.d)
                if not isinstance(hisdat, Hisdat) :
                    datas[i*5:i*5+5, j] = 0
                else:
                    #有些成交量字段没有存储上， 因此做一下修复
                    if hisdat.close>0 and hisdat.volume<0.1:
                        hisdat.volume = 10000
                    #取列里的值后也转化成行输出， 因此用行值赋值
                    datas[i*5:i*5+5, j] = np.array([hisdat.open,hisdat.high,hisdat.low,hisdat.close,hisdat.volume])
                j += 1

        #输出到文件
        #if 0: datas = np.array()
        #print np.shape(datas)
        #datas2.tofile("alldata.mat")
        f_name = "alldata.txt"	
        #f = open(f_name,"w")
        #pickle.dump(datas, f)
        #f.close()
        np.savetxt(f_name, datas, delimiter=',', fmt='%.3f')

        #附带输出一个到csv
        fname = "C:\\chromium\\src\\autoxd3\\third_party\\armadillo\\examples\\alldata.csv"
        fname = "..\\alldata.csv"
        agl.MatrixToCsv(datas, fname)

    @staticmethod
    def Dump30ToFile():
        """30分钟线, 因为np需要对齐, 因此不对齐的用0填充在尾部, 数据结构同日线"""
        date_win = ["2014-4-1","2014-6-18"]
        date = help.MyDate(date_win[0])
        codes = simulator.ISimulator.getGupiaos(enum.all)
        datas = []
        m=0; n=0
        for i, code in enumerate(codes):
            print( code)
            guider = Guider(code, period_type=Kline.enum.period_30)
            if guider.getSize()>0:
                mat = np.array(guider.DataToMat()	)
                mat = np.array(mat[:, 1:], dtype=float)
                if guider.getSize()>m:
                    m = guider.getSize()
                datas.append(mat)
        n = len(datas)*5
        mat_datas = np.zeros((n, m))
        for i in range(len(datas)):
            datas[i] = datas[i].T
            for j in range(5):
                cur_row = datas[i][j]
                mat_datas[i*5+j][:len(cur_row)] = cur_row

        #输出到文件
        f_name = "alldata.txt"	
        np.savetxt(f_name, mat_datas, delimiter=',', fmt='%.3f')

    @staticmethod
    def Dump1ToFile():
        """1分钟线, 因为np需要对齐, 因此不对齐的用0填充在尾部, 数据结构同日线"""
        date_win = ["2014-1-1","2014-6-18"]
        date = help.MyDate(date_win[0])
        codes = simulator.ISimulator.getGupiaos(enum.all)
        datas = []
        m=0; n=0
        for i, code in enumerate(codes):
            print( code)
            guider = Guider(code,date_win[0],date_win[1], period_type=Kline.enum.period_1)
            if guider.getSize()>0:
                if len(guider.fenshi_hisdats)>m:
                    m = len(guider.fenshi_hisdats)
                datas.append(guider.fenshi_hisdats)
        n = len(datas)
        mat_datas = np.zeros((n, m))
        for i in range(len(datas)):
            cur_row = datas[i]
            mat_datas[i][:len(cur_row)] = cur_row

        #输出到文件
        f_name = "alldata.txt"	
        np.savetxt(f_name, mat_datas, delimiter=',', fmt='%.2f')	
    @staticmethod
    def getDayDatas(date_win, codes):
        date = help.MyDate(date_win[0])
        datas = np.zeros((len(codes)*5, (help.MyDate(date_win[1]).d-date.d).days))	
        for i, code in enumerate(codes):
            #print code
            guider = Guider(code)
            j = 0
            date = help.MyDate(date_win[0])
            while date.d < help.MyDate(date_win[1]).d:
                date.Next()
                #print date.echo()
                hisdat = guider.getDataFromDate(date.d)
                if not isinstance(hisdat, Hisdat) :
                    datas[i*5:i*5+5, j] = 0
                else:
                    #取列里的值后也转化成行输出， 因此用行值赋值
                    datas[i*5:i*5+5, j] = np.array([hisdat.open,hisdat.high,hisdat.low,hisdat.close,hisdat.volume])
                j += 1
        return datas
    @staticmethod
    def DumpFenshiToFile():
        """因为分时数据太大， 因此一次只导出小部分至文件中， 包含日线数据
        [
         [每天
          [每笔,...],
          [每笔....],
          ...
         ],
         ...
        ]"""
        date_win = ["2014-8-1","2014-11-21"]
        date = help.MyDate(date_win[0])
        #codes = simulator.ISimulator.getGupiaos(enum.rand100)
        codes = simulator.ISimulator.getGupiaos(enum.all)
        #codes = ["600519"]
        datas = np.zeros((len(codes)*5, (help.MyDate(date_win[1]).d-date.d).days))	
        fenshis = []
        for i, code in enumerate(codes):
            print( code)
            guider = Guider(code)
            j = 0
            date = help.MyDate(date_win[0])
            fenshi_days = []
            while date.d < help.MyDate(date_win[1]).d:
                date.Next()
                #print date.echo()
                hisdat = guider.getDataFromDate(date.d)
                if not isinstance(hisdat, Hisdat) :
                    datas[i*5:i*5+5, j] = 0
                else:
                    #取列里的值后也转化成行输出， 因此用行值赋值
                    datas[i*5:i*5+5, j] = np.array([hisdat.open,hisdat.high,hisdat.low,hisdat.close,hisdat.volume])
                fenshi = Fenshi(code, date.echo())  #每天
                fenshi.mean()
                v = fenshi.ToMatrix()
                if len(v)>0:
                    fenshi_days.append(v)
                j += 1	
            fenshis.append(fenshi_days)	#每个股票

        agl.SerialMgr.serial((datas,fenshis), "fenshi.txt")

    @staticmethod
    def getSerialCloses(hisdats):
        """矩阵中的5排,
        return:去除0后的5个数组"""
        if isinstance(hisdats[-1], np.float16) and hisdats[-1]==0:	#对应1分钟分时dump的情况
            return 0,0,0,hisdats[np.nonzero(hisdats)],0
        opens, highs, lows, closes, volumes = hisdats
        #如果成交量与closes未对齐，那么需要先对齐
        opens = opens[np.nonzero(opens)]
        highs = highs[np.nonzero(highs)]
        lows  = lows[np.nonzero(lows)]
        closes = closes[np.nonzero(closes)]
        volumes = volumes[np.nonzero(volumes)]
        #assert(len(closes) == len(volumes))
        return opens,highs,lows,closes,volumes


    #----------------------------------------------------------------------
    def myprint(self):
        """"""
        for hisdat in self.hisdats:
            if 0: hisdat = Hisdat
            hisdat.myprint()

class AllDatas:
    """帮助处理全数据矩阵"""
    def __init__(self):
        self.datas = Kline.FromFile()
        self.is_fenshi = False
        if isinstance(self.datas[0][-1], np.float16) and self.datas[0,-1]==0:
            self.is_fenshi = True
    def get(self, index):
        """return: hisdats"""
        if self.is_fenshi:
            return self.datas[index]
        return self.datas[index*5:(index+1)*5]
    def getcloses(self, index):
        opens, highs, lows, closes, volumes = Kline.getSerialCloses(self.get(index))
        return closes
    def getSize(self):
        return len(self.datas)/5
    def RunOne(self, func, index):
        return func(self.get(index), index)
    def RunOneCloses(self, func, index):
        return func(self.getcloses(index))
    def RunOneAtLineByLine(self, func, index):
        last_sh = np.nan
        hisdat = self.get(index)
        for i in range(200, len(hisdat[0])):
            last_sh = func(hisdat[:,:i])
        return last_sh
    def RunOneAtLineByLineCloses(self, func, index):
        r = []
        closes = self.getcloses(index)
        for i in range(200, len(closes)):
            r.append(func(closes[:i], closes))
        return np.array(r)
    def Travl(self, func):
        """遍历，func: fn(hisdats)"""
        for i in range(0, len(self.datas)/5):
            func(self.get(i), i)
    def TravlClose(self, func):
        """func: fn(closes)"""
        for i in xrange(0, len(self.datas)/5):
            closes = self.getcloses(i)
            func(closes)
    def TravlCloseHaveIndex(self, func):
        """func: fn(closes, index)"""
        for i in xrange(0, len(self.datas)/5):
            closes = self.getcloses(i)
            func(closes, i)    
def TestAllDatas(func):
    AllDatas().Travl(func)

class DumpOne:
    """仅仅dump一个closes"""
    def Save(self):
        closes = AllDatas().getcloses(20)
        np.savetxt("one.txt", closes, delimiter=',', fmt='%.3f')
    def Load(self):
        f_name = "one.txt"
        if not os.path.isfile(f_name):
            self.Save()	
        return np.loadtxt("one.txt", delimiter=',')
#
class FenshiEx:
    """获取连续的分时, 管理pd"""
    def __init__(self, code, start_day='', end_day='', is_fuquan=False):
        self.is_fuquan = is_fuquan
        if isinstance(code, pd.DataFrame):
            self.df = code
            return
        self.df = CreateFenshiPd(code,start_day,end_day)
        if self.is_fuquan and len(self.df) > 0:
            closes = self.df['p']
            #closes = closes[np.isnan(closes) == False]
            #取日线的除权信息
            df_hisdat = mysql.getHisdat(code, start_day, end_day)
            closes = FuQuan_Fenshi(closes, df_hisdat)
            self.df['p'] = closes
    def Resample(self, resample='T'):
        """时间规整, 
        resample: T 每分钟 D 每天"""
        self.df = self.df.resample(resample, how='mean')
    def getCloses(self):
        a = np.array(self.df['p'])
        a = a[np.isnan(a) == False] / 100.0
        return a
    def getVolumes(self):
        a = np.array(self.df['v'])
        a = a[np.isnan(a) == False]
        return a
    def get_closes(self, day='', resample=''):
        """day: 取某一天的值，为空则取全部日期
        return: np.array closes 已复权"""
        if day != '':
            df = self.df[day]
        else:
            df = self.df
        if resample != '':
            a = df.resample(resample, how='mean')['p']
        else:
            a = df['p']
        closes = np.array(a)
        if not self.is_fuquan:
            closes = closes[np.isnan(closes) == False]
            FuQuan(closes)
        return closes	
    #再实现一次前复权， 1.找到两个价格（两天）之间的涨幅 ，
    #2如果涨幅大于10%， 那么对前面所有的值进行复权
    #3遍历这个过程直到结束
    def _fuquan(self):
        pass
    @staticmethod
    def Test():
        #杰瑞股份在此期间的三次复权, 从结果看，基本上是对的
        code = '002353'
        fenshi = FenshiEx(code, '2012-3-1','2014-7-1',is_fuquan=True)
        closes = fenshi.get_closes()
        print( min(closes))
        fenshi.df.resample('D', how='mean')['p'].plot()
        pl.show()
        closes_hisdat = Guider(code, '2012-3-1','2014-7-1').getCloses()
        print( min(closes_hisdat))

    @staticmethod 
    def to_csv(code):
        fenshi = FenshiEx(code)
        df = fenshi.df.resample('T', how='mean')
        df = df[np.isnan(df['p']) == False]
        path = "C:\\chromium\\src\\autoxd3\\matlab_src\\Automated_Trading\\%sfenshi.csv"%code 
        df['p'] = FuQuan(df['p'])
        df = np.array(df['p'])
        fname = path
        np.savetxt(fname, df)
def CreateFenshiPd(code, start_day='', end_day=''):
    """return: df columns=pvb p为真实价格"""
    db = mysql.createStockDb()
    df_hisdat = getHisdatDataFrameFromRedis(code, start_day, end_day)
    datas = []
    df_total = pd.DataFrame([])
    for i in range(len(df_hisdat)):
        cur_day = str(df_hisdat.index[i]).split(' ')[0]
        fenshis = db.getFenshi(code, cur_day)
        if len(fenshis) == 0:
            continue
        df = pd.DataFrame(fenshis)
        df = df[df[0]<901]  #过滤掉错误的数据
        n = 100.0
        if code=='510050':
            n = 1000.0
        df[1] = df[1]/n
        df[0] = df[0].map(lambda x: dateutil.parser.parse(cur_day+' %s:%s:0'%StockTime.ToTime(x)))
        df.index = pd.DatetimeIndex(df[0])
        df = df.drop([0,3], axis=1)
        df_total = pd.concat([df_total, df])
    if len(df_total)>0:
        df_total.columns = list('pvb')
    return df_total
def unittestCreatePd():
    a = agl.tic_toc()
    code ,day= "600779", '2014-9-12'
    print( CreateFenshiPd(code, day, day))

def FuQuan(closes):
    """对一个时间序列进行复权, 该版本对于处理fenshi等大数据速度很慢"""
    def GetZhangFu(price1, price2):
        return (price2 - price1) / price1
    def calcFuQuan(closes):
        """"""
        b = False
        while 1:
            for i in range(1,len(closes)):
                price1 = closes[i-1]
                price2 = closes[i]
                if IsChuQuan(price1, price2) :
                    zhangfu = GetZhangFu(price1, price2)
                    for j in range(i):
                        closes[j] = fuquan(closes[j], zhangfu)
                    b = True
                    print('find fuquan')
                    break
                if i == len(closes)-1:
                    b = False
            if not b:
                break

        return closes
    def fuquan(price, chuquan_zhangfu):
        """"""
        return calc_fuquan_price(price, chuquan_zhangfu)
    def calc_fuquan_price(price, chuquan_zhangfu):
        return float(str("%.2f"% (price * ( 1+ chuquan_zhangfu)) ) )
    def IsChuQuan(price1, price2):
        """"""
        zhangfu = GetZhangFu(price1, price2)
        return zhangfu < -0.1    
    return calcFuQuan(closes)
def FuQuan_Fenshi(df_fenshi, df_hisdat):
    """用矩阵计算对一个时间序列进行复权
    1. 先通过日线来获取除权信息， 比如那一天除了权， 修复的涨幅是多少
    2. 更新复权日期列表来对分时进行等比率复权
    df_fenshi: 日期索引的分时
    return:  df_fenshi"""
    def getChuQuanList(df_hisdat):
        """获取除权日期及除权涨幅
        return: df 在hlocv后加上z涨幅， 索引是日期"""
        #注意， df矩阵运算会与索引对其
        df_open = df_hisdat['o'][1:]
        zhang_fu = np.array(df_open)/np.array(df_hisdat['c'][:-1]) - 1
        zhang_fu = agl.array_insert(zhang_fu, 0, 0)
        df_result = df_hisdat[zhang_fu < -0.11]
        zhang_fu = zhang_fu[zhang_fu < -0.11]
        df_result.is_copy = False
        df_result['z'] = zhang_fu
        return df_result    
    df_fuquan = getChuQuanList(df_hisdat)
    for i in range(len(df_fuquan)-1, -1, -1):
        day = str(df_fuquan.index[i])
        day = str.split(day, " ")[0]
        day = help.MyDate(day)
        day.Add(-1)
        day = day.ToStr()
        z = df_fuquan.ix[i]['z']
        #关闭警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")	
            df_fenshi[:day] = df_fenshi[:day] *(1+z)
    return df_fenshi
########################################################################
class Guider(Kline):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, code, start_day='', end_day='', period_type=4):
        """Constructor"""
        Kline.__init__(self, code, start_day, end_day, period_type)
        self.calcFuQuan()
        if period_type == self.enum.period_1:
            #新增了一个分时成员变量，基本不会用这种形式了， 直接使用fenshiex类
            hisdats = []
            #读数据
            for i in range(0, self.getSize()):
                cur_day = self.getData(i).date
                fenshi = Fenshi(self.code, cur_day)
                fenshi.mean()
                for order in fenshi.orders:
                    if 0: order = Order
                    price = order.GetPrice()
                    hour , minute = StockTime.ToTime(order.date)
                    d = datetime.datetime(cur_day.year, cur_day.month, cur_day.day, hour, minute, 0)
                    hisdats.append(Hisdat([0,0,d,price,price,price,price,100]))	
            #对分时数据进行复权
            self.fenshi_hisdats = hisdats
            self.fenshiFuQuan()
            prices = []
            for i in range(len(self.fenshi_hisdats)):
                prices.append(self.fenshi_hisdats[i].open)
            self.fenshi_hisdats = np.array(prices)
        if period_type == self.enum.period_month and len(self.hisdats)>0:
            #把日线数据转换为月线
            month =  help.MyDate(self.hisdats[0].date).d.month
            hisdats = []
            month_hisdats = []
            for h in self.hisdats:
                if 0: h = Hisdat(ary)
                cur_month = help.MyDate(h.date).d.month
                if month != cur_month:
                    month = cur_month
                    if len(month_hisdats) > 0:
                        month_hisdats = np.array(month_hisdats)
                        hisdat = [month_hisdats[0,1], np.max(month_hisdats[:,2]), 
                                  np.min(month_hisdats[:,3]), month_hisdats[-1, 4]]
                        hisdats.append(hisdat)
                        month_hisdats = []
                if month == cur_month:
                    month_hisdats.append(h.ToMat())
            self.hisdats = np.array(hisdats)
    def fenshiFuQuan(self):
        for i in range(len(self.fenshi_hisdats)-2, 0, -1):
            hisdat1 = self.fenshi_hisdats[i]
            hisdat2 = self.fenshi_hisdats[i+1]

            if self.IsChuQuan(hisdat1, hisdat2) :
                zhangfu = self.GetZhangFu(hisdat1, hisdat2)
                for j in range(i, -1, -1):
                    self.fuquan(self.fenshi_hisdats[j], zhangfu)	
    ######fuquan start
    #----------------------------------------------------------------------
    def calcFuQuan(self):
        """"""
        for i in range(self.getSize()-2, 0, -1):
            hisdat1 = self.getData(i)
            hisdat2 = self.getData(i+1)

            if self.IsChuQuan(hisdat1, hisdat2) :
                zhangfu = self.GetZhangFu(hisdat1, hisdat2)
                for j in range(i, -1, -1):
                    self.fuquan(self.hisdats[j], zhangfu)



    #----------------------------------------------------------------------
    def fuquan(self, hisdat, chuquan_zhangfu):
        """"""
        if 0 : hisdat = Hisdat()
        hisdat.open = self.calc_fuquan_price(hisdat.open, chuquan_zhangfu)
        hisdat.close = self.calc_fuquan_price(hisdat.close, chuquan_zhangfu)
        hisdat.high = self.calc_fuquan_price(hisdat.high, chuquan_zhangfu)
        hisdat.low = self.calc_fuquan_price(hisdat.low, chuquan_zhangfu)
        return hisdat



    #----------------------------------------------------------------------
    def calc_fuquan_price(self, price, chuquan_zhangfu):
        """"""
        return float(str("%.2f"% (price * ( 1+ chuquan_zhangfu)) ) )

    #----------------------------------------------------------------------
    def IsChuQuan(self, hisdat1, hisdat2):
        """"""
        zhangfu = self.GetZhangFu(hisdat1, hisdat2)
        return zhangfu < -0.10

    ######fuquan end	

    #
    #----------------------------------------------------------------------
    def DataToOneCsv(self):
        """"""
        all_the_text = ""
        for i in range(0, self.getSize()):

            all_the_text += str(self.getData(i).close)
            all_the_text += ", "

        file_object = open('c:\\matlab_source\\AlgoTrading2010\\'+self.code+'.csv', 'w')
        file_object.write(all_the_text)
        file_object.close( )         


    #----------------------------------------------------------------------
    def DataToCsv(self):
        """把股票数据导出到csv中"""

        all_the_text = "Date,Open,High,Low,Close,Volume"
        all_the_text = ""

        #读数据
        for i in range(0, self.getSize()):

            all_the_text += str(help.DateToInt(self.getData(i).date))
            all_the_text += ", "
            all_the_text += str(self.getData(i).open)
            all_the_text += ", "
            all_the_text += str(self.getData(i).high)
            all_the_text += ", "
            all_the_text += str(self.getData(i).low)
            all_the_text += ", "
            all_the_text += str(self.getData(i).close)
            all_the_text += ", "
            all_the_text += str(self.getData(i).volume)
            #all_the_text += ","
            all_the_text += "\n"

        file_object = open('c:\\matlab_source\\AlgoTrading2010\\'+self.code+'.csv', 'w')
        file_object.write(all_the_text)
        file_object.close( )         

    #
    #----------------------------------------------------------------------
    def __DataToR(self):
        """"""
        s = ""
        closes = self.getCloses()
        m, n = max(closes), min(closes)
        def autoScale(v, m, n):
            v = (v-n)/(m-n)
            return v
        for h in self.hisdats:
            if 0: h = Hisdat
            s += str(autoScale(h.close,m,n))
            s += " "
        s += "\n"
        return s

    @staticmethod
    def DataToR():
        codes = simulator.ISimulator.getGupiaos(enum.all)
        s = ""
        i = 0
        l = []
        for code in codes:
            g = Guider(code, start_day='2012-3-1', end_day='2012-11-1')
            print(g.code, g.getSize())
            l.append(g.getSize())
            if g.getSize() > 100:
                g.hisdats = g.hisdats[-100:]
            if g.getSize() == 100:
                s += g.__DataToR()
            i += 1
            #if i == 600:
                #break

        #print max(l), min(l)
        f = open('C:\\chromium\\src\\autoxd3\\R\\stocka.txt','w')
        f.write(s)
        f.close()

    @staticmethod
    def getDf(codes, dates):
        df = pd.DataFrame([])
        d1,d2 = dates
        for code in codes:
            df2 = Guider(code,d1,d2).ToDataFrame()
            df2['code'] = code
            df = pd.concat([df, df2])
        return df
    def DataToMat(self):
        r = []
        for h in self.hisdats:
            if 0 : h = Hisdat(ary)
            r.append(h.ToMat())
        return r
    #----------------------------------------------------------------------
    def FenshiDataToCsv(self):
        """"""
        all_the_text = "Date,Open,High,Low,Close,Volume"
        all_the_text = ""

        #读数据
        for i in range(0, self.getSize()):

            fenshi = Fenshi(self.code, self.getData(i).date)
            fenshi.mean()
            for order in fenshi.orders:
                if 0: order = Order
                all_the_text += str(order.num)
                all_the_text += ","
                all_the_text += str(order.GetPrice())
                all_the_text += ","
                all_the_text += str(order.GetPrice())
                all_the_text += ","
                all_the_text += str(order.GetPrice())
                all_the_text += "\n"

        file_object = open('../matlab_src/Automated_Trading/'+self.code+'fenshi.csv', 'w')
        file_object.write(all_the_text)
        file_object.close( )      	

    #----------------------------------------------------------------------
    def GetZhangFu(self, hisdat1, hisdat2):
        """"""
        if 0 : hisdat1 = Hisdat()
        if 0 : hisdat2 = Hisdat
        return (hisdat2.open - hisdat1.close) / hisdat1.close

    #
    #----------------------------------------------------------------------
    def ZhangFu(self, index):
        """"""
        if 0 : hisdat1 = Hisdat
        if 0 : hisdat2 = Hisdat
        if index == 0:
            return 0
        if len(self.hisdats) == 1:
            return (self.hisdats[0].close - self.hisdats[0].open) / self.hisdats[0].open
        hisdat1 = self.hisdats[index-1]
        hisdat2 = self.hisdats[index]
        return (hisdat2.close - hisdat1.close) / hisdat1.close

    #
    #----------------------------------------------------------------------
    def HighZhangFu(self, index):
        """"""
        if 0 : hisdat1 = Hisdat
        if 0 : hisdat2 = Hisdat
        if index == 0:
            return 0
        hisdat1 = self.hisdats[index-1]
        hisdat2 = self.hisdats[index]
        return (hisdat2.high - hisdat1.close) / hisdat1.close



    #----------------------------------------------------------------------
    def Wave_Uptrend(self):
        """计算k线的趋势点"""
        return 0


    #	
    #----------------------------------------------------------------------
    def GetHHV(self, type="close"):
        """"""
        a=[]
        for i in range(0, self.getSize()):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            cur = 0
            if type == "close":
                cur = hisdat.close
            if type == "high":
                cur = hisdat.high
            if type == "low":
                cur = hisdat.low
            if type == "open":
                cur = hisdat.open
            if type == "vol" or type == "volume" :
                cur = hisdat.volume
            a.append(cur)
        return max(a)

    def GetLLV(self, type="close"):
        """"""
        a=[]
        for i in range(0, self.getSize()):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            cur = 0
            if type == "close":
                cur = hisdat.close
            if type == "high":
                cur = hisdat.high
            if type == "low":
                cur = hisdat.low
            if type == "open":
                cur = hisdat.open
            if type == "vol" or type == "volume" :
                cur = hisdat.volume
            a.append(cur)
        return min(a)

    #----------------------------------------------------------------------
    def HHV(self, type="close", index = 0, day=60):
        """
        index : 当前下标
        """
        day = max(0, index - day+1)
        high = 0
        for i in range(day, index+1, 1):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            cur = 0
            if type == "close":
                cur = hisdat.close
            if type == "high":
                cur = hisdat.high
            if type == "low":
                cur = hisdat.low
            if type == "open":
                cur = hisdat.open
            if type == "vol" or type == "volume" :
                cur = hisdat.volume

            high = max(high, cur)

        return high

    #----------------------------------------------------------------------
    def LLV(self, type="close", index=0, day=60):
        """"""
        day = max(0, index - day+1)
        high = 0
        for i in range(day, index+1, 1):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            cur = 0
            if type == "close":
                cur = hisdat.close
            if type == "high":
                cur = hisdat.high
            if type == "low":
                cur = hisdat.low
            if type == "open":
                cur = hisdat.open
            if type == "vol" or type == "volume" :
                cur = hisdat.volume

            high = min(high, cur)
            if high < 0.01:
                high = cur

        return high

    #
    #
    #----------------------------------------------------------------------
    if 0: getCustomHisdat = Hisdat
    def getCustomHisdat(self, index=-1, day=5):
        """
        重新计算周线
        index : [int]数组下标, 当前天
        day:	[int]日期长度
        return : [Hisdat]
        """
        if index == -1:
            index = self.getSize()-1

        assert(index >= 0 and index < self.getSize())
        assert (day < self.getSize())
        pre_index = index - day+1
        assert(pre_index >= 0 )

        open = self.getData(pre_index).open
        close = self.getData(index).close
        high = self.HHV(type="high", index=index, day=day)
        low = self.LLV(type="low", index=index, day=day)
        volume = 0
        for i in range(pre_index, index+1):
            volume += self.getData(i).volume
        date = self.getData(pre_index).date
        ary = ["","", date, open, high, low, close, volume]
        return Hisdat(ary)

    #
    #----------------------------------------------------------------------
    def getAvgs(self, type="close", day=60):
        """return ma array"""
        a = []
        for i in range(0, self.getSize()):
            if i <= day:
                a.append(0)
            else:
                avg = self.AVG(type, index=i, day=day)
                a.append(avg)
        return a


    #计算均值, index - 最后一个索引
    #----------------------------------------------------------------------
    def AVG(self, type="close", index=0, day=60):
        """"""
        day = max(0, index - day)
        high = 0
        num = 0
        for i in range(day, index+1, 1):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            cur = 0
            if type == "close":
                cur = hisdat.close
            if type == "high":
                cur = hisdat.high
            if type == "low":
                cur = hisdat.low
            if type == "open":
                cur = hisdat.open
            if type == "vol" or type == "volume" :
                cur = hisdat.volume

            high += cur
            num += 1


        return high / num

    @staticmethod
    def getFlatVolume(series_volumes):
        """计算处于一个低位的水平地量 return: float"""
        results = np.array(series_volumes)
        results_n = np.zeros((len(results),2))
        results_n[:,0] = 1
        results_n[:,1] = np.array(results)	
        #聚类成3份， 选取中间数量最大的作为平量
        k = KMeans(3)
        k.fit(results_n)
        df = pd.DataFrame(k.labels_)
        df_c = pd.DataFrame(k.cluster_centers_)
        v = []
        for i in range(3):
            v.append( df[df[0]==i].count()[0])
        df_c[2] = v
        return df_c.iloc[df_c[2].argmax()][1]


    #
    #区间振幅
    #----------------------------------------------------------------------
    def ZhengFu(self, index, day=30):
        """"""
        high = self.HHV("high", index, day)
        low = self.LLV("low", index, day)
        return low/high

    #----------------------------------------------------------------------
    def getZhengFu(self, index):
        """"""
        hisdat = self.getData(index)
        yestoday_close = self.getData(index-1).close
        return (hisdat.high - hisdat.low) / yestoday_close

    #底部
    #开盘价在60日振幅的10%之内
    #bilv跌幅比率， 20=》10， 跌幅50%
    #----------------------------------------------------------------------
    def IsDibu(self, index, day=60, bilv=0.2):
        """"""
        if 0: hisdat = Hisdat
        hisdat = self.hisdats[index]
        high = self.HHV("high", index, day)
        low = self.LLV("low", index, day)

        if high - low <= 0:
            return False
        v = (hisdat.open - low) / (high - low)
        #print v
        flag = v < bilv

        return flag
    #
    #顶部
    #----------------------------------------------------------------------
    def IsDingBu(self, index, day=60, bilv=0.8):
        """"""
        if 0: hisdat = Hisdat
        hisdat = self.hisdats[index]
        high = self.HHV("high", index, day)
        low = self.LLV("low", index, day)

        if low - high <= 0:
            return False
        v = (hisdat.open - low) / (high - low)
        #print v
        flag = v > bilv

        return flag


    #
    #乖离率
    #----------------------------------------------------------------------
    def bais(self, index=0, day=60):
        """"""
        if index < day:
            return 0
        avg = self.AVG(index=index, day = day)
        hisdat = self.hisdats[index]
        if 0: hisdat = Hisdat
        return hisdat.close / avg

    #----------------------------------------------------------------------
    def getBaiss(self, day=60):
        """"""
        y = []
        for i in range(0, self.getSize()):
            if 0: hisdat = Hisdat
            b = self.bais(index=i, day=day)
            y.append(b)
        return y

    #
    #----------------------------------------------------------------------
    def AdaptiveMovingAveragees(self, n):
        """Adaptive moving averages 考夫曼自适应均线
        n = day效率周期
        逐行
        考夫曼自适应均线系统【通达信版】
{N:5    30    20
K:1    10     8}

DIRECTION:=ABS(CLOSE-REF(CLOSE,N));
VOLATILITY:=SUM(ABS(CLOSE-REF(CLOSE,1)),N);
ER:=DIRECTION/VOLATILITY;
FSC:=2/(2+1);
SSC:=2/(30+1);
SC:=ER*(FSC-SSC)+SSC;
SCSQ:=SC*SC;
KMA:DMA(CLOSE,SCSQ),COLORBLUE,LINETHICK2;
THRESHOLD:=STD(KMA-REF(KMA,1),20)*K/10;
BUY:=KMA-LLV(KMA,4)>THRESHOLD;
SELL:=HHV(KMA,4)-KMA>THRESHOLD;
买入:IF(BUY=1 AND SELL=0,KMA,DRAWNULL),COLORRED,LINETHICK2;
观望:IF((BUY=0 AND SELL=0) OR (BUY=1 AND SELL=1),KMA,DRAWNULL),COLORBLUE,LINETHICK2;
卖出:IF(BUY=0 AND SELL=1,KMA,DRAWNULL),COLOR66BB99,LINETHICK2;
        """
        assert(self.getSize()-n-1 >= 0)
        #求当天
        dir = abs(self.getLastData().close - self.getData(self.getSize()-1-n).close)
        #计算n天的和
        sum = 0
        for i in range(self.getSize()-1-n, self.getSize()):
            sum += abs(self.getData(i).close-self.getData(i-1).close)
        E = dir/sum
        c = 2/31	#2/8	慢周期
        d = 2/3		#4/5	快周期
        d -= c
        f = 2		#指数
        v = c + d*E
        v *= v
        return v


    #----------------------------------------------------------------------
    def XiangDuiQuJian(self):
        """相对区间"""
        account = Account()
        for i in range(60, self.getSize(), 1):
            if 0: hisdat = Hisdat
            hisdat = self.getData(i)
            day = 60
            high = self.HHV("close", i, day)
            low = self.LLV("close", i, day)
            cur = hisdat.close
            v = (cur-low)/(high-low)
            if v > 0.9:
                account.sell(self.code, hisdat.close, -1, hisdat.date)
            if v < 0.1 :
                account.buy(self.code, hisdat.close, -1, hisdat.date)

            print(account.money)
        print(account.getMoney())
        self.myprint()
        account.printWeiTuo()
    def ToDataFrame(self):
        """return: df 日期为索引"""
        d = np.array(self.DataToMat())
        if len(d) == 0:
            return pd.DataFrame([])
        return pd.DataFrame(d[:,1:], index=pd.DatetimeIndex(d[:,0]), dtype=float, columns=list('ohlcv'))
    @staticmethod
    def DumpToRedis():
        """把数据放入redis， code为日线，分时会发生out of memory"""
        ths = createThs()
        codes = get_codes() 
        dapan_codes = {myenum.DaPan.shanghai:'上证指数', myenum.DaPan.shengzheng:'深成指数',
                       myenum.DaPan.zhongxiao:'中小板指', 
                       myenum.DaPan.chuangyeban:'创业板指', myenum.DaPan.etf:'50ETF'}
        for dapan_code in dapan_codes.keys():
            codes.append(dapan_code)
        for code in pyprind.prog_bar(codes, title='all codes kline dump'):
            df = mysql.getHisdat(code)
            #碰到新股没数据
            if len(df) == 0:
                continue
            one = ths.createThsOneCode(code)
            #复权计算
            df_fenhong = one.get_fenhong()
            df = calc_fuquan_use_fenhong(df, df_fenhong)
            myredis.set_obj(code, df)
            #记录代码名称供c查询
            try:
                if code in dapan_codes.keys():
                    name = dapan_codes[code]
                else:
                    name = one.get_name()
                key = code+'_name'
                myredis.set_str(key, name)
            except:
                continue
    @staticmethod
    def unittest():
        code = '002174'
        name = GetCodeName(code)
        guider = Guider(code, period_type=Guider.enum.period_1)
        print( name)
        df = guider.ToDataFrame()
        print( df.tail())
        #df.plot()
        df[3].plot()
        pl.show()
#
#现在分时和资金买卖单都在用这个类
########################################################################
class Order:
    """
    代码、日期、价格、数量、买卖标示
    """
    code = ''
    date = ''
    price = 0
    num = 0
    buy = True

    #----------------------------------------------------------------------
    def __init__(self, code, date, price, num, buy=True):
        """Constructor"""
        self.code = code
        self.date = date
        self.price = price
        self.num = num
        self.buy = buy


    #
    #----------------------------------------------------------------------
    def GetPrice(self):
        """"""
        return float(self.price)/100.0

    #----------------------------------------------------------------------
    def echo(self):
        """"""
        print( "[" + self.code + " " + str(self.date) + " " + str(self.price) + " " + str(self.num) + " " + str(self.buy) + "]")
    def ToStr(self):
        return "[" + self.code + " " + str(self.date) + " " + str(self.price) + " " + str(self.num) + " " + str(self.buy) + "]"
    #
    def ToList(self):
        return [self.code, str(self.date), self.price, self.num, int(self.buy)]
    #----------------------------------------------------------------------
    def myprint(self):
        """"""
        self.echo()

class DataSources:
    """生成数据面板, 面板数据选取的例子panel.ix[0].ix['2014-1-2']
    panel.ix[0, '2014']会失败"""
    @staticmethod
    def getHisdatPanl(codes, days):
        """k线的历史数据框面板
        codes: [list]
        days: [turple]
        return: [pandas.panel]"""
        def gen():
            start_day , end_day = days
            d = {}
            for code in codes:
                df = getHisdatDf(code, start_day, end_day)
                d[code] = df
            panel = pd.Panel(d)
            return panel
        panel = agl.SerialMgr.serialAuto(gen)
        if panel is None:
            panel = gen()
        return panel
    @staticmethod
    def getFenshiPanl(codes, days):
        """索引使用datetime, 如果是一天的，那么day1=day2
        return: dict"""
        def gen():
            start_day , end_day = days
            d = {}
            for code in codes:
                fenshi = FenshiEx(code, start_day, end_day, is_fuquan=True)
                if len(fenshi.df) == 0:
                    assert(False)
                fenshi.df = fenshi.df[fenshi.df['p']>0.01]
                d[code] = fenshi.df
            return d
        d = agl.SerialMgr.serialAuto(gen)
        if d is None:
            d = gen()
        return d
    @staticmethod
    def getFiveMinHisdatPanl(codes, days):
        """return: dict"""
        def gen():
            start_day , end_day = days
            d = {}
            for code in codes:
                df = mysql.getFiveHisdat(code, start_day, end_day)
                d[code] = df
            return d
        d = agl.SerialMgr.serialAuto(gen)
        if d is None:
            d = gen()
        return d
    @staticmethod
    def getCodes():
        """return: list"""
        def gen():
            return [u'300059',u'300229',u'600630',u'002466', u'300033']
        d = agl.SerialMgr.serialAuto(gen)
        if d is None:
            d = gen()
        return d
            
    @staticmethod   
    def Test():
        agl.tic()
        codes = DataSources.getCodes()
        days = ('2016-1-1', '2017-11-5')
        DataSources.getHisdatPanl(codes, days)
        print( DataSources.getHisdatPanl(codes, days).ix[codes[0]].head(2))
        days = ('2017-5-15', '2017-11-5')
        DataSources.getFiveMinHisdatPanl(codes, days)
        print(DataSources.getFiveMinHisdatPanl(codes, days)[codes[0]].head(2))
        days = ('2017-8-1', '2017-9-20')
        DataSources.getFenshiPanl(codes, days)
        print( DataSources.getFenshiPanl(codes, days)[codes[0]].head(2))
        agl.toc()

########################################	
class SplitAccount:
    def __init__(self, money):
        self.money = money
        self.stock_money = 0
    def buy(self, num, price):
        if self.money > num * price:
            self.stock_money += num*price
            self.money -= num*price
    def sell(self, num, price):
        if self.stock_money > num * price:
            self.stock_money -= num*price
            self.money += num * price
########################################################################

class Account:
    """本地账户, 保留该类为了兼容早期的策略"""
    money = 5000000
    weituo_historys = []		#委托记录
    orders = []				#当前仓储
    detailed_orders = []		#持仓明细单

    #----------------------------------------------------------------------
    def __init__(self, money = 50000):
        """Constructor"""
        self.money = money
        self.org_money = money
        self.weituo_historys = []
        self.orders = []
        self.total_moneys = []		#总资金列表
        self.total_moneys.append(self.money)
    def setMoney(self, money):
        self.money = money
    #
    #
    #----------------------------------------------------------------------
    if 0: getData = Order
    def getData(self, index):
        """"""
        assert(len(self.orders) > 0)
        assert (index >=0 and index < len(self.orders))
        return self.orders[index]

    #
    #----------------------------------------------------------------------
    if 0: getOrder = Order
    def getOrder(self, code):
        """"""
        index = self.findOrder(code)
        if index >=0:
            return self.getData(index)
        return None

    #----------------------------------------------------------------------
    def HaveStorge(self):
        """"""
        return len(self.orders) > 0

    #手续费
    #----------------------------------------------------------------------
    def sxf(self):
        """千分之1.6加印花税"""
        #新的修改为万3, 实测为千分之1.5
        return 0.0016
        #return 0.0045

    #总资产
    #----------------------------------------------------------------------
    def getMoney(self, df):
        """df: cols = code,price
        return: float 总资产"""
        money = self.money

        for code, price in df:
            money += self.getShiZhi(code,price)
        return money


    #	
    #市值
    #----------------------------------------------------------------------
    def getShiZhi(self, code, price):
        """"""
        money = 0
        for order in self.orders:
            money += order.num * price
            if code != '' and order.code == code:
                return order.num * price
        return 	money

    #----------------------------------------------------------------------
    def printWeiTuo(self):
        """"""
        for order in self.weituo_historys:
            if 0: order = Order
            order.echo()

    #	
    #得到上次交易的价格
    #----------------------------------------------------------------------
    if 0: getLastWeiTuo = Order
    def getLastWeiTuo(self, code):
        """"""
        if 0: order = Order
        size = len(self.weituo_historys)
        for i in range(size-1, -1, -1):
            if self.weituo_historys[i].code == code:
                return self.weituo_historys[i]
        #if size > 0:
            #order = self.weituo_historys[size-1]
            #return order
        return Order(code, '', 0, 0, 0)

    #
    #获取最后一个买入价格
    #----------------------------------------------------------------------
    def getLastWeiTuoBuy(self, code):
        """"""
        if 0: order = Order
        size = len(self.weituo_historys)
        for i in range(size-1, -1, -1):
            order = self.weituo_historys[i]
            if order.buy == True and order.code == code:
                return order.price
        return 0

    def getLastWeiTuoSell(self, code):
        """"""
        if 0: order = Order
        size = len(self.weituo_historys)
        for i in range(size-1, -1, -1):
            order = self.weituo_historys[i]
            if order.buy == False and order.code == code:
                return order.price
        return 0

    #发现某股票的仓位记录下标
    #----------------------------------------------------------------------
    def findOrder(self, code):
        """发现已有库单"""
        index = -1
        i = 0
        for order in self.orders:
            if 0: order = Order
            if order.code == code:
                index = i
            i+=1	

        return index

    #----------------------------------------------------------------------
    def buy_all(self, guider, fenshi):
        """"""
        if 0: fenshi = Fenshi
        if 0: guider = Guider
        price = guider.getLastData().close
        date = guider.getLastData().date
        if fenshi != None:
            price = fenshi.getLastData().GetPrice()
            date = fenshi.getLastData().date
        self.buy(guider.code, price, -1, date)

    def sell_all(self, guider, fenshi):
        """"""
        if 0: fenshi = Fenshi
        if 0: guider = Guider
        price = guider.getLastData().close
        date = guider.getLastData().date
        if fenshi != None:
            price = fenshi.getLastData().GetPrice()
            date = fenshi.getLastData().date
        self.sell(guider.code, price, -1, date)

    def buy_percent(self, code, price, percent, date):
        """根据可用资金的百分比来下单 percent: float 可用资金的百分比"""
        money = self.money * percent
        num = money / price
        num = self.ShouShu(num)
        return self.buy(code, price, num, date)
    #----------------------------------------------------------------------
    def buy(self, code, price, num, date):
        """"""
        if num == -1 :
            num = int((self.money / price) / 100) * 100
        if num % 100 != 0:
            return False
        if num == 0 :
            return False
        money = price * num
        if self.money < money:
            return False

        order_weituo = Order(code, date, price, num)	
        self.weituo_historys.append(order_weituo)
        self.detailed_orders.append(Order(code, date, price, num))

        #合并库单
        index = self.findOrder(code)
        if index>=0:
            order = self.orders[index]
            order.price = (order.price*order.num + price*num)/(num + order.num)
            order.num += num
        else:
            order = Order(code, date, price, num)	
            self.orders.append(order)

        self.money -= price*num
        self.total_moneys.append(self.money+self.getShiZhi(code, price))
        return True

    #----------------------------------------------------------------------
    def sell(self, code, price , num , date):
        """"""

        index = self.findOrder(code)			

        if index>=0:
            if 0:order = Order
            order = self.orders[index]
            if num == -1 :
                num = order.num
            #看是否超出可卖数量， 
            num = min(num , self.GetCanSellNum(code, date))
            if num == 0:
                return False
            if order.num < num:
                return False
            if dateutil.parser.parse(agl.DateTimeToDate(date)) <= \
               dateutil.parser.parse(agl.DateTimeToDate(order.date)):
                return False
            #	    

            order_weituo = Order(code, date, price, num, False)
            self.weituo_historys.append(order_weituo)

            #从低价位开始删除详细单
            num1 = num
            for o in self.detailed_orders:
                if 0: o = Order
                if o.code == code and date != o.date:
                    if price > o.price:
                        if num1 > o.num:
                            num1 -= o.num
                            o.num = 0
                        else:
                            o.num -= num1
                            num1 = 0
                            break
            #删除num=0的单
            for i in range(len(self.detailed_orders)-1, -1, -1):
                if self.detailed_orders[i].num == 0:
                    del self.detailed_orders[i]

            new_num = order.num - num
            if new_num == 0:
                del self.orders[index]
            else:
                self.orders[index].price = (order.price*order.num - price * num) / new_num
                self.orders[index].num = new_num

            self.money += price*num *(1-self.sxf()) - 5
            self.total_moneys.append(self.money+self.getShiZhi(code, price))
            return True

        return False

    #
    #手数, 去掉后面的值
    #----------------------------------------------------------------------
    def ShouShu(self, num):
        """"""
        num = int(num /100.0 )*100
        return num


    #
    #获取某股票当天可卖股数
    #----------------------------------------------------------------------
    def GetCanSellNum(self, code, date):
        """"""
        #在委托数据记录中找到当天的数量
        num = 0
        for order in self.weituo_historys:
            if 0: order = Order
            if order.code == code and order.date == date and order.buy == True:
                num += order.num

        #再看仓位记录里该股票的仓位
        index = self.findOrder(code)
        if index>=0:
            #assert(self.orders[index].num - num >= 0)
            return self.orders[index].num - num
        return 0

    def Trade(self, code, price, sign, num, date):
        if sign>0:
            return self.buy(code, price, num, date)
        if sign < 0:
            return self.sell(code, price, num, date)
        return False
    #----------------------------------------------------------------------
    def myprint(self, code_closes, is_draw=False):
        """输出账号的买卖记录
        code_closes: list (code,price)	用收盘价统计市值
        is_draw : bool  是否图形显示"""
        #return
        #for order in self.orders:
            #if 0: order = Order
            #order.myprint()
        for order in self.weituo_historys:
            order.myprint()
        print("------------------")
        #交易次数, 可用金额， 股票市值， 总金额, 原始资金
        total_money = self.getMoney(code_closes)
        help.myprint(len(self.weituo_historys), self.money, total_money-self.money, total_money, self.org_money, len(self.weituo_historys))
        for order in self.orders:
            if 0: order = Order(code, date, price, num)
            print("剩余仓位", order.myprint())
            self.sell(order.code, self.weituo_historys[-1].price, -1, self.weituo_historys[-1].date)
        if is_draw:
            self.plot()
    def plot(self):
        #绘制总资金，可用资金，股价到一张图上
        pl.figure
        #买卖点列表
        a = []
        for h in self.weituo_historys:
            a.append(h.price)
        a = GuiYiHua(a)
        pl.plot(a, 'b')
        #总资金
        a = np.array(self.total_moneys)
        a = GuiYiHua(a)
        pl.plot(a, 'r')
        pl.legend(['price list', 'money list'])
        pl.show()
        pl.close()

    #因为考虑到兼容性，没有推翻重来, 因此只能不考虑效率了
    def get_WeituoDf(self, day=''):
        """得到某一天的委托列表
        return: df index=datetime columns=['code','day','price','buy']"""
        if day == '':
            day = agl.CurDay()
        #对象转数组
        objs = []
        for order in self.weituo_historys:
            objs.append(order.ToList())
        if len(objs) == 0:
            return pd.DataFrame([])
        objs = np.array(objs)
        df = pd.DataFrame(objs, pd.DatetimeIndex(objs[:,1]), columns=['code','day','price','num','buy'])
        #df = df.convert_objects(convert_numeric=True)
        df['buy'] = df['buy'].astype(int)
        if day in df.index:
            return df.ix[day]	
        return pd.DataFrame([])
    @staticmethod
    def Test():
        account = Account()
        code, price, num, date = '600779', 19.8, 200, '2014-1-3'
        for i in range(3):
            account.buy(code, price+i, num, date)
        account.myprint()


#
#----------------------------------------------------------------------
def Unittest_Fuquan():
    """复权测试"""
    code = "002334"
    kline = Kline(code)
    print(kline.getData(30).close)
    guider = Guider(code)


    print(guider.getData(30).close)
#
########################################################################
class Fenshi:
    """Fen shi"""

    orders = []
    code = ''
    date=''
    yestoday_close = 0
    #----------------------------------------------------------------------
    def __init__(self, code, date, yestoday_close=0):
        """Constructor"""
        date = str(date)
        self.code = code
        self.date = date
        self.yestoday_close = yestoday_close
        #db = mysql.StockMysql()
        db = mysql.createStockDb()
        #取昨收盘
        if yestoday_close == 0 :
            kline = Kline(code, '', date)
            if kline.getSize()-2>=0:
                self.yestoday_close = kline.getData(kline.getSize()-2).close
            else:
                self.yestoday_close = 0
        orders = db.getFenshi(code, str(date))
        self.orders = []
        for order in orders:
            self.orders.append(Order('', order[0], order[1], order[2], order[4]))

        #print self.orders
        #assert len(self.orders) > 0
        #print "fenshi["+str(self.code)+"]"+str(date)

    #
    #----------------------------------------------------------------------
    if 0: getData = Order
    def getData(self, index):
        """"""
        return self.orders[index]

    #
    #----------------------------------------------------------------------
    if 0: getLastData = Order
    def getLastData(self):
        """"""
        return self.getData(len(self.orders)-1)

    #
    #----------------------------------------------------------------------
    def getCloses(self):
        """"""
        closes = []
        for order in self.orders:
            if 0: order = Order
            closes.append(order.GetPrice())
        return np.array(closes)

    #----------------------------------------------------------------------
    def myprint(self):
        """"""
        for order in self.orders:
            if 0: order = Order
            order.echo()

    #一分钟平均
    #----------------------------------------------------------------------
    def mean(self):
        """
        avg one minute
        none return
        """
        if len(self.orders) == 0:
            return

        orders = []
        if 0 : cur_order = Order

        date = 0
        price_sum = 0
        num_sum = 0
        count = 0
        for order in self.orders:
            if 0: order = Order
            if date != order.date:
                if count > 0:
                    cur_order = Order(order.code, date, price_sum/count, num_sum, True)
                    orders.append(cur_order)
                price_sum = 0
                num_sum = 0
                count = 0
            date = order.date
            price_sum += order.price
            num_sum += order.num
            count += 1

        if date != 901:
            if count > 0:
                cur_order = Order(order.code, date, price_sum/count, num_sum, True)
                orders.append(cur_order)

        self.orders = orders


    #	
    #
    #----------------------------------------------------------------------
    def DateToIndex(self, date):
        """"""
        for i in range(0, len(self.orders)):
            if date <= self.getData(i).date:
                return i
        return 0

    #----------------------------------------------------------------------
    def resize(self, date):
        """"""
        index = self.DateToIndex(date)
        if index >= 0:
            self.orders= self.orders[:index+1]

    #
    #----------------------------------------------------------------------
    def getSize(self):
        """"""
        return len(self.orders)

    def ToMatrix(self):
        """return: 当天的分笔数组"""
        datas = []
        for i in range(self.getSize()):
            order = self.getData(i)
            datas.append([order.date, order.buy, order.price, order.num])
        return np.array(datas)

    #----------------------------------------------------------------------
    def calcPath(self):
        """一分钟平均后的价格绝对值差价之和"""
        sum = 0
        for i in range(1, self.getSize()):
            sum += abs(self.getData(i).GetPrice() - self.getData(i-1).GetPrice())/self.getLastData().GetPrice()
        return sum


    #
    #快速突破起站点， 之前的价格在其正负1%之间
    #----------------------------------------------------------------------
    def Kstp_QiZhangQuJian(self, index_qizhangdian):
        """"""
        price = self.orders[index_qizhangdian].price


    @staticmethod
    def getLastFenshi(code):
        kline = Kline(code)
        date = kline.getLastData().date
        fenshi = Fenshi(code, date)
        return fenshi
#
#----------------------------------------------------------------------
def Unittest_Kstp():
    """"""
    fenshi = Fenshi('000100', '2011-1-6')
    fenshi.kstp(5, 3)
    #fenshi.myprint()


#
########################################################################
class StockTime:
    """把tdx tick转换为标准时间"""
    minute = 0

    #----------------------------------------------------------------------
    def __init__(self, minute):
        """Constructor"""
        #570 690 779
        if minute > 690 :
            minute -= 90
        minute -= 570

        self.minute = minute

    #
    #----------------------------------------------------------------------
    def getMinute(self):
        """"""
        return self.minute


    #----------------------------------------------------------------------
    def Dec(self, object):
        """"""
        return self.minute - object.getMinute()

    #
    #----------------------------------------------------------------------
    def Add(self, object):
        """"""
        return self.minute + object.getMinute()
    @staticmethod
    def ToTime(stock_fenshi_time):
        hour = stock_fenshi_time/60
        minute = stock_fenshi_time%60
        return hour, minute
    @staticmethod
    def s_ToStrTime(tdx_tick_time, day):
        """tdx_tick_time: 570 为9:30, 整数时间
        day : 日期
        return 2014-1-1 9:30:00"""
        hour, minute = StockTime.ToTime(tdx_tick_time)
        return "%s %s:%s:00"%(day, hour, minute)
    @staticmethod
    def s_ToStrDate(day):
        """day : 20150507
        return: 2015-05-07"""
        year = day/10000
        month = (day%10000)/100
        day = day%100
        return "%d-%d-%d"%(year,month,day)

def IsZhongXiaoBan(code):
    """判断一个股票代码是中小板"""
    return code[0] == "0" and code[1] == "0" and code[2] != "0"
#
def MA(closes, day=5):
    """closes is close price, day = avg day"""

    return talib.MA(closes, day)

def RSI(closes, timeperiod=12):
    """相对强弱指标， 30以下超卖， 70以上超买 return: np.darray"""
    closes = np.array(closes)
    closes = closes[np.isnan(closes) == False]
    return talib.RSI(closes, timeperiod)

def MACD(closes):
    """通过快慢均线交叉来判断交易信号
    MACD: (12-day EMA - 26-day EMA)	    慢线， 黑色
    Signal Line: 9-day EMA of MACD	    快线, 红色
    MACD Histogram: MACD - Signal Line  直方图, 柱状图
    return : macd, macdsignal, macdhist(柱状)"""

    return talib.MACD(closes)

def WILLR(highs, lows, closes):
    """0到-100的范围, 与KDJ相反, 0到-20卖出， -80到-100买入
    return: wr 
    """
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    return talib.WILLR(highs,lows,closes)

def OBV(closes, volumes):
    """能量潮, N字型推高或下跌， 类似于均线，需要使用趋势线分析方法
    return: obv"""
    return talib.OBV(closes, volumes)
def BOLL(closes, matype=MA_Type.EMA):
    """布林线
    matype: 使用的均线类型， 与通达信的计算有一点误差， EMA偏高2分，SMA小4分，其它的差别更大
    return upper, middle, lower"""
    closes = np.array(closes)
    return talib.BBANDS(closes, timeperiod=20, matype=matype)
def TDX_BOLL(closes):
    """最新版的TDX和该版本有轻微的差别， 但差别不大
    closes: np.ndarray
    return: upper, middle, lower
通达信的系统BOLL-M
    {参数 N: 2  250  20 }
    MID:=MA(C,N);
    #MID:=SMA(C,N,1);
    VART1:=POW((C-MID),2);
    VART2:=MA(VART1,N);
    VART3:=SQRT(VART2);
    UPPER:=MID+2*VART3;
    LOWER:=MID-2*VART3;
    BOLL:REF(MID,1),COLORFFFFFF;
    UB:REF(UPPER,1),COLOR00FFFF;
    LB:REF(LOWER,1),COLORFF00FF;    
    """    
    closes = np.array(closes)
    assert(len(closes)>=20)
    n = 20
    mid = talib.MA(closes, n)
    vart1 = np.zeros(len(closes))
    for i, v in np.ndenumerate(closes):
        i = i[0]
        vart1[i] = pow(closes[i] - mid[i], 2)
    vart2 = talib.MA(vart1, n)
    vart3 = np.sqrt(vart2)
    upper = mid + 2*vart3
    lower = mid - 2*vart3
    return upper, mid, lower
def TDX_BOLL2(closes):
    upper, mid, lower = TDX_BOLL(closes)
    w = abs(upper-lower)/mid*100
    return upper, mid, lower,w
#波动率指标
def ATR(highs, lows, closes):
    """真实波幅"""
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    return talib.ATR(highs, lows, closes)
def TDX_ADX(highs, lows, closes):
    """通达信版本的ADX, 单元测试见test_adx
    return: np.ndarray
MTR:=EXPMEMA(MAX(MAX(HIGH-LOW,ABS(HIGH-REF(CLOSE,1))),ABS(REF(CLOSE,1)-LOW)),N);
HD :=HIGH-REF(HIGH,1);
LD :=REF(LOW,1)-LOW;
DMP:=EXPMEMA(IF(HD>0&&HD>LD,HD,0),N);
DMM:=EXPMEMA(IF(LD>0&&LD>HD,LD,0),N);
PDI: DMP*100/MTR;
MDI: DMM*100/MTR;
ADX: EXPMEMA(ABS(MDI-PDI)/(MDI+PDI)*100,MM);
ADXR:EXPMEMA(ADX,MM);    
    """
    assert(len(closes)>30)
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)    

    mtr = np.zeros(len(closes))
    for i, v in np.ndenumerate(closes):
        i = i[0]
        if i>0:
            y = closes[i-1]
            mtr[i] = max(max(highs[i]-lows[i], abs(highs[i]-y)), abs(y-lows[i]))
    n = 14
    mm = 6
    mtr = talib.EMA(mtr, n)
    hd = np.zeros(len(highs))
    ld = np.zeros(len(highs))
    for i, v in np.ndenumerate(highs):
        i = i[0]
        if i>0:
            hd[i] = highs[i] - highs[i-1]
            ld[i] = lows[i-1] - lows[i]
            if not (hd[i] > 0 and hd[i]>ld[i]):
                hd[i] = 0
            if not (ld[i]>0 and ld[i]>hd[i]):
                ld[i] = 0

    dmp = talib.EMA(hd, n)
    dmm = talib.EMA(ld, n)
    pdi = dmp * 100 / mtr
    mdi = dmm * 100 / mtr
    adx = np.zeros(len(mdi))
    for i, v in np.ndenumerate(mdi):
        i = i[0]
        adx[i] = abs(mdi[i]-pdi[i]) / (mdi[i]+pdi[i])*100 
    adx = talib.EMA(adx, mm)
    return adx
def ADX(highs, lows, closes):
    """平均趋向指数, ADX指数是反映趋向变动的程度，而不是方向的本身
    DMI包含ADX，DX"""
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    return talib.ADX(highs, lows, closes, timeperiod=14)
def ADXR(highs, lows, closes):
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    return talib.ADXR(highs, lows, closes)
def DX(highs, lows, closes):
    """应该为DMI里的DI， 多空指标， 标示趋势方向，+为向上的趋势"""
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    return talib.DX(highs, lows, closes)
def FOUR(closes, days = [5,10,20,60]):
    """四均线计算 return: fours"""
    closes = np.array(closes)
    avgs = []
    for day in days:
        avgs.append(MA(closes, day=day))

    max_day = max(days)
    #计算每根线与其它线的差值并相加
    dvs = np.zeros(len(closes[max_day:]))
    for i in range(len(avgs)):
        c = avgs[i][max_day:]/closes[max_day:]
        for j in range(i, len(avgs)):
            dvs += c - avgs[j][max_day:]/closes[max_day:]
    max_day = min(max_day, len(closes))
    fours = np.zeros(max_day)
    fours = np.full(len(fours), np.nan)
    fours = agl.array_insert(fours, len(fours), np.array(dvs))
    return fours 
def FENSHI_MA(df):
    """计算分时均线 df: 分时 return: df 新增一个avg的列"""
    #df = df.resample('1min')
    avg = np.zeros(len(df))
    for i in range(len(df)):
        avg[i] = np.sum(df[:i+1]['p']*df[:i+1]['v'])/np.sum(df[:i+1]['v'])
    df['avg'] = avg
    #print df
    return df
def test_JiShuZhiBiao():
    """测试技术指标"""
    pl = publish.Publish()
    code = '002440'
    code = '999999'

    #计算分时的乖离率，rsi
    df = FenshiEx(code, '2014-10-8', '2014-10-8').df
    #df = FENSHI_MA(df)
    df = FENSHI_BIAS(df)
    df['rsi'] = RSI(df['p'])
    df1 = df.drop(['v','b','bias','rsi'], axis=1)
    ui.drawDf(pl, df1)
    df2 = df.drop(['v','b','p','avg', 'rsi'], axis=1)
    ui.drawDf(pl, df2)
    df2 = df.drop(['v','b','p','avg', 'bias'], axis=1)
    ui.drawDf(pl, df2)

def FENSHI_BIAS(df):
    """分时乖离率计算 df: 分时 return: df 新增bias列"""
    df = FENSHI_MA(df)
    df['bias'] = (df['p'] - df['avg'])*100 / df['avg']
    return df

def ZigZag(closes, percent=1):
    """计算zz线
    return: np.ndarray"""
    #如果是有负值的向量， 需要先偏移到正值再计算
    m = min(closes)
    if m<0:
        closes += abs(m)+0

    direction = 0;
    zz = []
    zz.append([0, closes[0]])

    j = 0 
    max_val = max(closes)
    for i in range(1, len(closes)):
        relClose = (closes[i] - zz[j][1]) / max_val * 100
        if (abs(relClose)>=percent) and (direction==0):
            j += 1
            zz.append([i, closes[i]])
            direction = help.sign(relClose)

        if (closes[i]>=zz[j][1]) and (direction==1):
            zz[j][0] = i
            zz[j][1] = closes[i]

        if (relClose < -percent) and (direction==1):
            direction = -1
            j=j+1
            zz.append([i,closes[i]])

        if (closes[i] < zz[j][1]) and (direction == -1):
            zz[j][0] = i
            zz[j][1] = closes[i]

        if relClose >= percent and direction==-1:
            direction = 1
            j += 1
            zz.append([i, closes[i]])

    #如果最后一个没有保存， 那么记上	
    if agl.array_last(zz)[0] != len(closes) -1:
        j += 1
        i = len(closes) -1
        zz.append([i, closes[i]])

    #负值还原
    zz = np.array(zz)
    if m < 0:
        zz[:,1] -= abs(m) +0
        closes -= abs(m)+0

    return zz   
def analyzeZZ(zz):
    """只取最后两段
    return: np.darray [[direction0, y0],[direction1, y1]] 方向1为上涨， -1为下跌, 价格差比, 前一个价格作为基准
    """
    zz = zz[-3:]
    y0 = (zz[1,1]-zz[0, 1])/zz[0,1]
    y1 = (zz[2,1]-zz[1,1])/zz[1,1]
    return (y0, y1)    
#----------------------------------------------------------------------
def Unittest_Kline():
    """"""
    kline = Guider("600100", "")
    print(kline.getData(0).date, kline.getLastData().date)

    #kline.myprint()
    obv = kline.OBV()

    pl.figure
    pl.subplot(2,1,1)
    pl.plot(kline.getCloses())
    pl.subplot(2,1,2)
    ma,m2,m3 = kline.MACD()
    pl.plot(ma)
    pl.plot(m2,'r')
    left = np.arange(0, len(m3))
    pl.bar(left,m3)
    #pl.plot(obv, 'y')
    pl.show()


#Unittest_Kstp()    
#
#找寻所有股票的底部突破
#----------------------------------------------------------------------
def findListStockZhangFuBigDay():
    """"""
    code = "600022"
    if 0:
        #ListStockZhangFuBigDay(0.07, "600188")
        codes = ["000002", "000563", "600008", "600000"]
        OneStockQjjy(codes[3], True)
        #OneStockQjjy("000002")
        #Qj(code)
        return

    #db = mysql.StockMysql()
    db = mysql.createStockDb()
    gupiaos = db.getGupiao()

    for gupiao in gupiaos:
        if 0:
            ListStockZhangFuBigDay(0.07, gupiao)
        if 0:
            ListStockKstp(gupiao)
        if 1:
            OneStockQjjy(gupiao, False)
        if 0:
            Qj(gupiao)



def unittest_dump():
    #Guider.DumpToFile()
    a= Guider.FromFile()
    print(np.shape(a))
    closes = Guider("600000").getCloses()

    pl.figure(1)
    a = a[0]
    a = a[np.nonzero(a)]
    pl.plot(a)
    pl.figure(2)
    pl.plot(closes[:len(a)+1])
    pl.show()
def SYL(price, mgsy):
    """mgsy = 全年利润/总股本"""
    if price < 0:
        price = 0.01
    if mgsy == 0:
        return -0.01
    return price / mgsy
def PE(shizhi, jll):
    """shizhi: 市值(亿), jll: 净利润(亿)"""
    return float(shizhi)/float(jll)
def StockToMatlabCsv():
    guider = Guider("600779")
    closes = guider.GetCloses()
    agl.MatrixToCsv(closes, "..\\matlab_src\\Automated_Trading\\stock.txt")
def getMainBanCode(code):
    """获取大盘代码"""
    if code[0] == '3':
        return myenum.DaPan.chuangyeban
    if code[0] == '6':
        return myenum.DaPan.shanghai
    if code[0] == '0':
        if code[2] != '0':
            return myenum.DaPan.zhongxiao
        return myenum.DaPan.shengzheng
    return myenum.DaPan.shanghai
def getDapanCode(code):
    """获取代码所属的大盘代码 return: str 大盘代码"""
    return getMainBanCode(code)

def GuiYiHua(closes):
    """ return: closes"""
    if isinstance(closes, pd.Series):
        closes = closes / np.max(closes)
        return closes
    if isinstance(closes, pd.DataFrame):
        df = closes
        for col in df.columns:
            df[col] = df[col] / np.max(df[col])
        return df
    h = np.max(closes)
    closes = closes/h
    return closes

def unittest_ma():
    closes = Guider('600100').getCloses()
    print(MA(closes))
    fours = FOUR(closes)
    print( len(closes), len(fours))
    print(fours)
    rsi = RSI(closes)
    #rsi = rsi/100 - 0.5
    rsi -= 50
    fours *= 100
    pl.figure
    #pl.plot(closes)
    pl.plot(fours,'r')
    pl.plot(rsi)
    pl.show()
def getGuPiaoListFromMysql(dtype=np.ndarray):
    """获取股票列表信息"""
    datas = []
    #db = mysql.StockMysql()
    db = mysql.createStockDb()
    for data in db.getGuPiaoList():
        price = db.getCurrentPrice(data[1])
        datas.append([float(data[1]),  float(data[3]), float(data[7]), price])
    #datas = np.array(datas, dtype=[('a','<i4'),('b','<f4'),('c','<f4')])
    datas = np.array(datas, dtype=np.float)
    if dtype != np.ndarray:
        datas = pd.DataFrame(datas)
    return datas
if 0:getGuPiaoList = pd.DataFrame
def getGuPiaoList():
    """从本地csv（来自插件）获取列表, 新浪数据, 不全
    csv文件需要手工转换为utf-8, 此时能够正常显示中文
    a股票代码，b股票名称，c流通股本，d行业，e总股本，f总资产，g每股收益"""
    #path = 'stockinfo.pickle'
    #if help.FileExist(path):
        #return pd.DataFrame().load(path)
    #def my_convert(x):
        #if x=='':
            #x = 0
        #return float(x)
    #需要修改成直接读数据表gupiao
    #db = mysql.StockMysql()
    db = mysql.createStockDb()
    rows = db.getGuPiaoList()
    rows = np.array(rows)
    #rows = np.array(rows, dtype=[('0','<i4'), ('a', '<U13'),('b', '<U13'),\
                                    #('c','<f4'),('d', '<U13'),('e','<f4'),\
                                    #('f','<f4'),('g', '<f4')])
    rows = rows[:, 1:]
    rows = rows[np.array(rows[:,-1], dtype=float) != 0]
    datas = pd.DataFrame(rows,columns=list('abcdefg'), \
                         #dtype={'a':object, 'b':object,'c':np.float,'d':object,'e':np.float,'f':np.float,'g':np.float}\
                         )
    #因为本地表里的行业不对， 用新浪行业来替换
    sina_datas = pd.read_csv('datas/sina_web_datas.txt')
    datas['d'] = sina_datas['4']
    #datas = pd.read_csv('stockinfo.csv',\
        ##header=['a','b','c','d','e','f','g'],\
        #dtype={'a':object, 'b':object,'c':np.float,'d':object,'e':np.float,'f':np.float,'g':np.float},\
        ##converters={'g':lambda x: x}\
        #)
    for col in list('cefg'):
        datas[col] = datas[col].convert_objects(convert_numeric=True)
    #插入现价
    codes = datas['a']
    prices = []
    for code in codes:
        price = db.getCurrentPrice(code)
        prices.append(price)
    datas['h'] = prices

    #datas.save(path)
    return datas

def PrintAllGupiaoListAndIndex():
    codes = simulator.ISimulator.getGupiaos(enum.all)
    for i in range(len(codes)):
        print( i, codes[i])
def GetIndexFromGupiaoListAtAll(code):
    codes = simulator.ISimulator.getGupiaos(enum.all)
    for i in range(len(codes)):
        if codes[i] == code:
            return i
    return 0
def TestReadCode(code):
    ts = Guider(code, period_type=Guider.enum.period_1).getCloses()
    ts = Fenshi(code, date=20140321).getCloses()
    ui.DrawTs(pl, ts)
def Unittest_1minuteFenshiDump():
    agl.tic()
    datas = Kline.FromFile()
    closes = Kline.getSerialCloses(datas[0])
    agl.toc()
    print( closes)
def IsCode(s):    
    """判断字符串是否是股票代码"""
    if len(s)!= 6:
        return False
    m = re.search(r'^[0-9]*$', s)
    if m != None:
        return True
    return False
def IsZhiShuCode(code):
    """判断是否是指数代码 return: bool"""
    if code[0] == '6' or code[0] == '3' or code[0] == '0':
        return False
    return True
def IsChuanYeBan(code):
    return code[0] == '3'
#板块
class TdxBlock:
    """从文件中提取通达信的板块个股, 1从tdx目录中取(风格，概念)， 2，从导出文件中取(行业，地区)， 3，指数的代码名称表"""
    def __init__(self):
        """因为序列化的原因， 该构造不能直接调用， 需要使用CreateInstance来替代"""
        path = "C:\\jcb_zxjt\\T0002\\hq_cache"
        self.path = path
        fname = "TdxBlock.pickle"
        self._getBankuaiCodeName()
        files = ['block.dat','block_zs.dat','block_gn.dat','block_fg.dat']
        self.files = []
        for f in files:
            self.files.append(path + "\\" + f)
        self.dictBlock = self._genDict()
        #for k in self.dictBlock.keys():
            #print k
        self._getHyDiqu()
    def _getHyDiqu(self):
        """目录中存放着从通达信中导出的各行业对应的股票列表
        生成名称代码对应map"""
        path = "C:\\chromium\\src\\autoxd3\\python\\datas\\block"
        #遍历全部文件
        for root , dirs, files in os.walk(path):
            for f in files:
                name = str.split(f, '.')[0]
                name = name.decode('gb2312')
                f = path + "\\"+f
                codes = self._getCodesFromFile(f)
                self.dictBlock[name] = codes[1:]
    def _getContent(self, fname):
        f = open(fname, 'rb')
        datas = f.read()
        f.close()
        #收集全部字符串
        my_strs = []
        a = []
        for data in datas:
            d = ord(data)
            if d != 0:
                a.append(d)
            else:
                if len(a)>=4:
                    v = agl.ArrayToStr(a)
                    #print v, len(v)
                    my_strs.append(v)
                a = []
        #根据字符串再分割
        bankuais = []
        bankuai = []
        for i in range(1, len(my_strs)):
            if IsCode(my_strs[i]) and IsCode(my_strs[i-1]) == False:
                if len(bankuai) > 0:
                    bankuais.append(bankuai)
                    bankuai = []
                bankuai.append((my_strs[i-1]).decode('gb2312'))
            if IsCode(my_strs[i]):
                bankuai.append(my_strs[i])
        #print bankuais[0][0]		
        return bankuais
    def _genDict(self):
        bankuais = {}
        for f in self.files:
            block = self._getContent(f)
            for b in block:
                bankuais[b[0]] = b[1:]
        #print bankuais[u'电商概念']
        return bankuais
    def _getBankuaiCodeName(self):
        """生成code与name的对应表, [[code, name],...], 直接读tdx目录中的板块文件"""
        fnames = ['tdxindex.cfg', 'tdxzs.cfg']
        #fnames = ['tdxzs.cfg']
        columns = ['name', 'code', 'type', 'count', 'type3', 'desc']
        def ReadFileContent(fname):
            f = open(fname, 'r')
            lines = f.readlines()
            f.close()
            bankuai_codes = []
            for line in lines:
                a = str.split(line, '|')
                bankuai_codes.append([a[1],a[0].decode('gb2312')])
            return bankuai_codes
        bankuai_codes = []
        for fname in fnames:
            fname = self.path +"\\"+fname
            bankuai_codes += ReadFileContent(fname)
        self.code_name_tbl = pd.DataFrame(bankuai_codes)
        #print self.code_name_tbl
        return self.code_name_tbl
    def _getCodesFromFile(self, fname):
        """从板块导出文件中获取代码列表"""
        f = open(fname, 'r')
        lines = f.readlines()
        f.close()
        codes = []
        for line in lines:
            a = str.split(line, '\t')
            if len(a) >4:
                codes.append(a[0])
        return codes
    def getBankuaiCodes(self, bankuai_name):
        """查询板块所属code列表， 
        bankuai_name: 可以是中文(unicode)，也可以是代码
        return : list"""
        #从代码获取名字
        code = self.getCodeOrName(bankuai_name)
        if code != None:
            assert not IsCode(code)
            if self.dictBlock.has_key(code):
                return self.dictBlock[code]
        return None
    def getCodeOrName(self, code):
        """从代码获取名字， 或从名字获取代码"""
        df = self.code_name_tbl
        if not IsCode(code):
            df2 = df[df[1]==code]
        else:
            df2 = df[df[0]==code]
        if len(df2) ==  1:
            #return df2[1][0]	#df取值有时候会遇到编码问题
            return np.array(df2)[0][1]
        return None
    @staticmethod
    def CreateInstance():
        fname = "TdxBlock.pickle"
        tb = agl.SerialMgr.unserial(fname)
        if isinstance(tb, TdxBlock):
            agl.SerialMgr.serial(tb, fname)
            return tb
        return TdxBlock()
    @staticmethod
    def unittest():
        tb = TdxBlock.CreateInstance()
        codes = tb._getBankuaiCodeName()
        #打印全部信息, 从结果看， 有用的板块特别是概念板块都有， 没有的可暂时忽略
        for (i, code) in enumerate(codes[0]):
            list_codes = tb.getBankuaiCodes(code)
            if list_codes != None and len(list_codes) > 0:
                print( u"有", tb.getCodeOrName(code))
                print (list_codes)
            else:
                print (u"没有", tb.getCodeOrName(code))

        #for k in tb.dictBlock.keys():
            #print k
        #print tb.code_name_tbl.head()
        #print tb.getBankuaiCodes(u'稀土永磁')
        #print tb.getBankuaiCodes('880409')
        #print tb.getBankuaiCodes(u'特斯拉')
        #print tb.getBankuaiCodes(u'有色')
        #print tb.getBankuaiCodes('880227')


        
def ZhengFu(v1, v2):
    """v1, 昨收盘
    v2, 今收盘"""
    return (v2-v1)/v1
def ZhangFu(price, yclose):
    """涨幅 return: float"""
    return (price - yclose) / yclose
def df_zhangfu(df):
    """通过df来计算涨幅 
    df.columns = list('hlocv')
    return: df"""
    c = np.array(df['c'])
    df.loc[:,'zhangfu']=(df['c'][1:] - c[:-1])/c[:-1]
    return df

def test_fenshi_rsi():
    """测试一个分时的rsi计算"""
    code = '300059'
    fenshi = CreateFenshiPd(code, '2015-8-6').resample('1min').mean().dropna()
    print( fenshi)
    closes = fenshi['p']
    print(closes)
    rsi = RSI(closes, 6)
    print(rsi)
    ui.DrawTs(pl, rsi)
def test_hisdat_redis():
    codes = get_codes(myenum.all)
    end_day = agl.CurDay()
    #end_day = '2015-8-16'
    start_day = help.MyDate.s_Dec(end_day, -15)    
    for code in codes:
        getHisdatDataFrameFromRedis(code, start_day, end_day)
        
#----------------------------------------------------------------------
def main():
    """"""
    #Account.Test()
    #PrintAllGupiaoListAndIndex()
    #print GetIndexFromGupiaoListAtAll("000596")
    #Guider.DataToR()    
    #Guider.unittest()
    #unittestCreatePd()
    #Unittest_Kline()
    #unittest_dump()

    #Guider.DumpToFile()
    #print StockInfo('002614').mgsy
    #Guider.Dump30ToFile()
    #Guider.Dump1ToFile()
    #FenshiEx.to_csv('000895')
    #Kline.DumpFenshiToFile()
    #Guider("000596","2012-1-1").FenshiDataToCsv()
    #h =  pd.DataFrame(Guider("002151",period_type=Kline.enum.period_month).hisdats)
    #print h
    #getGuPiaoList()    
    #print mysql.StockMysql().getCurrentPrice("600694")
    #Unittest_1minuteFenshiDump()
    #StockInfo.UpdateTable()

    #TestReadCode("880202")
    #unittest_ma()
    #DumpOne().Save()
    #print DumpOne().Load()
    #FenshiEx.Test()
    #test_fenshi_rsi()
    #print IsKaiPan()

    #TdxBlock.unittest()    
    #print IsCode('000000')
    #StockInfoThs.Test()
    #test_summary_bankuai_zhangfu()
    #test_beta()
    #test_calc_bankuai_zhishu()
    #DataSources.Test()
    #test_get_yjyb()
    #memcache_load()
    #print Guider.getAllKlineDf()

    #Guider.DumpToRedis()
    #test_hisdat_redis()
    #test_calc_fuquan_use_fenhong()
    #test_JiShuZhiBiao()
    #print createThs().d
    #print createThs().createThsOneCode('600570').get_mgsy()
    #StockInfoThs.genCodeNameTbl()
    #print GetCodeName('300059')

    unittest.main()
if __name__ == "__main__":
    main()
    print('end')
