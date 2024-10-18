#coding:utf8

"""pytdx test
通达信网络在8：45-9：05可能访问不了
"""
from __future__ import print_function
import sys
from pytdx.hq import TdxHq_API as tdx
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx
import pandas as pd
import time
from autoxd import stock

g_api = None
def create():
    global g_api;
    if g_api == None:
        g_api = tdx()
        #from connect.cfg
        ip = '123.125.108.219'
        b = g_api.connect(ip, 7709)
        assert b
    return g_api

def getFive(code, count=800):
    """return: df"""
    api = create()
    market = stock.IsShangHai(code)
    for i in range(3):
        data = api.get_security_bars(category=0, market=market, code=code, start=0, count=count)
        data = api.to_df(data)
        if DataIsValid(data):
            break
        time.sleep(5)
    if not DataIsValid(data):
        print("tdx get data failed")
        raise ValueError("tdx data error")
    if len(data) == 0:
        return pd.DataFrame([])
    df = data[['open','close', 'high','low','vol']]
    df.columns = list('ochlv')
    df.index = pd.DatetimeIndex(data['datetime'])
    return df

def DataIsValid(df:pd.DataFrame):
    if df.shape == (1,1) and df.iloc[0][0] is None:
        return False
    return True

def getHisdat(code):
    api = create()
    market = stock.IsShangHai(code)
    for i in range(3):
        data = api.get_security_bars(category=9, market=market, code=code, start=0, count=800)
        data = api.to_df(data)
        if DataIsValid(data):
            break
        time.sleep(5)
        
    if not DataIsValid(data):
        raise ValueError("tdx data error")
    df = data[['open','close', 'high','low', 'vol']]
    df.columns = list('ochlv')
    df.index = pd.DatetimeIndex(data['datetime'])
    return df

    
def test():
    print(getFive(jx.HWDQ禾望电气))
    
if __name__ == "__main__":
    
    test()

