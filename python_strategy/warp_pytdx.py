#coding:utf8

"""pytdx test"""

from pytdx.hq import TdxHq_API as tdx
import stock_pinyin as jx
import stock
import pandas as pd

g_api = None
def create():
    global g_api;
    if g_api == None:
        g_api = tdx()
        g_api.connect('119.147.212.81', 7709)
    return g_api

def getFive(code):
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
    print getFive(jx.HWWH)
    
#test()

