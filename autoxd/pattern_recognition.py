#-*- coding:utf-8 -*-

"""形态识别, 使用传统方式, 不使用机器学习"""
from __future__ import print_function
import sys, os
import numpy as np
import pandas as pd
import stock, ui
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx
import pylab as pl
import math
import myredis
import warp_pytdx as tdx
from pypublish import publish

def horizontal(df, zhouqi_zhenfu=[45,1.2], greater=False):
    """只扫描50个周期, 振幅大于5%, 最后10个周期在1%之间波动, 且整体小于1.5%
    df: 5分钟k线
    zhouqi_zhenfu: [周期, 振幅]
    greater : 是否大于当前振幅
    return: bool, (h,l, left,right), h,l为值,left,right为索引"""
    r = True
    zhouqi, zhenfu = zhouqi_zhenfu
    #一天是48, 48+24=72
    left,right=-zhouqi,-1
    df1 = df[left:]
    h, l = np.max(df1['h']), np.min(df1['l'])
    cur_zhengfu = abs(stock.ZhengFu(h, l))
    #print cur_zhengfu
    if greater:
        r = r and cur_zhengfu > zhenfu/100
    else:
        r = r and cur_zhengfu < zhenfu/100
    return r, (h,l, left, right)

def Combo(df):
    v1 = ([75, 2.5], True)
    v2 = ([45, 1.5], False)
    bFind, (h,l,left,right) = horizontal(df, v1[0], v1[1])
    if bFind:
        bFind, (h,l,left,right) = horizontal(df, v2[0], v2[1])
    return bFind, (h,l,left,right)
    
class Statistics:
    @staticmethod
    def pearson(x, y):
        """皮尔逊相关性分析
        x: np.ndarray
        y: 同x
        return: float 0~1
        """
        def pearson_np(x, y):
            np.corrcoef
        pass
        #计算特征和类的平均值

## ###############
## 曲线匹配        
#def calcMean(x,y):
    #sum_x = sum(x)
    #sum_y = sum(y)
    #n = len(x)
    #x_mean = float(sum_x+0.0)/n
    #y_mean = float(sum_y+0.0)/n
    #return x_mean,y_mean
##计算Pearson系数
#def calcPearson(x,y):
    #"""手工计算person"""
    #x_mean,y_mean = calcMean(x,y)	#计算x,y向量平均值
    #n = len(x)
    #sumTop = 0.0
    #sumBottom = 0.0
    #x_pow = 0.0
    #y_pow = 0.0
    #for i in range(n):
        #sumTop += (x[i]-x_mean)*(y[i]-y_mean)
    #for i in range(n):
        #x_pow += math.pow(x[i]-x_mean,2)
    #for i in range(n):
        #y_pow += math.pow(y[i]-y_mean,2)
    #sumBottom = math.sqrt(x_pow*y_pow)
    #p = sumTop/sumBottom
    #return p
    
def pearson(x, y):
    assert(len(x) == len(y))
    return np.corrcoef(x, y)[0,1]

#识别boll上轨
def recog_boll(pl, report_list):
    from autoxd import stock_pinyin as jx
    codes = [jx.HCGD, jx.HYGY]
    codes = stock.get_codes(stock.myenum.randn, 2)
    #import tushare_handle as th

    up1 = get_upper(codes[0])
    up2 = get_upper(codes[1])
    #print(len(up1), len(up2))

    n = 30
    a = up1[-n:]
    b = up2[-n:]
    a = stock.GuiYiHua(a-np.min(a))
    b = stock.GuiYiHua(b - np.min(b))
    v = pearson(a,b)
    df = pd.DataFrame(a)
    df['2'] = b
    df.plot()
    pl.show()
    fimg = pl.get_CurImgFname()
    report_list.append([v, fimg])

def recog_history_boll(pl, x, p, code):
    """在历史数据中找到相似的曲线
    x : np.ndarray 基准曲线
    p : float pearson相似度
    """
    df = stock.getFiveHisdatDf(code, method='local')
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)    
    df['upper'] = upper
    df = df[-1000:]
    #upper = upper[np.isnan(upper) == False]
    upper = df['upper'].values
    n = 30
    report_list = []
    x = stock.GuiYiHua(x - np.min(x))
    for i in range(0,len(upper)-30, 2):
        y = upper[i:i+n]
        assert(len(y)== 30)
        y = stock.GuiYiHua(y - np.min(y))
        pearson_v = pearson(x, y)
        if pearson_v > p:
            df2 = pd.DataFrame(x)
            df2['2'] = y
            df2.plot()
            pl.show()
            pl.close()
            fimg = pl.get_CurImgFname()
            report_list.append([code, pearson_v, df.index[i], fimg])
    return report_list

def get_boll_up_base():
    """获取一个用来作为标准的曲线
    return : np.ndarray
    """
    code = jx.HCGD
    t = '2018-12-3 10:30:00'
    t = '2018-11-30 10:00:00'
    key = myredis.gen_keyname(__file__, get_boll_up_base)
    df = myredis.createRedisVal(key, lambda : stock.getFiveHisdatDf(code, method='tdx')).get()
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)    
    df['upper'] = upper
    df = df[t:]
    df = df[df.index[20]:]
    df = df[:df.index[29]]
    #ui.DrawTs(pl, df['upper'].values)
    #pl.show()
    return df['upper'].values

def get_boll_lower_base():
    """获取一个向下的曲线
    return: np.ndarray
    """
    #翻转up
    na = get_boll_up_base()
    na1 = na - np.min(na)
    na2 = np.zeros(len(na)) - na1 + np.min(na)
    if 0:
        print(na1)
        print(len(na), len(na1))
        print(na2)
        df = pd.DataFrame(na)
        df['2'] = na2
        df.plot()
        pl.show()
    return na2
#
# ##################

class Recognize_boll(object):
    """识别形态"""
    def __init__(self, base_boll_up, df):
        """
        :base_boll_up: np.ndarray 基准线， 用来作为判断的标准:
        :df: 当前时刻的5分钟线, 用来与基准进行比对:
        """
        assert('boll_up' in df.columns)
        df = df[-len(base_boll_up):]
        self.df = df
        self.base = base_boll_up
    def _calc_beta_up(self):
        """计算closes与boll_up的beta"""
        series = self.df['c'] - self.df['boll_up']
        series = series/ self.df['boll_mid']
        return np.array(series)

    def _calc_beta_lower(self):
        """计算closes与boll_up的beta"""
        series = self.df['boll_lower'] - self.df['c'] 
        series = series/ self.df['boll_mid']
        return np.array(series)

    def is_matched(self):
        """与基准线对比，并符合
        return: bool
        """
        n = 0.8
        x = self.base
        y = self.df['c'].values
        return pearson(x, y) > n
    
    def sign(self):
        b = self._calc_beta_up()
        b2 = self._calc_beta_lower()
        if b[-1]>-0.005 and self.is_matched():
            return 1
        if b2[-1]>-0.005 and self.is_matched():
            return -1
        return 0
    @staticmethod
    def test():
        pl = publish.Publish()
        base_boll_up = get_boll_up_base()
        base_boll_lower = get_boll_lower_base()
        def get_data():
            code = jx.HCGD
            df = tdx.getFive(code)
            return df
        key = myredis.gen_keyname(__file__, Recognize_boll.test)
        df = myredis.createRedisVal(key, get_data).get()
        df = stock.TDX_BOLL_df(df)
        for i in range(60, len(df)):
            df_cur = df[ :i]
            c = Recognize_boll(base_boll_up, df_cur)
            c2 = Recognize_boll(base_boll_lower, df_cur)
            b = c._calc_beta_up()
            b2 = c._calc_beta_lower()
            #if c2.is_matched():
                #print(b2)
            if abs(c.sign())>0 or abs(c2.sign())>0:
                df_cur = df_cur[['c','boll_up', 'boll_mid', 'boll_lower']]
                df_cur.index = range(len(df_cur))
                df_cur.plot()
                pl.show()

import unittest
class mytest(unittest.TestCase):
    def _test1(self):
        print('test')
    def _test_horizontal(self):
        code = jx.THS
        df = stock.getFiveHisdatDf(code)
        df = df['2017-5-1':]
        df = df['2017-11-1':]
        rects = []
        bHit = False
        for i in range(100, len(df), 5):
            cur_df = df[:i]
            #bFind, (h,l,left,right) = horizontal(cur_df)
            bFind, (h,l,left,right) = Combo(cur_df)
            if bFind:
                bHit = True
                print(cur_df.index[-1], bFind, (h,l,left,right))
                left = i+left
                right = i
                rects.append((h,l,left,right))
        if bHit:                
            ui.drawKlineUseDf(pl, df, rects)
    def _test_fenshi_horizontal(self):
        code = jx.THS
        df = stock.getFenshiDfUseRedis(code, start_day='2017-12-1', end_day='2017-12-5')
        ui.drawFenshi(pl, df)
    def _test_person(self):
        a = np.array([1,2,3, 4, 1,7])
        b = np.array([2,3,1, 4, 2, 2])
        print(calcPearson(a, b))
        print(np.corrcoef(a, b))
        from scipy.stats.stats import pearsonr  
        corr, p_value = pearsonr(a, b)
        print(corr)        
    def _test_recog_boll(self):
        from pypublish import publish
        pl = publish.Publish()
        from policy_report import df_to_html_table
        report = []
        for i in range(200):
            try:
                recog_boll(pl, report)
            except:
                continue
        df = pd.DataFrame(report)
        df = df[df[df.columns[0]]>0.7]
        pl.reset(df_to_html_table(df))
        pl.publish()
        
def test_recog_history_boll():
    from pypublish import publish
    pl = publish.Publish(explicit=True)
    code = jx.ZCKJ.b
    def get_local_codes():
        data_path = 'cnn_boll/datasources/'
        return np.array([ str(f).split('.')[0] for f in os.listdir(data_path)])
    from sklearn.utils import shuffle
    key = myredis.gen_keyname(__file__, test_recog_history_boll)
    codes = myredis.createRedisVal(key, get_local_codes).get()
    code = shuffle(codes)[0]
    #ui.DrawTs(pl, x)
    #x = get_boll_up_base()
    x = get_boll_lower_base()
    p= 0.75
    #report = ['init', pl.get_CurImgFname()]
    report = recog_history_boll(pl, x, p, code)        
    pl.RePublish(report)
    
if __name__ == '__main__':
    #unittest.main()
    #test_recog_history_boll()
    #get_boll_up_base()
    Recognize_boll.test()
    #get_boll_lower_base()