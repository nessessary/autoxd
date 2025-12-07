#coding:utf8
import efinance as ef
import pandas as pd
from autoxd.pinyin import stock_pinyin3 as jx

def get_5min_kline(stock_code, start_date, end_date):
    df = ef.stock.get_quote_history(stock_code, klt=5, start_date=start_date, end_date=end_date)
    return df

def run():
    stock_code = jx.DSFS第四范式hk
    start_date = '2025-01-01'
    end_date = '2025-02-05'
    
    df = get_5min_kline(stock_code, start_date, end_date)
    df.to_csv('5min.csv')
    print(df[['日期', '开盘', '收盘', '最高', '最低']])

def get_hq(code):
    # 获取港股的 K 线数据
    stock_code = code  # 示例：腾讯控股的港股代码
    #data = ef.stock.get_quote_history(stock_code)
    #print(data.iloc[-1]['收盘'])
    #df = ef.stock.get_realtime_quotes(['港股'])
    #print(df)
    df = ef.stock.get_latest_quote(code)
    #print(df[[df.columns[2], df.columns[3]]])
    print(df.loc[0, df.columns[2]], df.loc[0, df.columns[3]], end=" ")

for c in [ '兴森科技','华正新材']:
    get_hq(c)
    
    