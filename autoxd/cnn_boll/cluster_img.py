# -*- coding: utf-8 -*-

"""聚类相似图片， 生成层分类, 参考ch6_julei_img.py"""

import os, shutil
#import Image
from PIL import Image
from PCV.clustering import hcluster
from matplotlib.pyplot import *
from numpy import *
import numpy as np
from autoxd import agl

#只选用图片后部的尺寸
#img_back_size = 30
img_distance = 0.05      #0.05
clusters_num = 1        #分类后的数量, 3个

#img_path = 'C:/chromium/src/autoxd3/python/cnn_boll/img_labels/imgs/'
img_path = 'img_labels/imgs/'
# create a list of images
path = img_path
imlist = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.png')]
imlist = agl.array_shuffle(imlist)
imlist = imlist[:2000]
# extract feature vector (8 bins per color channel)
features = zeros([len(imlist), 512])
for i, f in enumerate(imlist):
    im = array(Image.open(f))
    # multi-dimensional histogram
    h, edges = histogramdd(im.reshape(-1, 3), 8, normed=True, range=[(0, 255), (0, 255), (0, 255)])
    features[i] = h.flatten()
tree = hcluster.hcluster(features)

# visualize clusters with some (arbitrary) threshold
clusters = tree.extract_clusters(img_distance * tree.distance)
base_dir = 'datas/' 
# plot images for clusters with more than 3 elements
for i,c in enumerate(clusters):
    elements = c.get_cluster_elements()
    nbr_elements = len(elements)
    if nbr_elements >= clusters_num:
        for e in elements:
            print(imlist[e], i, c.get_depth(), c.get_height())
            dst = base_dir + str(i)
            if not os.path.isdir(dst):
                os.makedirs(dst)
            src = imlist[e]
            shutil.copy(src, dst)        
        #figure(figsize=(18,10))
        #for p in range(minimum(nbr_elements,20)):
            #subplot(4, 5, p + 1)
            #subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
            #im = array(Image.open(imlist[elements[p]]))
            #imshow(im)
            #axis('off')
#show()

hcluster.draw_dendrogram(tree,imlist,filename='./sunset.png')

    