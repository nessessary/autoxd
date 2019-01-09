#coding:utf8

"""把矩阵转换为view上的点"""

import os
import numpy as np
import pandas as pd
import pylab as pl
#import matplotlib.pyplot as pl
#from autoxd.stock import GuiYiHua
from autoxd.pypublish import publish
from autoxd import agl
#from sklearn.preprocessing import minmax_scale
import cv2

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

def df_to_img_martix(df, n):
    """生成df到目录img
    return: np.ndarray shape(n,n)"""
    pl = publish.Publish(explicit=True, is_clear_path=True)
    df.plot(legend=False)
    pl.axis('off')
    pl.show()
    fname = pl.get_CurImgFname()
    pl.close()
    #print(fname)
    
    img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (n,n))
    return img

if 0: df_to_imgs = np.array
def df_to_imgs(df, m, n, bInit=False):
    """df转imgs, 生成成功后会保存到img.npy中，如果有npy则直接读取
    m: int 中间切分的大小, df_len
    n: int 每一个片的长度, img_col_row
    bInit: True 重新初始化, False 使用本地存储
    return: np.ndarray shape(m,n,n)
    """
    fname = 'imgs.npy'
    if os.path.isfile(fname) and bInit==False:
        return np.load(fname)
    l = len(df)-m
    imgs = np.zeros((l,n,n), dtype=np.float)
    for i in range(0, l):
        cur_df = df[i:i+m]
        imgs[i] = df_to_img_martix(df, n)
    np.save(fname, imgs)
    return imgs
        
def test():
    width = 300
    height = 300
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
    
def test_df_to_img_martix():

    a = np.random.rand(30,4)*100
    #print(a)
    df = pd.DataFrame(a)
    img = df_to_img_martix(df, 60)
    print(img.shape)

def test_df_to_imgs():
    a = np.random.rand(40,4)*100
    #print(a)
    df = pd.DataFrame(a)
    imgs = df_to_imgs(df, 30, 128)
    print(imgs.shape)
    #fname = 'imgs'
    #np.save(fname, imgs)
    #fname += '.npy'
    #imgs = np.load(fname)
    #print(imgs.shape)

if __name__ == "__main__":
    #test()
    #test_df_to_img_martix()
    test_df_to_imgs()
