#-*- coding:utf-8 -*-

"""基本面分析"""

import unittest, pylab as pl, dateutil
import stock,agl,ui, myredis
import numpy as np
import pandas as pd

def predict_jll(series):
    """预测净利润"""
    pass

def calc_history_syl(df, df_hisdat, period='year', dtype='pd.series'):
    """计算股票的历史市盈率 
    df : df 单个股票的净利润表
    df_hisdat : 日线
    period: str year|quarter
    dtype: str pd.df|pd.series
    return: df index如果是年一般指年尾，虽然使用的是2016-1-1, 因此调整为下一年年初"""

    rows = df[u'基本每股收益元'].sort_index()
    #df_hisdat = stock.getHisdatDataFrameFromRedis(code)
    if len(df_hisdat) == 0:
        return pd.Series([])
    rows = rows.ix[df_hisdat.index[0]:df_hisdat.index[-1]]
    if len(rows) == 0:
        return rows
    if str(rows.dtype) != 'float64':
        rows = rows[rows.map(lambda x: x.strip() != '')]
        rows = rows.astype(float)
    for i in range(len(rows)):
        price = np.nan
        d = agl.datetime_to_date(rows.index[i])
        # d is year
        if period == 'year':
            d = d.split('-')[0]
            try:
                df_last = df_hisdat[d].sort_index()
            except:
                return pd.Series([])
        else:
            df_last = df_hisdat[:d].sort_index()
        if len(df_last)>0:
            price = df_last.iloc[-1]['c']
        mgsy = rows.iloc[i]
        if period == 'quarter':
            #季度转年度
            quarter = df_last.index[-1].quarter
            mgsy = mgsy / quarter * 4
        syl = stock.SYL(price, mgsy)
        #print i, d, mgsy, price, syl
        rows.iloc[i] = syl
    if period == "year":
        #调整index为下一年的年初
        #print rows.index
        last_next_year = str(int(rows.index[-1].year) + 1)+'-1-1'
        new_index = rows.index.astype(str).tolist()
        new_index = new_index[1:] + [last_next_year]
        rows.index = pd.DatetimeIndex(new_index)
    #rows.index = map(lambda x: )
    if dtype == 'pd.series':
        return rows
    df[u'历史市盈率'] = rows
    return df[[u'历史市盈率', u'净利润万元']]
    
def find_jll_increase(df_year, method='inc'):
    """从净利润表中找出年净利润持续增长的个股  return: list codes"""
    code_results = []
    codes = df_year['code']
    codes = pd.unique(codes)
    for code in codes:
        col_offset = 2
            
        df = df_year[df_year['code'] == code][df_year.columns[2]]
        #series
        df = df[df.map(lambda x: x.strip() != '')]
        df = df.astype(float)
        df = df.sort_index()
        df = df.ix['2010':]
        df = np.array(df)
        result = df[1:] - df[:-1]
        #取每年的
        #print result
        is_sign = False
        #判断每年的增长大于10%
        if method == 'inc':
            result = result / df[:-1]
            if (result>0.1).all():
                is_sign = True

        if is_sign:
            code_results.append(code)
    return code_results            

def find_avg_syl(codes, df_jll, syl=20):
    """发现历史平均市盈率小于syl的个股 
    df_jll : df 净利润表
    return: list codes"""
    result_codes = []
    for code in codes:
        df_hisdat = stock.getHisdatDfRedis(code)
        
        df = df_jll[df_jll['code'] == code]    
        history_syl = calc_history_syl(df, df_hisdat)
        history_syl = history_syl.map(lambda x: agl.where(x<0, abs(x)*3, x))
        if len(history_syl)>0:
            avg_syl = np.average(history_syl)
            #print avg_syl, syl, code
            if avg_syl < syl and avg_syl > 5:
                #print history_syl, stock.GetCodeName(code), avg_syl
                result_codes.append(code)
    return result_codes

class mytest(unittest.TestCase):
    def _test1(self):
        t = stock.THS()
        df = t.df_jll
        code = '300033'
        df = df[df['code'] == code][df.columns[2]]
        #series
        df = df[df.map(lambda x: x.strip() != '')]
        df = df.astype(float)
        predict_jll(df)
    def test_find_avg_syl(self):
        #统计历史平均市盈率小于某值的个数
        scopre = [10, 15, 20, 30]
        nums = []
        codes = stock.get_codes()
        #codes = ['300033']
        df_jll = stock.THS().df_year
        for v in scopre:
            cur_codes = find_avg_syl(codes, df_jll, syl=v)
            print len(cur_codes)
            nums.append(len(cur_codes))
        ui.bar(pl, scopre, nums)
    def _test_calc_history_syl(self):
        import stock_pinyin as jx
        codes = [jx.HHKG.a, jx.THS,jx.DHRJ]
        codes = [jx.THS]
        #codes = stock.get_codes(stock.myenum.randn, 30)
        #codes = stock.get_codes()
        cpu_num = 6
        exec agl.Marco.IMPLEMENT_MULTI_PROCESS

def Run(codes, task_id=0):
    from pypublish import publish
    pl = publish.Publish()
    df_year = stock.THS().df_year
    df_jll = stock.THS().df_jll
    #myredis.delKeys(myredis.enum.KEY_HISDAT_NO_FUQUAN)
    for code in codes:
        df = df_year[df_year['code'] == code]
        df_hisdat = stock.getHisdatDfRedis(code)
        history_syl = calc_history_syl(df, df_hisdat, 'year')
        ui.DrawTs(pl, history_syl, title=stock.GetCodeName(code).decode('utf8'))
        df = df_jll[df_jll['code'] == code]
        history_syl = calc_history_syl(df, df_hisdat, period='quarter')
        ui.DrawTs(pl, history_syl, title=stock.GetCodeName(code).decode('utf8'))
    
if __name__ == '__main__':
    unittest.main()