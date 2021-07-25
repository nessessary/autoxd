#coding:utf8

"""pytdx test"""
from __future__ import print_function
import sys
from pytdx.hq import TdxHq_API as tdx
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx
import pandas as pd
import time

g_api = None
def create():
    global g_api;
    if g_api == None:
        g_api = tdx()
        ip = '202.130.235.189'
        #ip = '140.207.241.60'
        b = g_api.connect(ip, 7709)
        if not b:
            #换一个ip， list见通达信目录的connect.cfg
            g_api.connect('119.147.212.81', 7709)
    return g_api

def getFive(code):
    """return: df"""
    from autoxd import stock
    api = create()
    market = stock.IsShangHai(code)
    for i in range(3):
        data = api.get_security_bars(category=0, market=market, code=code, start=0, count=800)
        data = api.to_df(data)
        if DataIsValid(data):
            break
        time.sleep(5)
    if not DataIsValid(data):
        print("tdx get data failed")
        raise ValueError("tdx data error")
    df = data[['open','close', 'high','low','vol']]
    df.columns = list('ochlv')
    df.index = pd.DatetimeIndex(data['datetime'])
    return df

def DataIsValid(df:pd.DataFrame):
    if df.shape == (1,1) and df.iloc[0][0] is None:
        return False
    return True

def getHisdat(code):
    from autoxd import stock
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
    print(getFive(jx.HWWH))
    
#test()

