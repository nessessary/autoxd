#-*- coding:utf-8 -*-
#把主目录放到路径中， 这样可以支持不同目录中的库
import os
def AddPath():
    from sys import path
    mysourcepath = os.getenv('AUTOXD_PYTHON')
    if not mysourcepath in path:
        path.append(mysourcepath)    
#AddPath()
import numpy as np
import pandas as pd
import sys
import pyh
from autoxd import agl

def df_to_html_table(df, color='white', df_img_col_indexs=[-1]):
    """df转化为html表格输出, 简单的columns为[txt, img]
    df : 数据源
    color : background
    df_img_col_indexs : list ,img字段的col索引, 一般放在最后几个字段, 因此里面的值只能是负值
    return: str html"""
    assert(np.max(df_img_col_indexs) < 0)
    page = pyh.PyH('report')
    mytab = page << pyh.table()
    for i in range(len(df)):
        mytr = mytab << pyh.tr(style="background-color:%s"%(color))
        v = df.iloc[i][:np.min(df_img_col_indexs)]
        if v.name == 0 and len(v.tolist()) == 1:
            v = v[0]
        s = str(v)
        mytr << pyh.td('<pre style="width:530px;">%s</pre>' % (s), width="20%")	
        for j in df_img_col_indexs:
            img_url = df.iloc[i][df.columns[j]]
            if img_url.find('http') != 0:
                img_url = os.path.basename(img_url)
            mytr << pyh.td('Row %i, column <img src="%s"/>' % (i, img_url))
    return page.render()
def main(args):
    pass

if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)