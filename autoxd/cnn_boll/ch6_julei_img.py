    # -*- coding: utf-8 -*-
import os
#import Image
from PIL import Image
from PCV.clustering import hcluster
from matplotlib.pyplot import *
from numpy import *

img_path = '/img_labels/imgs/'
img_path = os.path.dirname(os.path.abspath(__file__)) + img_path
# create a list of images
path = '../data/sunsets/flickr-sunsets-small/'
path = img_path
imlist = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.png')]
# extract feature vector (8 bins per color channel)
features = zeros([len(imlist), 512])
for i, f in enumerate(imlist):
    im = array(Image.open(f))
    # multi-dimensional histogram
    h, edges = histogramdd(im.reshape(-1, 3), 8, normed=True, range=[(0, 255), (0, 255), (0, 255)])
    features[i] = h.flatten()
tree = hcluster.hcluster(features)

# visualize clusters with some (arbitrary) threshold
clusters = tree.extract_clusters(0.23 * tree.distance)
# plot images for clusters with more than 3 elements
for c in clusters:
    elements = c.get_cluster_elements()
    nbr_elements = len(elements)
    if nbr_elements > 3:
        figure(figsize=(18,10))
        for p in range(minimum(nbr_elements,20)):
            subplot(4, 5, p + 1)
            subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
            im = array(Image.open(imlist[elements[p]]))
            imshow(im)
            axis('off')
show()

hcluster.draw_dendrogram(tree,imlist,filename='./sunset.png')
    