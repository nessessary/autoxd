#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457
from __future__ import print_function
import os,sys
import help,agl,ui,myenum,myredis
if sys.version > '3':
    import stock_pinyin3 as jx
else:
    import stock_pinyin as jx
import pyprind
import time,datetime, dateutil,copy, warnings, unittest,struct, itertools,pickle,re
import talib
from talib import MA_Type
import numpy as np
import pylab as pl
import pandas as pd
from sklearn.cluster import KMeans
import grabThsWebStockInfo
from pypublish import publish
#pl = publish.Publish()

def get_codes(flag=myenum.all, n=100):
    """获取有效的股票列表, enum现在改为myenum
    flag : enum.all 等枚举 , enum.exclude_cyb 排除创业板, enum.rand10 随机选10个
    n : enum.rand时使用
    return: list """
    def readTDXlist():
        #从本地csv读取
        cur_path = os.path.dirname(os.path.abspath(__file__))
        fname = cur_path + '/datas/tdx_codes.csv'
        df = pd.read_csv(fname, dtype=str, header=None)
        codes = df[0].tolist()    
        if len(codes)>0:
            #默认去除大盘的代码
            dapans = ['399001', '999999','399005','399002','399006','510050']
            codes = [unicode(code) for code in codes if code not in dapans]
            #codes = filter(lambda x: x[:2] != '88', codes)
        return codes
    key = myredis.enum.KEY_CODES    #更新ths F10时删除
    #这里不能使用从THS来读， 当重新拉取时， 会引起递归
    val = myredis.createRedisVal(key, readTDXlist)
    codes = val.get()
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

def get_bankuai_codes(bankuai):
    """从板块名获取该板块的股票代码
    bankuai: str 板块名称 包括行业及概念
    return: list"""
    key = myredis.enum.KEY_THS_GAIYAO
    val = myredis.createRedisVal(key, lambda: createThs().getDf(0))
    codes = []
    names = ['所属行业', '涉及概念','概念强弱排名']
    df = val.get()
    for i in range(len(df)):
        r = df.iloc[i]
        code = r['code']
        bankuai_cur = ''
        for name in names:
            if name in df.columns:
                bankuai_cur += str(r[name])
        if bankuai_cur.find(bankuai) >= 0:
            codes.append(code)
    return codes

def get_bankuai_avg_syl(bankuai, method='avg'):
    """获取板块平均市盈率
    method: str avg|low|all 平均市盈率|低位聚类|列表
    return: float"""
    key = myredis.enum.KEY_BANKUAI_AVG_SYL
    val = myredis.createRedisVal(key, lambda: createThs().getPjSylTable())
    df = val.get()
    df = df[df['行业及概念'] == bankuai]
    if method == 'all':
        return df
    if method == "avg":
        return float(df.iloc[0]['平均市盈率'])
    return df.iloc[0]['低位聚类市盈率']

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
        import fenshi_beta
        for key in myredis.getKeys():
            if key.find(fenshi_beta.FenshiBankuaiCache.keyhead)==0:
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
        #df = getHisdatDataFrameFromRedis(code)
        key = 'live_h_'+code
        hisdat = myredis.get_Bin(key)
        if agl.IsNone(hisdat) or len(hisdat) == 0:
            return pd.DataFrame([])
        a = []
        n = (4+5*4)
        for i in xrange(len(hisdat)/n):
            e = list(struct.unpack("=ifffff", hisdat[n*i:n*(i+1)]))
            e[0] = StockTime.s_ToStrDate(e[0])
            a.append(e)
        df = pd.DataFrame(a)
        df = df.set_index(df.columns[0])
        df.index = pd.DatetimeIndex(df.index)
        df.columns = list('hlocv')
        df['h'] /= 100.0
        df['l'] /= 100.0
        df['o'] /= 100.0
        df['c'] /= 100.0
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
        df[0] = df[0].map(lambda x: StockTime.s_ToStrTime(int(x), agl.CurDay()))
        df = df.set_index(df.columns[0])
        df.index = pd.DatetimeIndex(df.index)
        df.columns = list('pvdb')
        df['p'] /= 100.0
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
        df['h'] /= 100.0
        df['l'] /= 100.0
        df['o'] /= 100.0
        df['c'] /= 100.0
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
        codes = get_bankuai_codes('智能音箱')
        print(calc_bankuai_fenshi_zhishu(codes, date, end_day, ltgbs))
    def _test_beta(self):
        pl = publish.Publish()
        days = pd.period_range(start='2014-8-1', end='2015-4-28', freq='Q' )
        codes = get_codes(myenum.randn, 5)
        codes = [jx.DFZQ]
        for code in codes:
            for day in days.to_datetime():
                day = str(day.date())
                get_onecode_beta(code, day, pl)
        df = getHisdatDataFrameFromRedis(code)                
        df_bk = getHisdatDataFrameFromRedis('手机游戏')
        BETA(df['c'], df_bk,pl)

    def test_calc_fuquan(self):
        code = jx.SNYG
        df = getHisdatDf(code)
        print(df)
        df = getHisdatDf(code, is_Trunover=True)
        agl.print_df(df)
        ui.drawDf(pl, df)
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
        myredis.delkey(myredis.enum.KEY_CODES)
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
        print(upper[-10:])
        print(middle[-10:])
        print(lower[-10:])
        #df_five_hisdat['upper'] = upper
        #df_five_hisdat['lower'] = lower
        #df_five_hisdat['mid'] = middle
        #df = df_five_hisdat[['upper', 'c', 'mid', 'lower']]
        #df.plot()
        #pl.show()
        upper, middle, lower, boll_w = TDX_BOLL2(df_five_hisdat['c'])
        print(boll_w)
    def _test_livedata(self):
        code = '300033'
        print(LiveData().getHisdat(code))
        print(LiveData().getFiveMinHisdat(code))
        f=LiveData().getFenshi(code)
        print(f)
        print(1)
    def _test_grabths(self):
        code = jx.THCJ
        print(getFenHong(code))
    def _test_ths(self):
        agl.tic()
        ths = createThs()
        agl.toc()

        code = jx.TJGF.c
        df = ths.getDf(0)
        df = df[df['code'] == code]
        print(df.iloc[0])

        #price = getHisdatDataFrameFromRedis(code).iloc[-1]['c']
        #one = ths.createThsOneCode(code, price=price)
        #one = ths.createThsOneCode(code)
        #ths = THS()
        #print(ths.df_jll)

    def _test_history(self):
        code = jx.THS
        df = myredis.get_obj(code)
        print(df)
    def _test_fenshi_fuquan(self):
        #5-9除权
        code, start_day, end_day = '002560', '2016-3-1','2016-5-20'
        df = getHisdatDf(code, start_day, end_day, True)
        #df = FenshiEx(code, start_day, end_day, True).df
        print(df)
    def _test_Bankuais(self):
        #myredis.delkey(myredis.enum.KEY_BANKUAIS)
        agl.print_ary(get_bankuais())
        bankuais = filter(lambda x: x.find('360')>=0, get_bankuais())
        agl.print_ary(bankuais)
        print(get_bankuai_codes(bankuais[0]))
        print(get_bankuai_codes('航母'))
        #板块评价市盈率
        bankuai = '人工智能'
        print(get_bankuai_avg_syl(bankuai))

        df = THS().df_jll
        df = df[df['code']=='300033']
        print(df)
    def _test_bankuai_analyze(self):
        StockInfoThs.Test_Bankuai_Zhishu()
    def _test_GetCodeName(self):
        print(GetCodeName('603444'))
    def _test_get_ths_codes(self):
        print(getTHS_custom_codes())
    def _test_WhiteHorse(self):
        print(IsWhiteHorse(jx.SWKJ))
    def _test_dump(self):
        DumpToRedis()
    def _test_zz(self):
        pl = publish.Publish()
        closes = getHisdatDataFrameFromRedis(jx.THS)['c']
        closes = closes.values[-1000:]
        zz = ZigZag(closes, percent=5)
        print(zz)
        ui.DrawZZ(pl, zz)
        #验证zz非未来函数
        zz = ZigZag(closes[:-200], percent=5)
        ui.DrawZZ(pl, zz)
        zz = ZigZag(closes[:-195], percent=5)
        ui.DrawZZ(pl, zz)
    def _test_DumpToDir(self):
        DumpToDir()

def IsKaiPan():
    """确定当前是处于开盘时间 return: bool"""
    t = ['9:15:00','11:30:00','13:00:00', '15:00:00']	
    for i in range(len(t)):
        t[i] = dateutil.parser.parse(t[i]).time()
    cur_t = time.localtime()
    cur_t = datetime.time(cur_t.tm_hour, cur_t.tm_min, cur_t.tm_sec)
    if (cur_t >= t[0] and cur_t<= t[1]) or (cur_t>t[2] and cur_t <t[3]):
        return True
    return False
def IsShouPan():
    """收盘"""
    t = dateutil.parser.parse('15:00:00').time()
    cur_t = time.localtime()
    cur_t = datetime.time(cur_t.tm_hour, cur_t.tm_min, cur_t.tm_sec)
    return cur_t > t
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
        df = mysql.getHisdat(code, date, end_day)
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
    #for i in range(2):
        #if len(df) > len(df_dp):
            #df = df[df.index.map(lambda x: x in df_dp.index)]
        #else:
            #df_dp = df_dp[df_dp.index.map(lambda x: x in df.index)]
    df_dp = df_dp[df_dp.index.map(lambda x: x in df.index)]
    #assert(len(df) == len(df_dp))	    
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
    #low,high = 0,100
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
    df = getHisdatDataFrameFromRedis(code, day)
    if len(df) == 0:
        return None
    #code_dapan = getDapanCode(code)
    #df_dp = getHisdatDataFrameFromRedis(code_dapan, day)
    df_dp = getHisdatDataFrameFromRedis('手机游戏')
    return BETA(df['c'], df_dp, pl)
def calc_fuquan_use_fenhong(df, df_fenhong):
    """获取复权后的历史数据, 用分红表来计算复权 , 前复权
    df: 日k线
    df_fenhong: 分红表
    return: df"""
    assert(len(df)>0)
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

###基本面#######
def getFenHong(code, update=False):
    ths = grabThsWebStockInfo.GrabThsWeb(code)
    key = ths.GetFenHongKey()
    if update:
        myredis.delkey(key)
    def convert_fenhong(df):
        """转换分红表格式为数据格式
        分红记录 (说明, 股， 派现，除权日)
        return: df columns('股，现金, 日期')"""
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
    def impl():
        return convert_fenhong(ths.getFenHong())
    return myredis.createRedisVal(key, impl).get()
def getGubenbiangen(code, update=False):
    ths = grabThsWebStockInfo.GrabThsWeb(code)
    key = ths.GetGubenbiangenKey()
    if update:
        myredis.delkey(key)
    def impl():
        return ths.getGubenbiangen()
    return myredis.createRedisVal(key, impl).get()
###############    

def convertVolToStockTrunover(df, df_GuBen_change):
    """成交量转换手率, 通过历史股本变更表来计算
    df: hisdat
    return: df 换手率覆盖了v字段
    """
    #股本变动表
    col = '变动后流通A股(股)'
    #调整一下col
    df_GuBen_change.columns = df_GuBen_change.iloc[0]
    df_GuBen_change = df_GuBen_change.drop(index=0)
    #防止有超过当前日期的数据
    df_GuBen_change.index = pd.DatetimeIndex(df_GuBen_change[df_GuBen_change.columns[0]])
    df_GuBen_change = df_GuBen_change.sort_index(ascending=True)    #与df顺序一致
    last_day = agl.datetime_to_date(df.index[-1].to_pydatetime())

    #计算当时的流通股本
    df_GuBen_change[col] = df_GuBen_change[col].map(lambda x: agl.StrToFloat(x))
    df_GuBen_change = df_GuBen_change.dropna()
    first_day = agl.datetime_to_date(df.index[0].to_pydatetime())
    df_GuBen_change = df_GuBen_change.ix[first_day:last_day]    

    #Merge时排序需要对应
    df = df.sort_index()    #mysql存储时有些乱序， merge时必须是排序的，降序
    if len(df_GuBen_change) > 0:
        df2 = pd.merge_asof(df, df_GuBen_change,left_index=True,right_index=True)
        df2 = df2.fillna(method='backfill') #降序， 前面的Nan用第一个有数的值填充
        df2['v'] = df2['v']*100/df2[col]
        df['v'] = df2['v']
    else:   #有些老股因为送股太早，因此这里为空
        df['v'] = df['v']*100/(self.get_ltgb()*myenum.YI)

    #df['v'].plot()
    #pl.show()

    return df    


def getHisdatDf(code, is_fuquan=True , is_Trunover=False):
    """从数据库获取日线, 复权 
    is_fuquan : 使用前复权
    is_Trunover: 转换为换手率
    return: df"""
    df = LiveData().getHisdat(code)
    if is_fuquan:
        df_fenhong = getFenHong(code)
        df = calc_fuquan_use_fenhong(df, df_fenhong)    
    if is_Trunover:
        df_gubenbiangen = getGubenbiangen(code)
        df = convertVolToStockTrunover(df, df_gubenbiangen)
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
    #从拼音文件里获取中文名称
    fname = '../stock_pinyin3.py'
    name = None
    f = open(fname)
    if sys.version > '3':
        f = open(fname, encoding='utf8')
    for line in f.readlines():
        line = str(line)
        if str(line).find(code)>0 and str(line).find('#')>0:
            name = line.split('#')[-1]
            name = name[:-1]
            break
    return name
        
def load_ths_custom_codes():
    '先用ths导出自选股到桌面 获取自选股列表 return: list'
    fname = 'C:/Users/Administrator/Desktop/table.txt'
    codes = []
    if os.path.isfile(fname):
        f = open(fname, 'r')
        for l in f.readlines():
            if l[:2] == 'SH' or l[:2] == 'SZ':
                code = l[2:8]
                if code != '510050' and code not in myenum.DaPan.all_codes:
                    codes.append(code)
        f.close()	
    return codes
def getTHS_custom_codes():
    s = '510050'
    for code in load_ths_custom_codes():
        s += '|'
        s += code
    return s

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



datasource_fn = None  #数据函数 fn() return df
class DataSources:
    """生成数据面板, 面板数据选取的例子panel.ix[0].ix['2014-1-2']
    panel.ix[0, '2014']会失败"""
    class datafrom:
        """enum"""
        mysql = 1   #保留
        livedata = 2
        serial = 3  #废弃
        online = 4  #废弃
        custom = 5  #自定义实现
    data_mode = datafrom.livedata   #默认值, 影响日线模式
    @staticmethod
    def getHisdatPanl(codes, days):
        """k线的历史数据框面板
        codes: [list]
        days: [turple]
        return: [pandas.panel]"""
        start_day , end_day = days
        d = {}
        for code in codes:
            if DataSources.data_mode == DataSources.datafrom.mysql:
                df = getHisdatDataFrameFromRedis(code, start_day, end_day)
            else:
                if DataSources.data_mode == DataSources.datafrom.livedata:
                    df = LiveData().getHisdat(code)
                if DataSources.data_mode == DataSources.datafrom.custom:
                    df = datasource_fn()
                df = df.ix[start_day:end_day]
                #复权
                df_fenhong = getFenHong(code)
                df = calc_fuquan_use_fenhong(df, df_fenhong)
            df = df.sort_index()
            d[code] = df
        panel = pd.Panel(d)
        return panel
    @staticmethod
    def getFiveMinHisdatPanl(codes, days):
        start_day , end_day = days
        d = {}
        for code in codes:
            if DataSources.data_mode == DataSources.datafrom.mysql:
                df = mysql.getFiveHisdat(code, start_day, end_day)
            else:		
                if DataSources.data_mode == DataSources.datafrom.livedata:
                    df = LiveData().getFiveMinHisdat(code)
                if DataSources.data_mode == DataSources.datafrom.custom:
                    df = datasource_fn()
            df = df.ix[start_day:end_day]
            #复权
            df_fenhong = getFenHong(code)
            df = calc_fuquan_use_fenhong(df, df_fenhong)
            df = df.sort_index()
            d[code] = df
        return d

    @staticmethod
    def getFenshiPanl(codes, days):
        """索引使用datetime, 如果是一天的，那么day1=day2"""
        assert(False)   #废弃
        start_day , end_day = days
        d = {}
        for code in codes:
            fenshi = FenshiEx(code, start_day, end_day, is_fuquan=True)
            if len(fenshi.df) == 0:
                return d
            fenshi.df = fenshi.df[fenshi.df['p']>0.01]
            d[code] = fenshi.df
        #d = dict( (code, FenshiEx(code, start_day, end_day, is_fuquan=True).df) for code in codes )
        #这里产生了异常
        #panel = pd.Panel(d)
        return d


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
    df = pd.DataFrame(upper, columns=['upper'])
    df['mid'] = mid
    df['lower'] = lower
    df = df.fillna(value=0)
    w = abs(df['upper']-df['lower'])/df['mid']*100
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
    只有最后一个值是当前值， 之前的节点都是一致的, 非未来函数
    closes : np.ndarray
    percent: 忽略的百分比
    return: np.ndarray"""
    assert(isinstance(closes, np.ndarray))
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
            direction = 0
            if relClose>0:
                direction = 1
            if relClose<0:
                direction = -1

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
    if zz[-1][0] != len(closes) -1:
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
    #return: np.darray [[direction0, y0],[direction1, y1]] 方向1为上涨， -1为下跌, 价格差比, 前一个价格作为基准
    return: (y0, y1)
    """
    assert(len(zz)>2)
    zz = zz[-3:]
    y0 = (zz[1,1]-zz[0, 1])/zz[0,1]
    y1 = (zz[2,1]-zz[1,1])/zz[1,1]
    return (y0, y1)    

def zz_to_dfzz(zz,df):
    """把数组格式的zz转成df"""
    indexs = np.zeros(len(df))
    for i in zz[:,0]:
        indexs[int(i)] = 1
    indexs = indexs.astype(bool)
    indexs = df.index[indexs]    
    df = pd.DataFrame(zz[:,1], indexs)
    return df

def SYL(price, mgsy):
    """mgsy = 全年利润/总股本"""
    price = float(price)
    mgsy = float(mgsy)
    if price < 0:
        price = 0.01
    if mgsy == 0:
        return -0.01
    return price / mgsy
def PE(shizhi, jll):
    """shizhi: 市值(亿), jll: 净利润(亿)"""
    return float(shizhi)/float(jll)
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
def IsWhiteHorse(code):
    """白马股"""
    ths = THS.getInstance()
    df_gaiyao = ths.df_gaiyao
    s = df_gaiyao[df_gaiyao['code'] == code]['概念强弱排名'].tolist()[0]
    return s.find('白马股')>=0
def IsLanChouGu(code):
    """蓝筹股"""
    ths = THS.getInstance()
    df_gaiyao = ths.df_gaiyao
    s = df_gaiyao[df_gaiyao['code'] == code]['财务分析'].tolist()[0]
    return s.find('蓝筹')>=0
def IsChuanYeBan(code):
    return code[0] == '3'

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
    unittest.main()
if __name__ == "__main__":
    main()
    print('end')
