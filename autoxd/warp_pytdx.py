#coding:utf8

"""pytdx test
通达信网络在8：45-9：05可能访问不了
"""
from pytdx.hq import TdxHq_API as tdx
from autoxd.pinyin import stock_pinyin3 as jx
import pandas as pd
import time
from autoxd import stock

g_api = None

# 可用的公共行情服务器列表 (来源: pytdx.config.hosts.hq_hosts, 2026-09-10验证可用)
HQ_HOSTS = [
    ('59.36.5.11', 7709),
    ('117.34.114.13', 7709),
    ('117.34.114.14', 7709),
    ('117.34.114.15', 7709),
    ('117.34.114.16', 7709),
    ('117.34.114.17', 7709),
    ('117.34.114.18', 7709),
    ('117.34.114.20', 7709),
    ('117.34.114.27', 7709),
]

def _find_working_host(hosts, test_code='603063', timeout=5):
    """从候选服务器中挑一个能返回有效数据的"""
    market = stock.IsShangHai(test_code)
    for ip, port in hosts:
        try:
            api = tdx()
            api.connect(ip, port, time_out=timeout)
            data = api.get_security_bars(category=0, market=market,
                                         code=test_code, start=0, count=10)
            if data:
                return ip, port
        except Exception:
            continue
    return None

def create():
    global g_api
    if g_api is None:
        addr = _find_working_host(HQ_HOSTS)
        if addr is None:
            raise ConnectionError("no available tdx hq host")
        ip, port = addr
        g_api = tdx()
        g_api.connect(ip, port)
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
    #指数必须用get_index_bars, get_security_bars对指数返回损坏数据
    is_index = code[:3] == '399' or code == '999999'
    for i in range(3):
        if is_index:
            data = api.get_index_bars(category=9, market=market, code=code, start=0, count=800)
        else:
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
