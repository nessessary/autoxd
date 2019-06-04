# -*- coding: utf-8 -*-
from PCV.tools import pca
from PIL import Image, ImageDraw
from pylab import *
from PCV.clustering import  hcluster
import os
import numpy as np
import pandas as pd

def get_imlist_png(path):
    """    Returns a list of filenames for 
        all jpg images in a directory. """
        
    return [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.png')]

img_path = 'img_labels/imgs/'
imlist = get_imlist_png(img_path)
imnbr = len(imlist)

# Load images, run PCA.
#immatrix = array([array(Image.open(im)).flatten() for im in imlist], 'f')
#图片太大的话array会内存不够， 改为numpy
#immatrix = np.array([np.array(Image.open(im)).flatten() for im in imlist], dtype=np.float)
immatrix = None
for i, im in enumerate(imlist):
    v = array(Image.open(im)).flatten()
    if immatrix is None:
        immatrix = np.array([v], dtype = np.float)
    else:
        immatrix = np.insert(immatrix, 1, v, axis=0)
V, S, immean = pca.pca(immatrix)

# Project on 2 PCs.
projected = array([dot(V[[0, 1]], immatrix[i] - immean) for i in range(imnbr)])  # P131 Fig6-3左图
#projected = array([dot(V[[1, 2]], immatrix[i] - immean) for i in range(imnbr)])  # P131 Fig6-3右图

# height and width
h, w = 1200, 1200

# create a new image with a white background
img = Image.new('RGB', (w, h), (255, 255, 255))
draw = ImageDraw.Draw(img)

# draw axis
draw.line((0, h/2, w, h/2), fill=(255, 0, 0))
draw.line((w/2, 0, w/2, h), fill=(255, 0, 0))

# scale coordinates to fit
scale = abs(projected).max(0)
scaled = floor(array([(p/scale) * (w/2 - 20, h/2 - 20) + (w/2, h/2)
                      for p in projected])).astype(int)

# paste thumbnail of each image
for i in range(imnbr):
    nodeim = Image.open(imlist[i])
    nodeim.thumbnail((25, 25))
    ns = nodeim.size
    box = (scaled[i][0] - ns[0] // 2, scaled[i][1] - ns[1] // 2,
         scaled[i][0] + ns[0] // 2 + 1, scaled[i][1] + ns[1] // 2 + 1)
    img.paste(nodeim, box)

#tree = hcluster.hcluster(projected)
#hcluster.draw_dendrogram(tree,imlist,filename='output_img/fonts.png')

figure()
imshow(img)
axis('off')
img.save('output_img/pca_font.png')
show()
