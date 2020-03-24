#coding:utf8
from __future__ import print_function
import os
import cv2  #opencv-python
import matplotlib.pyplot as pl
import matplotlib.ticker as tic
from PIL import Image
import numpy as np
from autoxd.cnn_boll import env
from autoxd.cnn_boll.pearson_clust import g_fname_csv

# the data, split between train and test sets
#(x_train, y_train), (x_test, y_test) = mnist.load_data()
def show_imgs():
    img_path = 'img_labels/imgs/'
    files = os.listdir(img_path)
    fig = pl.figure(figsize=(18,10))
    pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)#调整子图间距    
    #fig, ax = pl.subplots(len(files[:10])/4+1, 4,figsize=(20,10))
    #ax2 = np.array(ax).reshape((1,-1))[0]
    col = 6
    for i,f in enumerate(files[:10]):
        print(f)
        fname = img_path + f
        ax = pl.subplot(len(files[:10])/col+1, col, i+1)
        img = Image.open(fname)
        #ax2[i].imshow(np.array(img))
        pl.imshow(np.array(img))
        #temp = tic.MaxNLocator(3)
        #ax.yaxis.set_major_locator(temp)
        #ax.set_xticklabels(())
        ax.title.set_visible(False)        
        #pl.axis('equal')
        pl.axis('off')
    #pl.tight_layout()#调整整体空白
    
    pl.show()        

def load_data():
    """加载imgs
    return: (x_train, y_train), (x_test, y_test)
    x_train, np.dnarray  (num, row, col)
    y_train, (num, [0,0,0,1,0,0]) 分类标签
    """
    img_path = 'img_labels/imgs/'
    files = os.listdir(img_path)
    imgs = []
    labels = []
    n = 28
    for f in files:
        fname = img_path + f
        #label
        #这里和pearson_clust里的数据加载有区别， 这里是遍历
        code = str(f).split('_')[0]
        label_path = (env.get_root_path() + '/datas/%s/%s')%(code, g_fname_csv)
        #... 等待人工标签结果， 人工标签最后再进行归类
        
        #img
        img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (640, 480))
        img = np.array(img)
        img[img==255] = 0
        imgs.append(img)
        
    data = np.array(imgs)
    
    #label
    
    

if __name__ == "__main__":
    #show_imgs()
    
    data = load_data()
    print(data.shape)
    #print(data[0])
    from autoxd import agl
    agl.print_ary(data[0])

