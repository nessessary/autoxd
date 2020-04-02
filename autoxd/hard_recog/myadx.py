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
from autoxd.pypublish import publish

pl = publish.Publish()

def getCenterPoint():
    """计算聚类点"""
    code = jx.HLE
    df = get_data(code)
    #df = myredis.createRedisVal(myredis.gen_keyname(__file__, getCenterPoint), lambda: get_data(code)).get()
    closes = df['c'].values
    boll_up = df[colname.boll_upper].values
    boll_mid = df[colname.boll_middle].values
    boll_low = df[colname.boll_lower].values
    adx = pd.Series(df[colname.adx]).values
    pdi = pd.Series(df[colname.pdi]).values
    mdi = pd.Series(df[colname.mdi]).values
    rsi = pd.Series(df[colname.rsi]).values    
    
    if (rsi[-1] < 70 and rsi[-1] > 30 ) or (adx[-1]<50):
        return
    
    #计算斜率
    boll_z = boll_up if closes[-1]>boll_mid[-1] else boll_low
    zz = ZigZag(boll_z, percent=0.05)
    zz = zz[-2:]
    v_slope = slope(zz)
    #print(v_slope)
    v_slope = float_to_2(v_slope)
    
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
    pl.legend([v_slope],  loc='upper left')
    pl.subplot(212)
    pl.plot(adx)
    pl.plot(pdi)
    pl.plot(mdi)
    pl.plot(rsi)
    pl.legend([colname.adx, colname.pdi, colname.mdi, colname.rsi], loc='upper left')        
    pl.show()
    pl.close()
    
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
    for i in range(50):
        getCenterPoint()
    
if __name__ == "__main__":
    main()
    pl.publish()