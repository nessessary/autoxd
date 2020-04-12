#coding:utf8

"""设计自有的adx判断， 
1. 根据量价，把价格线转换为直方图， 然后聚类出一个中心点作为水平线,  (先不用成交量， 只使用价格来聚类)
2. 计算当前点与均线及水平线的距离
3. 计算boll轨的斜率
4. boll宽度及放大状态, ( 或者用自有adx代替)
"""

from autoxd.stock import getFiveHisdatDf, ZigZag
from autoxd import stock
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd.agl import ClustList2, float_to_2
from autoxd import ui, myredis
import pylab as pl
from single_boll import get_data, colname, pd
from single_boll import boll_data_Iterable as mydata
from autoxd.pypublish import publish
import numpy as np



pl = publish.Publish()

def find_trade_pos(df):
    """计算聚类点
    return: bool
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
    
    #if (rsi[-1] < 70 and rsi[-1] > 30 ):
        #return False
    #if  adx[-1]<50:
        #return False
    if closes[-1] > boll_mid[-1]:
        return False
    
    #计算斜率
    boll_z = boll_up if closes[-1]>boll_mid[-1] else boll_low
    zz = ZigZag(boll_z, percent=0.01)
    zz = zz[-2:]
    if len(zz) < 2:
        return False
    v_slope = slope(zz)
    #print(v_slope)
    if v_slope > -0.6:
        return False
    if boll_w[-1] < 2:
        return False
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
        y3_1 = k * x3
        v = y3-y3_1
        x3_1 = y3/k
        h = x3- x3_1
        return h, v
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
    h = float_to_2(h)
    v = float_to_2(v*100)
    
    #计算聚类点
    ary, line = ClustList2(2, closes)
    #ui.drawTsAndHlines(pl, closes, ary[0,1], ary[1,1])
    lines = [ary[0,1], ary[1,1]]
    
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
    pl.legend([v_slope, h, v],  loc='upper left')
    pl.subplot(212)
    pl.plot(adx)
    pl.plot(pdi)
    pl.plot(mdi)
    pl.plot(rsi)
    pl.legend([colname.adx, colname.pdi, colname.mdi, colname.rsi], loc='upper left')        
    pl.show()
    pl.close()
    
    return True

def slope(line):
    """ 计算线条的斜率
    index与price_percent的单位需要统一, index默认最大为30, price_percent的极限为30%
    line: [(index, price_percent),(index2,price_percent2)]
    return: float
    """
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

    
def main():
    code = stock.get_codes(stock.myenum.randn, 1)[0]
    points = []
    for i, df in enumerate(mydata(code)):
        if find_trade_pos(df):
            points.append(i)
    #print(points)          
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
    
if __name__ == "__main__":
    main()
    pl.publish()