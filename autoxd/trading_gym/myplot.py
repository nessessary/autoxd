#coding:utf8

"""把矩阵转换为view上的点"""

import numpy as np
import pandas as pd
import pylab as pl
#from autoxd.stock import GuiYiHua
from autoxd.pypublish import publish
from autoxd import agl
#from sklearn.preprocessing import minmax_scale

def convert(view_width, view_height, df):
    """转换值到屏幕点， pyglet的视图是以左下角为0,0
    return: list df的每一列 [[x,y],...]
    """
    #先把df按最大最小归一化
    max_value = df.values.max()
    min_value = df.values.min()
    #print(max_value, min_value)
    df = df - min_value
    df = df / (max_value -min_value)
    # 把归一化得值乘以高
    df = df * (view_height -10) + 5
    
    lines = []
    for i in range(len(df.columns)):
        a = np.zeros((len(df), 2))
        x = df[df.columns[i]].values
        #y = range(0, view_width, int(view_width/len(df)))
        y = np.arange(len(x))
        y = y * (view_width / len(x))
        assert(len(x)==len(y))
        a[:,1] = x
        a[:,0] = y
        lines.append(a)
    # 数值得长度与宽匹配
    
    return lines

def test():
    width = 600
    height = 400
    a = np.random.rand(30,4)*100
    print(a)
    df = pd.DataFrame(a)
    pl = publish.Publish()
    df.plot()
    pl.show()
    pl.close()
    v = convert(width, height, df)
    #filter(lambda x:pl.scatter(x[0],x[1]), v )
    for x in v:
        pl.scatter(x[:,0], x[:,1])
        pl.show()
        pl.close()
    print("")

if __name__ == "__main__":
    test()