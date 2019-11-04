#coding:utf8

"""显示第一次聚类后各聚类的中心点
查看聚类结果
"""

import pearson_clust
import pandas as pd
#from autoxd.pandas_autocomplete import *
from autoxd.pypublish import publish

def show_first():
    fname = 'center_indexs_mid.csv'
    datas = pearson_clust.load_data()
    df = pd.read_csv(fname)
    df = df['0']
    indexs = df.get_values()
    print(len(indexs))
    #print(len(indexs))
    #print(len(datas))

    pl = publish.Publish()
    for index in indexs:
        pl.figure
        pearson_clust.draw(datas[index])
        pl.show()
        pl.close()

def show_second():
    fname = 'center_indexs.csv'
    #fname = 'html/'+fname
    datas = pearson_clust.load_csv_data()
    df = pd.read_csv(fname)
    df = df['0']
    indexs = df.get_values()
    print(len(indexs) )
    #print(len(indexs))
    #print(len(datas))

    pl = publish.Publish()
    for index in indexs:
        pl.figure
        pearson_clust.draw(datas[index])
        pl.show()
        pl.close()


if __name__ == "__main__":
    show_first()
    show_second()