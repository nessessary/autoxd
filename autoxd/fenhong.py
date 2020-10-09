#coding:utf8
"""把分红表从ths f10里独立出来 datas\fenhong.csv
同时生成股本变更表 datas\astockchange.csv
"""
from autoxd import warp_pytdx
from autoxd import stock, agl
from autoxd.pinyin import stock_pinyin3 as jx
import pandas as pd
import numpy as np
import copy, os

class enum:
    fname_fenhong = 'datas/fenhong.csv'
    fname_astockchange = 'datas/astockchange.csv'
    astockchange_col = '变动后流通A股(股)'

def _convert_fenhong(df):
    """转换分红表格式为数据格式
    分红记录 (说明, 股， 派现，除权日)
    return: df columns('股，现金, 日期, code')"""
    cloumns = []
    #获取分红表
    df_fenhong = pd.DataFrame([])#股，现金, 日期
    for i in range(len(df)):
        code = df.iloc[i]['code']
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
                df_fenhong = pd.concat([df_fenhong, pd.DataFrame([gu, money, date, code]).T])
    return df_fenhong    

def _convert_stockchange(df):
    row = df.iloc[0]
    row['code'] = 'code'
    df = df[df[0]!='变动日期']  # 删除col行
    #2015年之前的不记录
    year = '2015-1-1'
    df.index = pd.DatetimeIndex(df[df.columns[0]])
    df = df[df.index > year]
    df.columns = row
    df = df[1:]
    df = df.drop([df.columns[1],df.columns[2], df.columns[4], df.columns[-1]], axis=1) # 删除不要的列
    # 相同的记录只保存最新的一条
    indexs = np.array(range(len(df)), dtype=bool)
    indexs[:] = True
    row_pre = df.iloc[0]
    for i in range(len(df)):
        row = df.iloc[i]
        if row[1:-1].tolist() != row_pre[1:-1].tolist():
            indexs[i] = True
        else:
            indexs[i] = False
        row_pre = row
    df = df[indexs]
    return df

def _dump():
    import stock as mystock
    ths = mystock.createThs()
    df_fenhong = ths.getDf(-1)
    df_fenhong = _convert_fenhong(df_fenhong)
    fname = enum.fname_fenhong
    df_fenhong.to_csv(fname,index=False)
    
    #历次股本变动
    df_stockchange = ths.getDf(3)
    df_stockchange = _convert_stockchange(df_stockchange)
    fname = enum.fname_astockchange
    df_stockchange.to_csv(fname, index=False)
    
class FenHongTable:
    def __init__(self):
        fname = enum.fname_fenhong
        fname = os.path.join(os.path.dirname(__file__), fname)
        df_fenhong = pd.read_csv(fname)
        
        df_fenhong.index = pd.DatetimeIndex(df_fenhong[df_fenhong.columns[2]])
        df_fenhong.columns = range(len(df_fenhong.columns))
        self.df = df_fenhong

    def getOne(self, code):
        df_fenhong = self.df
        df_fenhong = df_fenhong[df_fenhong[df_fenhong.columns[-1]] == int(code)]
        df_fenhong = df_fenhong[df_fenhong.columns[:-1]]
        return df_fenhong

class AStockChangeTable:
    def __init__(self):
        fname = enum.fname_astockchange
        fname = os.path.join(os.path.dirname(__file__), fname)
        df = pd.read_csv(fname)
        df.index = pd.DatetimeIndex(df[df.columns[0]])
        self.df = df
        
    def getOne(self, code):
        df = self.df
        df = df[df['code']==int(code)]
        return df
    
def test_fuquan():
    code = jx.THS
    code = jx.KDXF
    df_close = stock.getHisdatDf(code, method='tushare', is_fuquan=False, is_Trunover=False)
    df_close2 = copy.deepcopy(df_close)
    
    table = FenHongTable()
    df_fenhong = table.getOne(code)
    print(df_fenhong)
    df = stock.calc_fuquan_use_fenhong(df_close, df_fenhong)
    agl.print_df(df)
    # 复权后应该是不相等
    print(df['c'][:-1].tolist() == df_close2['c'][:-1].tolist())
 
def test_astockchange():
    code = jx.THS
    df = stock.getHisdatDf(code, method='tdx', is_fuquan=False)
    df = df['2018-4-11':]
    print(df['v'].head())
    df = stock.getHisdatDf(code, method='tushare', is_fuquan=False)
    print(df['v'].head())
    table = AStockChangeTable()
    df_stockchange = table.getOne(code)
    df = stock.convertVolToStockTrunover(df, df_stockchange)
    print(df)
        
if __name__ == "__main__":
    #_dump()
    #test_fuquan()
    test_astockchange()