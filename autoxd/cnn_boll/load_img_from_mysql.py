#coding:utf8

"""保存图像从mysql"""
from __future__ import print_function
import mysql, stock, stock_pinyin as jx
import judge_boll_sign, tushare_handle
import pylab as pl
import os

img_path = 'img_labels/imgs/'
def init():
    root_dir = img_path.split('/')[0]
    if not os.path.isdir(root_dir):
        os.mkdir(root_dir)
    if not os.path.isdir(img_path):
        os.mkdir(img_path)
def getData(code):
    df = stock.getFiveHisdatDf(code)
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)
    return upper, middle, lower, df
def gen_fname(code,index, df):
    t = str(df.index[index])
    t1 = t.replace(' ', '_')
    t1 = t1.replace(':', '_')
    fname = code +'_'+ t1+'.png'    
    return fname
def load_img(code):
    datas = getData(code)
    df = datas[-1]
    if len(df)<200:
        return 
    for index in range(200,len(df),2):
        judge_boll_sign.drawfig(index, datas)
        fname = gen_fname(code, index, df)
        fname = img_path + fname
        pl.savefig(fname)
        #pl.show()
        
init()        
for code in stock.get_codes(stock.myenum.randn, 10):
    load_img(code)



    