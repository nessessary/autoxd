#coding:utf8

import pandas as pd
from autoxd import stock
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd.cnn_boll import env

def run():
    fpath = env.get_root_path()
    for code in stock.get_codes():
        fname = '/datasources/%s.csv'%(code)
        fname = fpath + fname
        df = stock.getFiveHisdatDf(code)
        df.to_csv(fname)
run()
        