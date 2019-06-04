#coding:utf8
from __future__ import print_function
import os, cv2
import matplotlib.pyplot as pl
import matplotlib.ticker as tic
from PIL import Image
import numpy as np

# the data, split between train and test sets
#(x_train, y_train), (x_test, y_test) = mnist.load_data()
def load_imgs():
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

load_imgs()

