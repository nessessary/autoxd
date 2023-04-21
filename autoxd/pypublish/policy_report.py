#-*- coding:utf-8 -*-
import os
import numpy as np
import pandas as pd
import sys
import pyh
from autoxd import agl

def df_to_html_table(df: pd.DataFrame, color='white'):
    """df转化为html表格输出, 有图片字段的话按图片输出 ; 自动获取img col
    df : 数据源
    color : background
    return: str html
    
    #sample##
    df = pd.DataFrame( [["1","2","img_path1", "img_path2"]] )
    df_to_html_table(df)
    """
    assert(len(df) > 0)
    # 找到img字段 ， 不需要在一起
    df_img_col_indexs = []
    for i, v in enumerate(df.iloc[0]):
        if os.path.isfile(str(v)):
            df_img_col_indexs.append(i)
    
    page = pyh.PyH('report')
    mytab = page << pyh.table()
    for i in range(len(df)):
        mytr = mytab << pyh.tr(style="background-color:%s"%(color))
        s = ''
        row = df.iloc[i]
        row = row.drop(df.columns[df_img_col_indexs])
        if len(row.tolist()) == 1:
            row = row[0]        
        s = str(row)
        #for j, v in enumerate(df.iloc[i]):
            #if j not in df_img_col_indexs:
                #s += str(df.columns[j]) + ' : ' + str(v) + '<br>'
        mytr << pyh.td('<pre>%s</pre>' % (s))	
        for j in df_img_col_indexs:
            mytr << pyh.td('Row %i, column <img src="%s"/>' % (i, os.path.basename(df.iloc[i][df.columns[j]])))	
    return page.render()

