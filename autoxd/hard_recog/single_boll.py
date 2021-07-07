#coding:utf8

"""
遍历boll
输出符合技术指标组合的结果
"""
from autoxd import stock, ui, myredis, agl, sign_observation
from autoxd.cnn_boll.judge_boll_sign import getBolls
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd.myenum import MYCOLS_NAME as colname
from autoxd.cnn_boll.judge_boll_sign import g_scope_len
import pylab as pl
import pandas as pd
import random
import numpy as np
from collections import Iterator, Iterable
from autoxd.pypublish import publish
pl = publish.Publish(is_clear_path=True)

#需要处理的字段
#col_names = [""]
#cols = ["close_zz_0", "close_zz_1", "boll_low_zz_0", "boll_low_zz_1", "boll_w"]

class calc_property:
    close_zz_0 = np.nan
    close_zz_1 = np.nan
    boll_low_zz_0 = np.nan
    boll_low_zz_1 = np.nan
    boll_w = np.nan
    adx = 0
    boll_x = 0   # x, 时间周期
    boll_y = 0.1    # (mid-v)/(mid-low)

class recorg_boll:
    def __init__(self, data_boll):
        pass

def get_x_boll(close, boll):
    """通过当前的价格y回溯获取boll同样y值的x;
    return 当前价格到boll线的水平距离"""
    def is_eq(a, b):
        return a+0.01>b and a-0.01>b
    for i in range(len(boll)-1,-1,-1):
        if is_eq(boll[i], close):
            return len(boll) - i
    return -1
    
def get_y_boll(close, boll, boll_mid):
    """return: (y0, y1)"""
    mid = boll_mid[-1]
    v = boll[-1]
    return (mid-close)/(mid-v)

def gen_random_int(a, b):
    """在ab之间产生一个随机数"""
    return random.randint(a, b)

def load_data(code):
    df = stock.getFiveHisdatDf(code, method='tdx')
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)
    
    df['upper'] = upper
    df['middle'] = middle
    df['lower'] = lower
    
    highs = pd.Series(df[colname.high]).values
    lows = pd.Series(df[colname.low]).values
    closes = pd.Series(df[colname.close]).values
    adx, pdi, mdi = stock.TDX_ADX2(highs, lows, closes)
    
    df[colname.adx] = adx
    df[colname.pdi] = pdi
    df[colname.mdi] = mdi
    rsi = stock.RSI(closes)
    df[colname.rsi] = rsi
    
    return df

class boll_params:
    h1 = 0  # close离mid的垂直距离
    h2 = 0  # close离low的垂直距离
    
def load_data_at_point(df, index, length):
    return df.iloc[index: index+length]
    
def recorg(pl, df_boll):
    sign = 0
    df = df_boll
    if 0: df = pd.DataFrame
    #计算参数
    
    #输出原始图片
    #closes, boll_up, boll_mid, boll_low = df[['c', 'upper','middle', colname.boll_lower]].to_list()
    closes = df['c'].values
    boll_up = df[colname.boll_upper].values
    boll_mid = pd.Series(df[colname.boll_middle]).values
    boll_low = pd.Series(df[colname.boll_lower]).values
    
    #转zz
    zz_boll_up = stock.ZigZag(boll_up)
    zz_boll_mid = stock.ZigZag(boll_mid)
    zz_boll_low = stock.ZigZag(boll_low)
    zz_close = stock.ZigZag(closes, percent=5)
    zz_close_short = stock.ZigZag(closes, percent=.5)
    adx = df[colname.adx].values[-1]
    bollw = stock.BOLLW(boll_up, boll_low, closes)
    
    #数值判断
    
    obj = boll_params()
    obj.h1 = closes[-1] - boll_mid[-1]
    obj.h2 = closes[-1] - boll_low[-1]
    boll_y = get_y_boll(closes[-1], boll_low, boll_mid)
    techs = calc_property()
    y1,y2 = stock.analyzeZZ(zz_close)
    techs.close_zz_0 = "%.3f"%y1
    techs.close_zz_1 = "%.3f"%y2
    y1,y2 = stock.analyzeZZ(zz_boll_low)
    techs.boll_low_zz_0 = "%.3f"%y1
    techs.boll_low_zz_1 = "%.3f"%y2
    techs.boll_w = "%.3f"%bollw[-1]
    techs.adx = "%.3f"%adx
    techs.boll_x = get_x_boll(closes[-1], boll_low)
    techs.boll_y = boll_y
    techs.boll_y = "%.2f%%"%(techs.boll_y*100)
    sign = False
    select = 1
    #第二次机会
    if sign_observation.assemble(1, obj.h1 <0, adx>25, bollw[-1]>0.2, boll_y<0.2, techs.boll_x>10):
        sign = True
    #第一次机会
    if sign_observation.assemble(0, obj.h1 <0, adx>25, bollw[-1]>0.2, float(techs.boll_low_zz_1)<-0.1, 
                                 techs.boll_x>1, boll_y>0.8):
        sign = True

    #输出判断
    if sign:
        
        pl:publish.Publish
        pl.insertHtml("<tr><td>")
        ui.drawBoll(pl, closes, boll_up, boll_mid, boll_low)
        pl.insertHtml("</td><td>")
        
        ui.DrawZZ(pl, zz_boll_up, is_append=ui.draw_style.head)
        ui.DrawZZ(pl, zz_boll_mid, is_append=ui.draw_style.mid)
        ui.DrawZZ(pl, zz_close, c='b', is_append=ui.draw_style.mid)
        ui.DrawZZ(pl, zz_close_short, c='g', is_append=ui.draw_style.mid)
        ui.DrawZZ(pl, zz_boll_low, is_append=ui.draw_style.end)
        pl.insertHtml("</td><td>")
        vals = agl.get_print_object(techs)
        pl.insertHtml(vals)
        pl.insertHtml("</td></tr>")
    return sign

class boll_data_Iterator(Iterator):
    def __init__(self, code):
        df = load_data(code)
        self.df = df
        self.index = g_scope_len
    def __next__(self):
        if self.index == len(self.df):
            raise StopIteration        
        index = self.index
        df = self.df[index: index+g_scope_len]
        self.index += 1
        return df
    def __len__(self):
        return len(self.df) - g_scope_len
class boll_data_Iterable(Iterable):
    def __init__(self, code):
        self.code = code
    def __iter__(self):
        return boll_data_Iterator(self.code)
    def __len__(self):
        return len(boll_data_Iterator(self.code))

#def get_data(code):
    #"""
    #return: df ['o', 'c', 'h', 'l', 'upper', 'middle', 'lower']"""
    ##df = load_data(code)
    ##myredis.delkey(myredis.gen_keyname(__file__, get_data))
    #df = myredis.createRedisVal(myredis.gen_keyname(__file__, get_data),
                                #lambda: load_data(code)).get()
    #size = len(df)
    #if size > g_scope_len:
        #index = gen_random_int(0, size - g_scope_len)
        #df = load_data_at_point(df, index, length=g_scope_len)
    #return df

def get_data_rand(code):
    """随机在结果集中取一个数据
    return : df
    """
    df = load_data(code)
    size = len(df)
    assert(size > g_scope_len)
    index = gen_random_int(g_scope_len, size - g_scope_len)
    df = load_data_at_point(df, index, length=g_scope_len)
    return df

count = 0
g_c2 = 0    #total_count
def run(code):
    global count
    global g_c2
    df_data = load_data(code)
    size = len(df_data)
    if size > g_scope_len:
        #index = gen_random_int(0, size - g_scope_len)
        #index = 148
        for index in range(148, size - g_scope_len):
            df = load_data_at_point(df_data, index, length=g_scope_len)
            g_c2 += 1
            if recorg(pl,df):
                count += 1
    else:
        raise Exception('长度太短') #在调试中会直接停在这里
    
def main():
    codes = [jx.NDSD宁德时代, jx.PAYH平安银行]
    codes = stock.get_codes(stock.myenum.randn, n=10)
    #codes = codes[:10]
    pl.myimgs += "<table>"
    for code in codes:
        pl.myimgs += "<tr><td><table>"
        run(code)
        pl.myimgs += "</table></td></tr>"
    pl.myimgs += "</table>"
    print(g_c2, count)
    
if __name__ == "__main__":
    main()    
    pl.publish()    
    