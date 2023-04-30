#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# mail: nessessary@qq.com


import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as mp
import matplotlib.font_manager as fm
import mplfinance as mpf
from matplotlib.pylab import date2num
import matplotlib.dates as mdates
import matplotlib
import pylab as pl
import pandas as pd
import copy,unittest, datetime
#from autoxd import stock
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx
from autoxd import agl

#动态设置中文字体
#import matplotlib as mpl
#class FontStyle:
    #KAITI = 'KaiTi'
    #YAHEI = 'Microsoft YaHei'
    #FANGSONG = 'FangSong'
    #HEITI = 'SimHei'
#mpl.rcParams['font.sans-serif'] = [FontStyle.YAHEI]
#mpl.rcParams['font.serif'] = [FontStyle.YAHEI]

#plt.plot(x,y)
#plt.show()
def getFont():
    if sys.platform == 'win32':
        return fm.FontProperties(fname="c:/windows/fonts/simsun.ttc")
    elif sys.platform == 'darwin':
        fname = "/Library/Fonts/STIXGeneral.otf"
        #fname = ""
        return fm.FontProperties(fname=fname)
    else:
        return fm.FontProperties(fname="")  

#
#----------------------------------------------------------------------
def demo():
    """"""
    plt.figure(1) # the first figure
    plt.subplot(121) # the first subplot in the first figure
    plt.plot([1,2,3])    
    plt.subplot(122) # the second subplot in the first figure
    plt.plot([4,5,6])

    plt.figure(2) # a second figure
    plt.plot([4,5,6]) # creates a subplot(111) by default
    plt.figure(1) # figure 1 current; subplot(212) still current
    plt.subplot(211) # make subplot(211) in figure1 current
    plt.title('Easy as 1,2,3') # subplot 211 title    

    plt.show()    

def DrawLine(pl, sign, closes):
    """根据sign来画竖线"""
    assert(len(sign) == len(closes))
    high = max(closes)
    low = min(closes)
    l = (high - low) * 0.1	#竖线的高度
    for i in range(1,len(sign)):
        if sign[i]>sign[i-1]:
            #画红线
            pl.plot([i,i],[closes[i]-l,closes[i]+l],'r')
        if sign[i]<sign[i-1]:
            pl.plot([i,i], [closes[i]-l, closes[i]+l], 'g')
def DrawDvs(pl, closes, curve, sign, dvs, pandl, sh, title, leag=None, lad=None ):
    pl.figure
    pl.subplot(311)
    pl.title("id:%s Sharpe ratio: %.2f"%(str(title),sh))
    pl.plot(closes)
    DrawLine(pl, sign, closes)
    pl.subplot(312)
    pl.grid()
    if dvs != None:
        pl.plot(dvs)
    if isinstance(curve, np.ndarray):
        DrawZZ(pl, curve, 'r')
    if leag != None:
        pl.plot(leag, 'r')
    if lad != None:
        pl.plot(lad, 'b')
    #pl.plot(stock.GuiYiHua(closes[:i])[60:])
    pl.subplot(313)
    pl.plot(sign)
    pl.plot(pandl)
    pl.show()
    pl.close()    

class draw_style:
    none = 0
    head = 1
    mid = 2
    end = 3

def DrawZZ(pl, zz, c='r', is_append=draw_style.none):
    if is_append == draw_style.none or is_append == draw_style.head:
        pl.figure
    pl.plot(zz[:,0], zz[:,1],c)
    if is_append == draw_style.none or is_append == draw_style.end:
        pl.show()
        pl.close()
def drawZZAndKstpZZ(pl, zz, zz_kstp, yestoday_close):
    pl.figure
    pl.plot(zz[:,0], zz[:,1])
    pl.plot(zz_kstp[:,0], zz_kstp[:,1], 'r')
    #画一个横线
    pl.plot([0, 250], [yestoday_close, yestoday_close])
    pl.show()
    pl.close()

def DrawTs(pl, ts=[], lines = None, title="", high=[], low=[],mid=[], save_file=False,legends=None):
    """画时间序列, ts: closes, save_file: 返回图像文本文件名"""
    pl.figure
    legend = []
    if len(ts)>0:
        pl.plot(ts)
        legend.append('ts')
    if len(high)>0:
        pl.plot(high)
        legend.append('high')
    if len(low)>0:
        pl.plot(low)
        legend.append('low')
    if len(mid)>0:
        pl.plot(mid)
        legend.append('mid')

    prop = fm.FontProperties(fname="c:/windows/fonts/simsun.ttc")
    if title != "":
        pl.title(title, fontproperties=prop)
    if lines != None:
        i = lines
        if i>=len(ts):
            i = len(ts)-1
        pl.plot([i,i], [ts[i]-ts[i]*0.1, ts[i]+ts[i]*0.1], 'g')
        legend.append('lines')
    if legends is not None:
        legend = legends
    pl.legend(legend, loc='upper left')
    if save_file:
        fname = 't3.png'
        pl.savefig(fname)
        return fname
    pl.show()
    pl.close()
def _DrawVLine(pl, i, ts):
    """画一个短竖线, i在ts中的索引"""
    i = int(i)
    pl.plot([i,i], [ts[i]-ts[i]*0.1, ts[i]+ts[i]*0.1], 'r')
def DrawHLine(pl, v, n, clr='r'):
    pl.plot([0, n], [v, v], clr)
    
def drawTsAndHlines(pl, ts, *lines):
    pl.figure
    pl.plot(ts)
    for l in lines:
        DrawHLine(pl, l, len(ts))
    pl.show()
    pl.close()

def DrawClosesAndVolumes(pl, closes, volumes, zz=None, avg=None, trade_index=None,\
                         title=None, closes_dp=None, closes_bankuai=None):
    """画closes，非df模式，
    closes_dp: 大盘
    closes_bankuai: 板块
    """
    legend = []
    pl.figure
    pl.subplot(211)
    if title != None:
        pl.title(title, fontproperties=getFont())
    pl.plot(closes)
    legend.append('close')
    if zz is not None:
        DrawZZ(pl, zz, c='r')
    if avg is not None:
        pl.plot(avg)
    if not agl.IsNone(closes_dp):
        pl.plot(closes_dp)
        legend.append('dapan')
    if not agl.IsNone(closes_bankuai):
        pl.plot(closes_bankuai)
        legend.append('bankuai')
    if trade_index != None:
        pl, index, ts = pl, trade_index, closes
        _DrawVLine(pl, index, ts)	
    pl.legend(legend, loc='upper left')
    pl.subplot(212)
    pl.plot(volumes)
    pl.show()
    pl.close()
def DrawDvsAndZZ(pl, dvs, zz, closes=None):
    """dvs和zz画在一张图里; dvs : 也可以是closes, """
    dvs = np.array(dvs)
    pl.figure
    if closes == None:
        pl.plot(dvs)
        pl.plot(zz[:,0], zz[:,1], 'r')
    else:
        pl.subplot(211)
        pl.plot(closes)
        pl.grid()
        pl.subplot(212)
        pl.grid()
        pl.plot(dvs)
        pl.plot(zz[:,0], zz[:,1], 'r')
    pl.show()
    pl.close()
def ShowZZ(pl, zz, title=''):
    pl.figure
    pl.grid()
    if title != '':
        pl.title(title)
    DrawZZ(pl, zz, c='b')
    pl.show()
    pl.close()
def DrawStr(s):
    pl.figure
    pl.text(0,0,s)
    pl.show()
    pl.close()
def DebugZZ(zz):
    import pylab
    pylab.figure
    pylab.plot(zz[:,0], zz[:,1])
    pylab.show()
    pylab.close()

def MyShow(closes):
    pl.figure
    pl.plot(closes)
    pl.show()
    pl.close()

def drawDf(pl, df, title=''):
    pl.figure
    if title != '':
        if agl.is_utf8(title):
            title = title.decode('utf8')
        #pl.title(title, fontproperties=getFont())
    if not isinstance(df, type(None)):
        pl.rc('font', family='simhei')
        df.plot(title=title)
    pl.show()
    pl.close()
def drawTwoDf(pl, df1, df2, title=''):
    """分别画两个df"""
    pl.figure
    pl.rc('font', family='simhei')
    if title != '':
        if agl.is_utf8(title):
            title = title.decode('utf8')    
    fig = pl.gcf()
    ax1 = fig.add_subplot(211)
    df1.plot(ax=ax1, title=title)
    ax2 = fig.add_subplot(212)
    df2.plot(ax=ax2)
    pl.show()
    pl.close()    
def DrawScatt(pl, x,y, title='', label_legend=None):
    pl.figure
    prop = fm.FontProperties(fname="c:/windows/fonts/simsun.ttc")
    if title != "":
        pl.title(title, fontproperties=prop)
    pl.scatter(x,y,s=10)
    if label_legend is None:
        label_legend = [u"市盈率", u"流通市值(亿)"]
    pl.ylabel(label_legend[0], fontproperties=prop)
    pl.xlabel(label_legend[1], fontproperties=prop)
    pl.show()
    pl.close()

def drawChips(pl, df, df_close, title=""):
    """画一个竖向的直方图, 坐标显示价位, 值为仓位比率
    df: df_chips
    """
    pl.figure
    pl.subplot(121)
    pl.title(title)
    df_close['c'].plot()
    pl.subplot(122)
    chips = df[df.columns[1]].values
    pl.barh(df[df.columns[0]].values, chips)
    pl.show()
    pl.close()    
    
def drawChipMa(df_chips, mas):
    """白线、黄线、紫线、绿线、蓝线依次分别表示:5、10、20、30、60日移动平均线"""
    df = df_chips
    pl.figure
    chips = df[df.columns[1]].values
    pl.barh(df[df.columns[0]].values, chips)
    pl.show()
    pl.close()    

def DrawHist(pl, shs):	
    """画直方图统计, shs: 夏普率 array"""
    shs = np.array(shs, dtype=float)
    #print "mean: %.2f"%shs.mean()
    shs = shs[np.isnan(shs) == False]
    if len(shs)>0:
        pl.figure
        pl.hist(shs)
        def ShowHitCount(shs):
            #出击个数
            go_count = len(shs) - len(shs[np.isnan(shs)])
            #出击率
            if len(shs) != 0:
                v = float(go_count)/ float(len(shs))
                #print("trade rato:%.2f%%"%(v*100))
            #出击后胜率
            if go_count>0:
                v = float(len(shs[shs>0]))/float(go_count)
                #print("win rato: %.2f%%"%(v*100))
        pl.show()
        #ShowHitCount(shs)

def barh(pl, x, h, title=''):
    pl.figure
    if title != '':
        pl.title(title)
    pl.barh(x, h, height=0.1)
    pl.show()
    pl.close()
def bar(pl, x, y):
    pl.figure
    pl.bar(x,y)
    pl.show()
    pl.close()
    
def ParallelBar(pl, df):
    """画多个并列的柱状图"""
    plt.rcParams['font.sans-serif']=['SimHei'] # 解决中文乱码
    plt.rcParams['axes.unicode_minus'] = False
    df.plot.bar()
    pl.show()
    
def ShowTradeResult(pl, bars, signals, returns, signal_dependent_num=0):
    """绘制策略的交易结果
    注意，bars不能有nan，否则画不出箭头
    bars: pd.DateFrame 日线等数据集 index为时间 收盘为['c']
    signals: pd.DateFrame 信号 包含技术指标 index同bars
    returns: 资金结果, 由backtest.MarketOnClosePortfolio生成
    signal_dependent_num: 显示signals里的依赖线
    """
    # Plot two charts to assess trades and equity curve
    pl.figure
    #fig = pl.figure()
    fig = pl.gcf()
    fig.patch.set_facecolor('white')     # Set the outer colour to white
    ax1 = fig.add_subplot(211,  ylabel='Price in RMB')

    # Plot the AAPL closing price overlaid with the moving averages
    bars['c'].plot(ax=ax1, color='r', lw=2.)
    #显示信号产生的依据, 最好是使用固定的值， 比如信号线1-n, range(n)
    if signal_dependent_num>0:
        signals[np.array(range(signal_dependent_num), dtype=str)].plot(ax=ax1, lw=2.)
    #signals[['short_ma', 'long_ma']].plot(ax=ax1, lw=2.)

    # Plot the "buy" trades against AAPL
    ax1.plot(signals.loc[signals.positions == 1.0].index, 
             bars['c'][signals.positions == 1.0],
             '^', markersize=10, color='m')

    # Plot the "sell" trades against AAPL
    ax1.plot(signals.loc[signals.positions == -1.0].index, 
             bars['c'][signals.positions == -1.0],
             'v', markersize=10, color='k')

    # Plot the equity curve in dollars
    ax2 = fig.add_subplot(212, ylabel='Portfolio value in RMB')
    returns['total'].plot(ax=ax2, lw=2.)

    # Plot the "buy" and "sell" trades against the equity curve
    ax2.plot(returns.loc[signals.positions == 1.0].index, 
             returns.total[signals.positions == 1.0],
             '^', markersize=10, color='m')
    ax2.plot(returns.loc[signals.positions == -1.0].index, 
             returns.total[signals.positions == -1.0],
             'v', markersize=10, color='k')

    # Plot the figure
    #fig.show()    
    pl.show()
    pl.close()

def ShowTradeResult2(pl, bars, signals, zhijin, changwei,signal_dependent_num=0, freq=300, title=''):
    """绘制策略的交易结果, 交易剔除了非交易时间， 资金未剔除， 因此两者的xtick看起来是不一致的
    注意，bars不能有nan，否则画不出箭头
    bars: pd.DateFrame 日线等数据集 index为时间 收盘为['c']
    signals: pd.DateFrame 信号 包含技术指标 index同bars
    zhijin: pd.Serias 资金结果
    changwei: 当前仓位
    signal_dependent_num: 显示signals里的依赖线
    freq: 坐标的间隔
    """
    # Plot two charts to assess trades and equity curve
    pl.figure
    #fig = pl.figure()
    pl.close()
    fig = pl.gcf()
    fig.patch.set_facecolor('white')     # Set the outer colour to white
    ax1 = fig.add_subplot(211,  ylabel='Price in RMB')
    if title != '':
        pl.title(title, fontproperties=getFont())

    #思路， 把时间转整数，显示时再把整数转时间字符串
    # 为了去除非交易时间， 把index 转换为整数
    date_ticks = copy.deepcopy(bars.index)
    indexs = np.arange(len(bars))
    bars.index = indexs
    signals.index = indexs
    
    if len(bars) == len(zhijin):
        if zhijin is not None:
            zhijin.index = indexs
        if changwei is not None:
            changwei.index = indexs

    # Plot the AAPL closing price overlaid with the moving averages
    bars['c'].plot(ax=ax1, color='r', lw=2.)
    #显示信号产生的依据, 最好是使用固定的值， 比如信号线1-n, range(n)
    if signal_dependent_num>0:
        signals[np.array(range(signal_dependent_num), dtype=str)].plot(ax=ax1, lw=2.)
    #signals[['short_ma', 'long_ma']].plot(ax=ax1, lw=2.)

    # Plot the "buy" trades against AAPL
    ax1.plot(signals.loc[signals.positions == 1.0].index, 
             bars['c'][signals.positions == 1.0],
             '^', markersize=10, color='m')

    # Plot the "sell" trades against AAPL
    ax1.plot(signals.loc[signals.positions == -1.0].index, 
             bars['c'][signals.positions == -1.0],
             'v', markersize=10, color='k')

    # Plot the equity curve in dollars
    ax2 = fig.add_subplot(212, ylabel='Portfolio value in RMB')
    if zhijin is not None and len(zhijin)>1:
        zhijin.plot(ax=ax2, lw=2.)
    legends = ['zhijing']
    if changwei is not None and len(changwei)>1:
        changwei.plot(ax=ax2)
        legends.append('changwei')
    ax2.legend(legends,loc=0)

    #剔除非交易时间
    #freq = 300
    ax1.set_xticks(indexs[::freq])
    date_ticks = date_ticks.map(lambda x : agl.datetime_to_date(x))
    ax1.set_xticklabels(date_ticks[::freq], rotation=45, ha='right')
    if len(bars) == len(zhijin):
        ax2.set_xticks(indexs[::freq])
        ax2.set_xticklabels(date_ticks[::freq], rotation=45, ha='right')

    # Plot the figure
    #fig.show()    
    pl.show()
    pl.close()
def testShowTradeResult():
    import backtest
    from autoxd import stock
    code = '600100'
    bars = stock.Guider(code).ToDataFrame()
    bars = bars.loc['2014':]
    print(bars.head())
    #两均线穿越
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0.0
    signals['short_ma'] = stock.MA(closes=np.array(bars['c']), day=5)
    signals['long_ma'] = stock.MA(closes=np.array(bars['c']), day=20)
    signals['0'] = signals['short_ma']
    signals['1'] = signals['long_ma']
    signals['signal'] = np.where(signals['short_ma'] > signals['long_ma'], 1.0, 0.0)
    signals['positions'] = signals['signal'].diff()  
    print(signals)
    portfolio = backtest.MarketOnClosePortfolio(code, bars, signals, initial_capital=100000.0)
    returns = portfolio.backtest_portfolio()
    ShowTradeResult(pl, bars, signals, returns, 2)

def TradeResult_Boll(pl, bars, zhijin,changwei, title=''):
    """显示策略结果
    bars: df 包含有  c字段即可
    zhijin: df index同bars
    changwei: df index同bars
    title: str 中文需要使用decode(utf8)
    """
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0.0
    signals['signal'] = np.zeros(len(bars['c']))
    signals['positions'] = bars['positions']
    ShowTradeResult2(pl, bars, signals, zhijin,changwei , 0, freq=30, title=title)
def testTradeResult_Boll():
    code = '002074'
    bars = stock.CreateFenshiPd(code, '2017-7-22','2017-8-4')
    if len(bars)>0:
        bars = bars.resample('1min').mean()
    else:
        return
    bars['c'] = bars['p']
    bars = bars.dropna()
    zhijin = pd.Series(index=bars.index)
    zhijin.loc[:] = 1000000
    zhijin[100] = 1010000
    zhijin[200] = 980000

    TradeResult_Boll(pl, bars, zhijin, None, stock.GetCodeName(code).decode('utf8'))


def drawFenshi(pl, df_fenshi, title=None):
    """df_fenshi: ['bpv']"""
    if 0: pl = plt
    pl.figure
    pl.subplot(211)
    if title != None:
        pl.title(title, fontproperties=getFont())
    df = copy.deepcopy(df_fenshi)
    df['p'] = df['p']/max(df['p'])
    df['v'] = df['v']/max(df['v'])
    df['p'].plot()
    pl.subplot(212)
    df['v'].plot()
    pl.show()
    pl.close() 
def test_drawFenshi():
    code = '600100'
    df_fenshi = stock.FenshiEx(code, is_fuquan=True).df
    drawFenshi(pl, df_fenshi)
######根据pandas来画图
def drawKline(pl, df_code, df_dp=None, df_bk=None, title=None, df_syl=None, legend2=None):
    """画个股k线图
    pl: 自定义pl
    df_code: 个股pd.DataFrame, ['holcv']
    df_dp: 大盘
    df_bk: 板块
    df_syl: 历史市盈率
    legend2: 标识, 不支持中文
    """
    if 0: pl = plt
    pl.figure
    pl.subplot(211)
    if title != None:
        pl.title(title, fontproperties=getFont())
    #画个股数据
    df = copy.deepcopy(df_code)
    df['c'] = df['c']/max(df['c'])
    df['v'] = df['v'] / max(df['v'])
    df['c'].plot()
    df2 = df['v']
    legend = ['close']
    if not isinstance(df_dp, type(None)) and len(df_dp)>0:
        df = copy.deepcopy(df_dp)
        if isinstance(df, pd.Series):
            df.plot()
        else:
            df['c'] = df['c']/max(df['c'])
            #df['v'] = df['v'] / max(df['v'])
            df['c'].plot()
        legend.append('dapan')
        #df['v'].plot()
    if not agl.IsNone(df_bk):
        df_bk.plot()
        legend.append('bankuai')
    pl.legend(legend, loc='upper left')
    pl.subplot(212)
    df2.plot()
    legend = ['volumns']
    if not isinstance(df_syl, type(None)) and len(df_syl) > 0:
        df = copy.deepcopy(df_syl)
        #df['市盈率'] = df['市盈率'] / max(df['市盈率'])
        #df['每股收益'] = df['每股收益'] / max(df['每股收益'])
        ##df['市盈率'].plot()	
        #df['每股收益'].plot()
        #legend.append('mgsy')
        df.plot()
        legend.append('jll')
    if legend2 is not None:
        legend = legend2
    pl.legend(legend, loc='upper left')	
    pl.show()
    pl.close()
def test_drawKline():
    code, start_day, end_day = '600100','',''
    df = stock.getHisdatDataFrameFromRedis(code, '', '')
    code = stock.getDapanCode(code)
    df_dp = stock.getHisdatDataFrameFromRedis(code, start_day, end_day)
    drawKline(pl, df_code=df, df_dp=df_dp)
def drawBeta(pl, df, title):
    if 0: pl = plt
    pl.figure
    df.plot()
    pl.title(title, fontproperties=getFont())
    pl.show()
    pl.close()     
def drawBoll(pl, closes, boll_up, boll_mid, boll_low, save_file=""):
    pl.figure
    ax = plt.gca()
    ax.yaxis.set_ticks_position('both')
    plt.tick_params(axis='y', which='both', labelleft='on', labelright='on')
    ax.plot(closes)
    pl.plot(boll_up)
    pl.plot(boll_mid)
    pl.plot(boll_low)
    if len(save_file)>0:
        pl.savefig(save_file)
    pl.show()
    pl.close()


def drawBollAndChip(pl, closes, boll_up, boll_mid, boll_low, chips):
    """按一个固定比例显示， 显示当前价的正负20%"""
    last_price = closes[-1]
    high_price = last_price * 1.1
    low_price = last_price * 0.9
    h_close = np.max(closes)
    l_close = np.min(closes)
    if (h_close- l_close) / last_price > 0.2:
        pass
    else :
        h_close = high_price
        l_close = low_price
    h_sum = chips[1][chips[0]>=h_close].sum()
    l_sum = chips[1][chips[0]<=l_close].sum()
    chips = chips[chips[0]<h_close]
    chips = chips[chips[0]>l_close]
    chips = agl.df_concat(chips, [h_close, h_sum])
    chips = agl.df_concat(chips, [l_close, l_sum])
    
    pl.figure
    ax = plt.gca()
    ax.yaxis.set_ticks_position('both')
    plt.tick_params(axis='y', which='both', labelleft='on', labelright='on')
    df = chips
    chips = df[df.columns[1]].values 
    chips = chips * 100
    ax.barh(df[df.columns[0]].values, chips, height=0.5)    
    
    ax.plot(closes)
    pl.plot(boll_up)
    pl.plot(boll_mid)
    pl.plot(boll_low)
    pl.show()
    pl.close()
    
def weekday_candlestick(ohlc_data, ax, fmt='%b %d', freq=7, **kwargs):
    """ Wrapper function for matplotlib.finance.candlestick_ohlc
        that artificially spaces data to avoid gaps from weekends 
    去除非交易时间的空隙
    fmt: 日期格式
    freq: 日期显示的间隔
    """
    freq = int(freq)
    
    # Convert data to numpy array
    ohlc_data_arr = np.array(ohlc_data)
    ohlc_data_arr2 = np.hstack(
        [np.arange(ohlc_data_arr[:,0].size)[:,np.newaxis], ohlc_data_arr[:,1:]])
    ndays = ohlc_data_arr2[:,0]  # array([0, 1, 2, ... n-2, n-1, n])

    # Convert matplotlib date numbers to strings based on `fmt`
    dates = mdates.num2date(ohlc_data_arr[:,0])
    date_strings = []
    for date in dates:
        date_strings.append(date.strftime(fmt))

    # Plot candlestick chart
    #mpf.candlestick_ohlc(ax, ohlc_data_arr2, **kwargs)
    mpf.plot(ohlc_data_arr2, type='candle')

    # Format x axis
    ax.set_xticks(ndays[::freq])
    ax.set_xticklabels(date_strings[::freq], rotation=45, ha='right')
    ax.set_xlim(ndays.min(), ndays.max())

class AsynDrawKline(object):
    class enum:
        trade_bSell = '买0卖1'
        trade_price = '委托价格'
    @staticmethod
    def drawKline(df, df_trades=None):
        """画k线图, 异步模式
        需要注意的是如果df比较大的话，那么速度是相当的慢, 一般5日线10天的数据较好
        df : 日线或5分钟线, cols('ohlcv')
        df_trades : 交易点, 需要包含字段cols('trade_bSell', ['trade_price']), 见enum, []意思为不是必须
        """

        def df_to_matplotformat(df):
            """
            return: list[turpl(t,o,h,l,c)]
            """
            data_list = []
            for dates,row in df.iterrows():
                # 将时间转换为数字
                #date_time = datetime.datetime.strptime(dates,'%Y-%m-%d')
                t = date2num(dates)
                open,high,low,close = row[:4]
                datas = (t,open,high,low,close)
                data_list.append(datas)	
            return data_list
        quotes = df_to_matplotformat(df)
        plt.cla()
        # 创建一个子图 
        #fig, ax = plt.subplots(facecolor=(0.5, 0.5, 0.5))
        #fig.subplots_adjust(bottom=0.2)
        ax = plt.gca()
        if 0: ax = matplotlib.axes.Axes(fig, rect)
        plt.subplots_adjust(bottom=0.2)
        ## 设置X轴刻度为日期时间
        #ax.xaxis_date()
        ## X轴刻度文字倾斜45度
        #plt.xticks(rotation=45)
        #plt.title("code")
        #plt.xlabel("time")
        #plt.ylabel("price")
        #mpf.candlestick_ohlc(ax,quotes,width=.001,colorup='r',colordown='green')
        #调整下面日期显示的密度
        freq = len(quotes)/20
        weekday_candlestick(quotes, ax, fmt='%b %d %H:%M', freq=freq, width=0.01, colorup='r',colordown='green')
        #plt.grid(True)    

        #画交易点
        if not agl.IsNone(df_trades):
            if 0:df_trades = pd.DataFrame()
            for index, row in df_trades.iterrows():
                if AsynDrawKline.enum.trade_price in row.keys():
                    price = row[AsynDrawKline.enum.trade_price]
                else:
                    price = row['c']
                #交易点
                trade_position = []
                a = np.zeros(len(quotes))
                a[:] = price
                index = len(df[:index])
                a[:index] =np.nan
                bSell = int(row[AsynDrawKline.enum.trade_bSell])
                clr = agl.where(bSell, 'g', 'r')
                plt.plot(a, color=clr, linewidth=0.25)
                plt.text(len(quotes),price, str(price), color=clr)   

        #左右两边都有坐标
        #ax.yaxis.set_ticks_position('both')
        #plt.tick_params(axis='y', which='both', labelleft='on', labelright='on')
        plt.draw()
        plt.pause(0.1)    

def Rectangle(pl,quotes, h,l, left, right,clr='b', linewidth=0.25):
    """在k线图中画矩形
    h,l : 上下的价格, np.max(quotes); np.min(quotes)
    left,right: 左右的index
    """
    #clr = 'b'
    #linewidth = 0.25
    a = np.zeros(len(quotes))
    a[:] = np.nan
    
    #a[:] = 30
    #pl.plot(a)
    #画横线
    a[left:right] = h
    pl.plot(a, color=clr, linewidth=linewidth)
    a[:] = np.nan
    a[left:right] = l
    pl.plot(a, color=clr, linewidth=linewidth)
    #画竖线
    pl.plot([left,left],[h,l], clr, linewidth=linewidth)
    pl.plot([right, right], [h,l], clr, linewidth=linewidth)

def drawKlineUseDf(pl, df, df_boll=None, dpi=100):
    df = copy.deepcopy(df)
    df.columns =  ('Open', 'Close','High', 'Low',  'Volume')
    from autoxd.pypublish import publish
    if type(pl) == publish.Publish:
        pl: publish.Publish
        pl.save()
        img_path = pl.get_CurImgFname()
        if df_boll is None:
            ap0 = []
        else:
            ap0 = [
                mpf.make_addplot(df_boll['boll_up'], color = 'orange'),
                mpf.make_addplot(df_boll['boll_mid'], color = 'g'),
                mpf.make_addplot(df_boll['boll_lower'], color = 'r'),
            ]        
        mpf.plot(df, type='candle',savefig=img_path, closefig=True, figsize=(640/dpi, 480/dpi), addplot=ap0)
    else:
        mpf.plot(df, type='candle')
       

    

def draw3d(df=None, titles=None, datas=None):
    """画3d"""
    #该行在c运行时会报错
    from mpl_toolkits.mplot3d.axes3d import Axes3D
    
    def genDf():
        df = pd.DataFrame([])
        for i in range(3):
            n = agl.array_random(100)
            df[i] = n
        return df
    if df is None:
        df = genDf()
    assert(len(df.columns)>=3)
    X, Y, Z = np.array(df[df.columns[0]]), np.array(df[df.columns[1]]), np.array(df[df.columns[2]])
    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(1, 1, 1, projection='3d')
    p = ax.scatter(X, Y, Z)
    
    if datas is not None:
        for i in range(len(datas)):
            df = datas[i][0]
            x, y, z = np.array(df[df.columns[0]]), np.array(df[df.columns[1]]), np.array(df[df.columns[2]])
            c = str(datas[i][1])
            ax.scatter(x,y,z, c=c)
    
    if titles is not None and len(titles)>=3:
        ax.set_xlabel(titles[0])
        ax.set_ylabel(titles[1])
        ax.set_zlabel(titles[2])    
            
    plt.show()

class MyTest(unittest.TestSuite):
    def _test_DrawTs(self):
        code = '300059'
        date = ['2016-1-1','2016-3-1']
        fenshi = stock.getFenshiDfUseRedis(code, date[0],date[1])
        print(fenshi)
        DrawTs(pl, ts=fenshi['p'])
    def _test_DrawZZ(self):
        code = '300033'
        df_five_hisdat = stock.getFiveHisdatDf(code)
        closes = df_five_hisdat['c'][-500:]
        zz = stock.ZigZag(closes,percent=1)
        DrawDvsAndZZ(pl, closes, zz)
        #df = stock.getHisdatDataFrameFromRedis(code)
        #closes = df['c']
        #zz = stock.ZigZag(closes,percent=1)
        #DrawDvsAndZZ(pl, closes, zz)
        
    def _test_ShowTradeResult(self):
        #testShowTradeResult()
        testTradeResult_Boll()
    def _test_AsynDrawKline(self):
        from autoxd import stock
        code = jx.ZCKJ.b
        start_day = '2017-8-25'
        #df = stock.getHisdatDataFrameFromRedis(code, start_day)
        df = stock.getFiveHisdatDf(code, start_day=start_day, method='tdx')
        import account
        account = account.LocalAcount(account.BackTesting())
        #随机找三个交易点
        indexs = agl.GenRandomArray(len(df), 3)
        trade_bSell = [0,1,0]
        df_trades = df[df.index.map(lambda x: x in df.index[indexs])]
        df_trades = df_trades.copy()
        df_trades[AsynDrawKline.enum.trade_bSell] = trade_bSell

        plt.ion()
        for i in range(10):
            AsynDrawKline.drawKline(df[i*10:], df_trades)

        plt.ioff()
        #plt.show()  #最后停在画面处， 没有的话进程结束
    def _test_3d(self):
        draw3d()
    def _test_drawKline2(self):
        code = jx.CYJM长盈精密
        #drawKlineUseDf(pl, df)
    def _test_drawKlin(self):
        code = jx.THS
        df = stock.getHisdatDataFrameFromRedis(code)
        drawKline(pl, df, legend2=['成交量'])
    def test_parllelbar(self):
        df = pd.DataFrame([[1, 2, 3], [2, 3, 4]])
        ParallelBar(pl, df)
        
    def test_drawKlineUseDf(self):
        from autoxd import stock
        code = jx.CYJM长盈精密
        df = stock.getFiveHisdatDf(code)
        
        from autoxd.pypublish.publish import Publish
        pl = Publish()
        df = df[-100:]
        drawKlineUseDf(pl, df)
    
        df = stock.getHisdatDataFrameFromRedis(code)
        drawKlineUseDf(pl, df, None, 120)
    
        pl.publish()
    
    
        
if __name__ == "__main__":
    t = MyTest()
    #t.test_parllelbar()
    t.test_drawKlineUseDf()

    

    
