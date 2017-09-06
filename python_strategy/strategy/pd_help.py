#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import numpy as np
import pandas as  pd
import sys, datetime

def df_zhangfu(df):
    """通过df来计算涨幅 return: df"""
    c = df['c'].tolist()
    df.loc[:,'zhangfu']=(df['c'][1:] - c[:-1])/c[:-1]
    return df
class Df:
    """辅助, 把一些常用数组调用转换为函数调用"""
    def __init__(self, df):
        """df: (index ['hlocv'])"""
        self.df = df
        if 0: self.df = pd.DataFrame()
    def getLastDate(self):
        """return: datetime.date"""
        return self.df.index[-1].date()
    def getLastTime(self):
        """return: int time"""
        return int(self.df.tail(1)['t'])
    def getLastPrice(self):
        """return: cur price"""
        return float(self.df.tail(1)['p'])
    def getDec(self):
        """获取涨跌差值， 现价-昨收盘"""
        cur = self.df.tail(1)['p']
        pre = self.df.loc[-2]['p']
        return float(cur- pre)/100.0
    def getCloses(self):
        """return: np.ndarray"""
        #取分时的closes
        try:
            return np.array(self.df['c'])
        except:
            return np.array(self.df['p'])
    def getVolumes(self):
        return np.array(self.df['v'])

def main(args):
    print "end"
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)