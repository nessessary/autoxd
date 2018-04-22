#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os
import numpy as np
import pandas as pd
import sys, unittest, copy
import pylab as pl
import stock, agl, help, ui, myredis, myenum

"""每次分时获取后， 把分时转换为5min线，保存到redis里
由分时下载调用play.bat
"""
def showBoll(closes):
    """显示布林线"""
    upper, middle, lower = stock.BOLL(closes)
    ui.DrawTs(pl, closes, high=upper, low=lower)
def genOne(code):
    #print code
    #先清理5分钟分时redis
    stock.FenshiCodeCache(code).delKey()
    try:
        #通过日线来取最近的5天
        df_hisdat = stock.getHisdatDataFrameFromRedis(code)
        df_hisdat = df_hisdat.tail()
        start_day = agl.datetime_to_date(df_hisdat.index[0])
        end_day = agl.datetime_to_date(df_hisdat.index[-1])
        
        df_fenshi = stock.getFenshiDfUseRedis(code, start_day, end_day).dropna()
    except:
        return
    stock.FenshiCodeCache(code).set(df_fenshi)
    #print df_fenshi
    #closes = np.array(df_fenshi['p'])
        #showBoll(closes)
    
def getAllFenshi():
    
    for code in stock.get_codes():
        genOne(code)
if 0: getFiveMinFenshiFromRedis = pd.DataFrame
def getFiveMinFenshiFromRedis(code):
    """获取5分钟分时线
    return: df"""
    return stock.FenshiCodeCache(code).getBankuaiFenshiZhishu().resample("5min")
def getOneMinFenshiFromRedis(code):
    """获取1分钟分时线
    return: df"""
    return stock.FenshiCodeCache(code).getBankuaiFenshiZhishu()
    
class mytest(unittest.TestCase):
    def test1(self):
        self.assertFalse(0)
    def testCreate(self):
        codes = stock.get_codes(myenum.randn, 10)
        codes = [u'002072']
        for code in codes:
            genOne(code)
    def _test_fenshi_redis(self):
        """取一个个股的redis， 看下日期"""
        end_day = agl.CurDay()
        start_day = help.MyDate.s_Dec(end_day, -15)
        code = u'600100'
        
        #取一个值
        df_fenshi = getFiveMinFenshiFromRedis(code)
        df_fenshi_day = df_fenshi.resample('D').dropna()
        self.assertEqual(len(df_fenshi_day), 5)
        d = agl.datetime_to_date(df_fenshi_day.index[-1])
        self.assertEqual(stock.getKlineLastDay(), d)
        
        df = stock.LiveData().getFiveMinHisdat(code)
        print df
    
def main(args):
    a = agl.tic_toc()
    print 'save fenshi to redis, predict 1 hour'
    getAllFenshi()
    #print "end"
    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
