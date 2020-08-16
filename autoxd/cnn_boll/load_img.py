#coding:utf8
from __future__ import print_function
import os
#import cv2  #opencv-python
import matplotlib.pyplot as pl
import matplotlib.ticker as tic
from PIL import Image
import numpy as np
from autoxd.cnn_boll import env
from autoxd.cnn_boll.pearson_clust import g_fname_csv, load_data as main_load_data
import pandas as pd

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

class Label2Id:
    fname = 'label_desc.csv'
    def __init__(self, reinit=False):
        self.fname = os.path.join(env.get_root_path(), 'datas',self.fname)
        if os.path.exists(self.fname) and reinit==False:
            self.df = pd.read_csv(self.fname)
            #print(self.df)
        else:
            result = self._initLabeDescTable()
            self.df = pd.DataFrame(result)
            self.df.to_csv(self.fname)
            print(self.df)
            print('write label_desc_table')
    def _initLabeDescTable(self):
        decss=[]
        for i in range(3):
            for j in range(3):
                for m in range(3):
                    for n in range(3):    
                        s = ("%d,%d,%d,%d")%(i,j+3,m+6,n+9)
                        decss.append(s)
        return decss
        
    def label_desc_to_label_id(self,label_desc):
        """根据排列组合转为id号
        1,1,1,1=>40
        """
        #a,b,c,d = str(label_desc).split(',')
        #return a*3+b*3+c*3+d*3
        try:
            row = self.df[self.df[self.df.columns[-1]] == label_desc]
            id = row.index[0]
        except:
            return np.nan
        return id
    def get_desc(self, id):
        row = self.df.iloc[id]
        return row[self.df.columns[-1]]
    
def BollsToImg(bolls):
    """归一化处理boll数据, 以mid的平均值作为基准点
    return: np.ndarray, np.shape (3, )
    """
    up,mid,low = bolls
    base = np.average(mid)
    return (bolls-base)/base*10000
    
def load_data(num=-1):
    """加载imgs
    return: (x_train, y_train), (x_test, y_test)
    x_train, np.dnarray  (num, row, col)
    y_train, (num, [0,0,0,1,0,0]) 分类标签
    """
    img_path = os.path.join(env.get_root_path(),'img_labels/imgs/')
    files = os.listdir(img_path)
    files = files[:num]
    datas = None
    pre_code = ''
    imgs = []
    labels = []
    n = 28
    label_converter = Label2Id()
    for f in files:
        fname = img_path + f
        #label
        #这里和pearson_clust里的数据加载有区别， 这里是遍历
        f = f.split('.')[0]
        code, datas_index = str(f).split('_')
        print(code)
        datas_index = int(datas_index)
        label_path = os.path.join(env.get_root_path() ,('datas/%s/%s')%(code, g_fname_csv))
        #... 等待人工标签结果， 人工标签最后再进行归类
        table_colmns = "id,datas_index,code,dt,tick_period,clust_id,label_id,label_desc".split(',')
        df = pd.read_csv(label_path)
        label = df[df[table_colmns[1]] == int(datas_index)]
        label_id = np.nan
        if len(label)>0:
            label = label[table_colmns[-1]].values[0]
            if isinstance(label, str) and label[-1] == ',':
                label = label[:-1]
            label_id = label_converter.label_desc_to_label_id(label)
        labels.append(label_id)
        
        #img
        if pre_code != code:
            datas = main_load_data(code)
        #归一化
        bolls = datas[datas_index]
        img = BollsToImg(bolls)
        img = img.astype(np.uint8)
        #print(img)
        imgs.append(img)
        
    #for i in range(5):
        #imgs += imgs
        #labels += labels
    data = np.array(imgs)
    labels = np.array(labels).astype(np.uint8)
    len_data = len(data)
    len_labels = len(labels)
    assert(len_data == len_labels)
    split_len_pos = int(len_data*0.8)
    return (data[:split_len_pos], labels[:split_len_pos]),(data[split_len_pos:], labels[split_len_pos:])

if __name__ == "__main__":
    #test
    obj = Label2Id(reinit=True)
    id = obj.label_desc_to_label_id('2,3,7,9')
    print(id, obj.get_desc(id))
    print(obj.get_desc(0))
    exit(0)
    
    #from keras.datasets import mnist
    #datas = mnist.load_data()
    #(x_train, y_train), (x_test, y_test) = datas
    ##x_train dtype=uint8
    #print(x_train.shape)
    #exit(0)
    
    (x_train, y_train), (x_test, y_test)  = load_data()
    print(x_train.shape)
    print(y_train.shape)
    #print(data[0])
    from autoxd import agl
    agl.print_ary(x_train[0])

