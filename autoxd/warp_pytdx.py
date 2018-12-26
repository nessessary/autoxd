#coding:utf8

"""pytdx test"""
from __future__ import print_function
import sys
from pytdx.hq import TdxHq_API as tdx
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx
from autoxd import stock
import pandas as pd

g_api = None
def create():
    global g_api;
    if g_api == None:
        g_api = tdx()
        b = g_api.connect('119.147.212.81', 7709)
        if not b:
            #换一个ip， list见通达信目录的connect.cfg
            g_api.connect('202.130.235.189', 7709)
    return g_api

def getFive(code):
    """return: df"""
    api = create()
    market = stock.IsShangHai(code)
    data = api.get_security_bars(category=0, market=market, code=code, start=0, count=800)
    data = api.to_df(data)
    df = data[['open','close', 'high','low']]
    df.columns = list('ochl')
    df.index = pd.DatetimeIndex(data['datetime'])
    return df
def getHisdat(code):
    api = create()
    market = stock.IsShangHai(code)
    data = api.get_security_bars(category=9, market=market, code=code, start=0, count=800)
    data = api.to_df(data)
    df = data[['open','close', 'high','low']]
    df.columns = list('ochl')
    df.index = pd.DatetimeIndex(data['datetime'])
    return df
def test():
    print(getFive(jx.HWWH))
    
#test()

