#coding:utf8

"""尝试用pearson来聚类图像
1. 引入已实现的数据加载
2. 对单副图进行pearson比较
3. 比较的结果作为knn的距离
"""
from __future__ import print_function
import pandas as pd
import judge_boll_sign as jbs
from autoxd import pattern_recognition as pr
from autoxd import agl, ui
#import pylab as pl
import matplotlib.pyplot as pl
import numpy as np
from pypublish import publish
from autoxd import policy_report
from PCV.clustering import hcluster
from itertools import combinations
from scipy.cluster.vq import *
from PIL import Image

g_list = []
g_report = []   #比较的结果
#pl = publish.Publish(explicit=True)

def draw(b):
    boll_up, boll_mid, boll_low = b
    closes = np.nan
    #ui.drawBoll(pl, closes, boll_up, boll_mid, boll_low)
    pl.plot(closes)
    pl.plot(boll_up)
    pl.plot(boll_mid)
    pl.plot(boll_low)
    pl.axis('off')

def cmp_boll_two(tuple1, tuple2, id1, id2):
    """对于两个图， 如何象matplotlib一样的变成图"""
    #print(tuple1, tuple2)
    a = tuple1[0]
    b = tuple2[0]
    v_up = pr.pearson_guiyihua(a, b)
    v_down = pr.pearson_guiyihua(tuple1[-1], tuple2[-1])
    fimg1 = ''
    fimg2 = ''
    #if hasattr(pl, 'get_CurImgFname'):
        #draw(tuple1)
        #fimg1 = pl.get_CurImgFname()
        #draw(tuple2)
        #fimg2 = pl.get_CurImgFname()
    if not np.isnan(v_up) and not np.isnan(v_down):
        g_report.append([v_up, v_down, id1, id2, fimg1, fimg2])    
    return v_up, v_down

def cmp_bolls():
    """return: (int) g_list index"""
    indexs = range(len(g_list))
    indexs = indexs[:100]
    indexs2 = agl.array_shuffle(indexs)
    #for i in indexs:
        #j = indexs2[i]
        #v = cmp_boll_two(g_list[j], g_list[i], j, i)
        ##print(agl.float_to_2(v[0]), agl.float_to_2(v[1]))
    return indexs2
    
def load_data():
    """
    """
    codes = ['000005']
    for code in codes:
        datas = jbs.getData(code)   # from local
        upper, middle, lower, df, adx = datas
        if len(df) < 100:
            continue
        if jbs.IsSide(df['c'].values, upper, lower, middle):
            for index in range(100, len(df) - jbs.g_scope_len):
                g_list.append(getBolls(index, datas))

def getBolls(index, datas):
    """画5分钟线的boll图
    index : int
    datas : (ary,ary,ary,df)
    return: u,m,l
    """
    assert(index>=100)
    u,m,l,df,adx = datas
    scope_len = jbs.g_scope_len  #图片尺寸

    #plt.plot([1,2,3])
    index_s = index-scope_len
    if index_s < 0:
        index_s = 0
    #c = jbs.th.filter_close(df['h'].values[index_s:index], df['l'].values[index_s:index], m[index_s:index])
    return u[index_s:index], m[index_s:index], l[index_s:index]

def run():
    """输出两两比较后的列表"""
    load_data()
    print(len(g_list))
    cmp_bolls()
    df = pd.DataFrame(g_report)
    #show_result(df)
    pl.reset(policy_report.df_to_html_table(df, df_img_col_indexs=[-2,-1]))
    pl.publish()
    
def distfn(v1, v2):
    """距离函数, v1: id
    return: float
    """
    #print(v1, v2)
    #v1 = int(v1[0])
    #v2= int(v2[0])
    #print(v1,v2)
    
    v_up = pr.pearson_guiyihua(g_list[v1][0], g_list[v2][0])
    v_down = pr.pearson_guiyihua(g_list[v1][-1], g_list[v2][-1])
    dist = (v_up + v_down) / 2
    return dist

def myhclust():
    """尝试层次聚类"""
    load_data()
    indexs = cmp_bolls()
    
    #写入本地img中
    fname = 'img_labels/hclust_imgs'
    #agl.removeDir(fname)
    #agl.createDir(fname)
    imlist = []
    #for i in range(len(indexs)):
    for i in indexs:
        fname1 =fname + '/img_%s.png'%(i)
        #pl.figure
        #draw(g_list[i])
        #pl.savefig(fname1)
        #pl.close()
        imlist.append(fname1)
    
    #df = pd.DataFrame(g_report)
    # 转换一下数据
    features = [np.array([i]) for i in indexs]
    #features = indexs
        
    #把距离值放入一个id为key的字典
    #dict_distance = {}
    #for v in g_report:
        #ni,nj = v[2:4]
        #dict_distance[ni,nj] = (v[0]+v[1])/2
        

    tree = hcluster.hcluster(features, distfcn=distfn)
    clusters = tree.extract_clusters(0.3 * tree.distance)
    #for c in clusters:
        #elements = c.get_cluster_elements()
        #print(len(elements), elements)        
        #if len(elements)>3:
            #for index in elements:
                #draw(g_list[index])            
    for c in clusters:
        elements = c.get_cluster_elements()
        nbr_elements = len(elements)
        if nbr_elements > 3:
            print(elements)
            pl.figure(figsize=(10,5))
            for i, p in enumerate(elements):
                pl.subplot(4, 5, i + 1)
                pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
                #im = array(Image.open(imlist[elements[p]]))
                #imshow(im)
                draw(g_list[p])
                
            pl.show()
    
    hcluster.draw_dendrogram(tree,imlist,filename='./sunset.png')                
    
    
    print('end')
        
#def test_kmeans():
    #pl = None
    #from scipy.cluster.vq import *
    #from pylab import *
    #class1 = 1.5 * randn(100,2)
    #class2 = randn(100,2) + array([5,5])
    #features = vstack((class1,class2))
    
    ##knn
    #if 0:
        #centroids,variance = kmeans(features,2)
        #code,distance = vq(features,centroids)
        #figure()
        #ndx = where(code==0)[0]
        #plot(features[ndx,0],features[ndx,1],'*')
        #ndx = where(code==1)[0]
        #plot(features[ndx,0],features[ndx,1],'r.')
        #plot(centroids[:,0],centroids[:,1],'go')
        #axis('off')
        #show()    
    
    ##hclust
    #tree = hcluster.hcluster(features)
    #clusters = tree.extract_clusters(0.23 * tree.distance)
    #for c in clusters:
        #elements = c.get_cluster_elements()
        #print(len(elements), )        

def myknn():
    load_data()
    indexs = cmp_bolls()
    
    #写入本地img中
    fname = 'img_labels/hclust_imgs'
    agl.removeDir(fname)
    agl.createDir(fname)
    imlist = []
    #for i in range(len(indexs)):
    for i in indexs:
        pl.figure
        draw(g_list[i])
        fname1 =fname + '/img_%s.png'%(i)
        pl.savefig(fname1)
        pl.close()
        imlist.append(fname1)

    n = len(indexs)
    # 计算距离矩阵
    S = np.array([[ distfn(indexs[i], indexs[j])
    for i in range(n) ] for j in range(n)], 'f')
    # 创建拉普拉斯矩阵
    rowsum = np.sum(S,axis=0)
    D = np.diag(1 / np.sqrt(rowsum))
    I = np.identity(n)
    L = I - np.dot(D, np.dot(S,D))
    # 计算矩阵L 的特征向量
    U,sigma,V = np.linalg.svd(L)
    k = 5
    # 从矩阵L 的前k 个特征向量（eigenvector）中创建特征向量（feature vector）
    # 叠加特征向量作为数组的列
    
    features = np.array(V[:k]).T
    # k-means 聚类
    features = whiten(features)
    centroids,distortion = kmeans(features,k)
    code,distance = vq(features,centroids)
    # 绘制聚类簇
    for c in range(k):
        ind = np.where(code==c)[0]
        figure()
        for i in range(np.minimum(len(ind),39)):
            im = Image.open(imlist[ind[i]])
            subplot(4,10,i+1)
            imshow(array(im))
            axis('equal')
            axis('off')
    show()    
    
def MyKnnImpl():
    """自行实现， 对每个元素， 分别输出70，80，90区间的集合；其实现方式不能简单的套knn和hclust
    并不需要完整的放入集合中
    经过测试，pearson的效果也不好， 只能使用手工打标签了
    """
    load_data()
    indexs = cmp_bolls()
    print(indexs)
    
    #写入本地img中
    fname = 'img_labels/hclust_imgs'
    agl.removeDir(fname)
    agl.createDir(fname)
    imlist = []
    #for i in range(len(indexs)):
    for i in indexs:
        fname1 =fname + '/img_%s.png'%(i)
        pl.figure
        draw(g_list[i])
        pl.savefig(fname1)
        pl.close()
        imlist.append(fname1)

    dist_v = 0.90   #pearson相似度
    n = len(indexs)
    S = np.zeros([n,n])
    for i in range(n):
        for j in range(n):
            S[i,j] = distfn(indexs[i], indexs[j])
    print(S)
    #用选择法，把各元素放到它们相近的集合内
    for i in range(n):
        clust = []
        for j in range(n):
            if S[i,j] > 0.9:
                clust.append(j)
        print(clust)        
        if i<10:
            pl.figure(figsize=(18,10))
            for k,j in enumerate(clust):
                im = Image.open(imlist[indexs[j]])
                pl.subplot(4,5,k+1)
                pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
                pl.imshow(np.array(im))
                pl.axis('equal')
                pl.axis('off')
            pl.show()

            print('end')
if __name__ == "__main__":
    #run()
    #myhclust()
    #myknn()
    #test_kmeans()
    MyKnnImpl()