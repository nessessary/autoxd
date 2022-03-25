#coding:utf8

"""设计自有的adx判断， 
1. 根据量价，把价格线转换为直方图， 然后聚类出一个中心点作为水平线,  (先不用成交量， 只使用价格来聚类)
2. 计算当前点与均线及水平线的距离
3. 计算boll轨的斜率
4. boll宽度及放大状态, ( 或者用自有adx代替)
"""

from autoxd.stock import getFiveHisdatDf, ZigZag
from autoxd import stock, agl
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd.agl import ClustList2, float_to_2
from autoxd import ui, myredis, mysql
import pylab as pl
from autoxd.hard_recog.single_boll import colname, pd, get_data_rand
from autoxd.hard_recog.single_boll import boll_data_Iterable as mydata
from autoxd.pypublish import publish
import numpy as np
import os


#pl = publish.Publish()

class find_trade_pos_probability(object):
    """遍历各参数的范围, 计算在各个范围出现的概率"""
    pass

def get_cols():
    return ["close", "boll_mid", "boll_h", "boll_v", "boll_zz_slope", "boll_w", "adx", "pdi", "mdi", "rsi", "close_clust1", "close_clust2"]

def calc_boll_tech(df):
    """计算boll相关技术指标
    返回均为单值
    return: close, boll_mid, boll_h, boll_v, boll_zz_slope, boll_w, adx, pdi, mdi, rsi, close_clust1, close_clust2
    """
    #code = jx.HLE
    #df = get_data(code)
    #df = myredis.createRedisVal(myredis.gen_keyname(__file__, getCenterPoint), lambda: get_data(code)).get()
    closes = df['c'].values
    boll_up = df[colname.boll_upper].values
    boll_mid = df[colname.boll_middle].values
    boll_low = df[colname.boll_lower].values
    adx = pd.Series(df[colname.adx]).values
    pdi = pd.Series(df[colname.pdi]).values
    mdi = pd.Series(df[colname.mdi]).values
    rsi = pd.Series(df[colname.rsi]).values    
    boll_w = (boll_up - boll_low)/boll_mid*100
    
 
    #计算斜率
    boll_z = boll_up if closes[-1]>boll_mid[-1] else boll_low
    zz = ZigZag(boll_z, percent=0.01)
    zz = zz[-2:]
    #if len(zz) < 2:
        #return False
    v_slope = slope(zz)
    #print(v_slope)
    v_slope = float_to_2(v_slope)
    
    # 计算close到左侧boll线的距离
    #   \
    #    \
    #     \             *
    #      \   
    #已知直线两点, 单点point， 求点到直线的水平距离和垂直距离
    def calc_distance(x1,y1, x2,y2, x3,y3):
        """x3,y3为point
        return: h, v
        """
        #设x1,y1为原点
        #y = kx
        k = (y2-y1)/(x2-x1)
        if k < 0.001:
            return 0, 0
        y3_1 = k * x3
        v = y3-y3_1
        x3_1 = y3/k
        h = x3- x3_1
        return h, v
    if len(zz) >=2:
        x1,y1 = zz[-2]
        x2,y2 = zz[-1]
        x3 = len(closes)-1
        y3 = closes[-1]
        #调整单位为百分比, x1,y1作为0，0原点
        y3 = y3/y1
        y2 = y2 /y1
        y1 = y1/y1
        x3 = x3-x1
        x2 = x2-x1
        x1 = x1-x1
        y3 = y3 - y1
        y2 = y2 - y1
        y1 = y1 - y1
        h,v = calc_distance(x1, y1, x2, y2, x3, y3)
        boll_h = float(float_to_2(h))
        boll_v = float(float_to_2(v*100))
    else:
        boll_h = np.nan
        boll_v = np.nan
    
    #计算聚类点
    if len(closes)>2:
        ary, line = ClustList2(2, closes)
        #ui.drawTsAndHlines(pl, closes, ary[0,1], ary[1,1])
        close_clust1 = ary[0,1]
        close_clust2 = ary[1,1]    
    else:
        close_clust1 = np.nan
        close_clust2 = np.nan
    boll_zz_slope = float(v_slope)
    
    def draw():
        lines = [close_clust1, close_clust2]
        
        #绘制
        pl.figure
        pl.subplot(211)
        pl.plot(closes)
        pl.plot(boll_up)
        pl.plot(boll_mid)
        pl.plot(boll_low)
        pl.plot(zz[:,0], zz[:,1])
        for l in lines:
            ui.DrawHLine(pl, l, len(closes))
        pl.legend([v_slope, boll_h, boll_v],  loc='upper left')
        pl.subplot(212)
        pl.plot(adx)
        pl.plot(pdi)
        pl.plot(mdi)
        pl.plot(rsi)
        pl.legend([colname.adx, colname.pdi, colname.mdi, colname.rsi], loc='upper left')        
        pl.show()
        pl.close()
    #draw()    
    return closes[-1], boll_mid[-1], boll_h, boll_v, boll_zz_slope, boll_w[-1], adx[-1], pdi[-1], mdi[-1], rsi[-1],\
           close_clust1, close_clust2



def slope(line):
    """ 计算线条的斜率
    index与price_percent的单位需要统一, index默认最大为30, price_percent的极限为30%
    line: [(index, price_percent),(index2,price_percent2)]
    return: float
    """
    if len(line) != 2:
        return np.nan
    x1, y1 = line[0]
    x2, y2 = line[1]
    y_mid = (y1+y2)/2
    y1 = (y1/y_mid)*100
    y2 = (y2/y_mid)*100
    #先统一单位, index不用变， percent本来是100%, 按30%的范围进行变化
    unit_change = 1.0/0.3
    
    #k=(y2-y1)/(x2-x1)
    k = (y2-y1)*unit_change/(x2-x1)
    return k

def find_trade_pos(df, df_result, code, index):
    """
    return: df_result, bool
    """
    close, boll_mid, boll_h, boll_v, boll_zz_slope, boll_w, adx, pdi, mdi, rsi, close_clust1, close_clust2 = calc_boll_tech(df)
    ary = [code, index, close, boll_mid, boll_h, boll_v,
                            boll_zz_slope, boll_w, adx, pdi, mdi, rsi, close_clust1, close_clust2]
    #df_tmp = pd.DataFrame(ary)
    #df_result = pd.concat([df_result, df_tmp], axis=0)
    df_result = agl.df_concat(df_result, ary)
    #print(df_result)
    #if (rsi[-1] < 70 and rsi[-1] > 30 ):
        #return False
    #if  adx[-1]<50:
        #return False
    sign = True
    if close > boll_mid:
        sign = False
    if boll_zz_slope > -0.6:
        sign = False
    if boll_w < 2:
        sign = False
    
    return df_result, sign
    
def main():
    code = stock.get_codes(stock.myenum.randn, 1)[0]
    points = []
    df_result = pd.DataFrame([])
    for i, df in enumerate(mydata(code)):
        df_result, sign = find_trade_pos(df, df_result, code, i)
        if sign:
            points.append(i)
    #print(points)          
    fname = 'out/myadx_%s.csv'%(code)
    agl.createDir(os.path.dirname(os.path.abspath(fname)))
    df_result.to_csv(fname)
    #查看信号出现的概率
    x = np.arange(len(mydata(code)))
    y = np.zeros(len(x))
    y[points] = 1
    pl.scatter(x, y)
    pl.show()
    
    #统计出现的概率
    print(len(points)/len(x))
    count = 0
    for i in range(1, len(points)):
        if points[i] - points[i-1]> 1:
            count += 1
    print(count)
    
def read_cur_slope(df, df_result):
    """给定一个状态， 看该状态在结果表中出现的机率
    return : float
    """
    c = 0
    for index, row in df_result.iterrows():
        df2 = pd.DataFrame(row).T
        if find_near(df, df2):
            c += 1
    return c / len(df_result)

def load_result():
    code = '603111'
    fname = 'out/myadx_%s.csv'%(code)
    df_result = pd.read_csv(fname, index_col = 0)
    return df_result

def test_read_cur_slope():
    # 取一个df
    #code = df_result[df_result.columns[0]][0]
    df_result = load_result()
    code = '603111'
    df = get_data_rand(code)
    ary = calc_boll_tech(df)
    df = pd.DataFrame(ary).T
    print(df)
    df_result = df_result[df_result.columns[2:]]
    used_cols = [1,2,3]
    df_result.columns = range(len(df_result.columns))
    df = df[df.columns[used_cols]]
    df_result = df_result[df_result.columns[used_cols]]
    print(df)
    print(df_result.head(1))
    v = read_cur_slope(df, df_result)
    
    print(v)

def find_near(df1, df2):
    """规定各个col相差的距离
    先简单的以相差5%来区分
    return: bool
    """
    assert(len(df1.columns)  == len(df2.columns))  
    b = True
    for col in df1.columns:
        v1 = float(df1[col])
        if v1 < 0.001:
            return False
        b = abs(v1 - float(df2[col]))/v1 < 0.05
        if not b:
            return b
    return b

if __name__ == "__main__":
    #main()
    test_read_cur_slope()    
    #pl.publish()
