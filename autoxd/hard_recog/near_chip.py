#coding:utf8

"""查看five最近n天的筹码分布"""
from autoxd import stock, ui, myredis, agl, help
from autoxd.pinyin import stock_pinyin3 as jx
#import pylab as pl
from autoxd.pypublish import publish, policy_report
import pandas as pd

def dumpFiveToRedis():
    tt = agl.tic_toc()
    codes = stock.get_codes()
    for code in codes:
        key = code + '_five_kline'
        df = stock.getFiveHisdatDf(code)
        myredis.set_obj(key, df)
    return True

def init():
    myredis.gen_data_at_curday(__file__, init, dumpFiveToRedis)
    
class near_chip(object):
    def __init__(self, pl, n=10):
        self.n = n
        self.pl = pl
        
    def run_one(self, code):
        #df_hisdat = stock.getHisdatDataFrameFromRedis(code)
        df = stock.getFiveFromRedis(code)
        if len(df) == 0:
            return
        day=agl.datetime_to_date(df.index[-1])
        #print (df_hisdat.iloc[-1]['v'] *100 , df[day]['v'].sum())
        pre_day = help.MyDate.s_Dec(day, daynum=-self.n)
        df = df[pre_day:]
        df['v'] /= 100
        df_GuBen_change=stock.getGubenbiangen(code)
        if len(df_GuBen_change) == 0:
            return
        df = stock.convertVolToStockTrunover(df, df_GuBen_change)
        #print('day trunover=', df[day]['v'].sum())
        df_chip = stock.calcChips(df, n=0.0001)
        pl = self.pl
        pl: publish.Publish
        ui.drawKlineUseDf(pl, df)
        img_path_kline = pl.get_CurImgFname()
        ui.drawChips(self.pl, df_chip, df)
        img_path = self.pl.get_CurImgFname()
        last_close = df.iloc[-1]['c']
        chip_price_ratio = df_chip[df_chip[0]>last_close][1].sum()
        chip_price_ratio_percent = (chip_price_ratio / df_chip[1].sum())
        #print(last_close, chip_price_ratio, chip_price_ratio_percent)
        return [stock.GetCodeName(code), chip_price_ratio, chip_price_ratio_percent, img_path_kline, img_path]
        
def run(codes):
    pl = publish.Publish(explicit=True, is_clear_path=False) # 因为 是多进程 不能删除目录
    df = pd.DataFrame([])
    obj = near_chip(pl)
    for code in codes:
        r = obj.run_one(code)
        df = agl.df_concat(df, r)
    df.columns = ['name', 'trunover_sum', 'percent', 'imgkline', 'imgchip']
    return df

def report(df):
    pl = publish.Publish()
    pl.reset(policy_report.df_to_html_table(df))
    pl.publish()
    
    
if __name__ == "__main__":
    init()
    tt = agl.tic_toc()
    codes = stock.get_codes()
    #codes = stock.get_codes(stock.myenum.randn, n=100)
    cpu_num = 0
    if cpu_num == 1:
        codes = stock.get_codes(stock.myenum.randn, n=10)
        df = run(codes)
    else:
    # multi run
        from autoxd.MultiSubProcess import MultiSubProcess
        df, = MultiSubProcess.run_fn(run, codes, __file__, cpu_num)
        
    df = df[df['percent']>=0.9]
    df = df.sort_values(by='percent', ascending=False)
    df = df.head(50)
    report(df)
