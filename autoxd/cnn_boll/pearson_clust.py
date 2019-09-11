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
#from PCV.clustering import hcluster
import hcluster_person as hcluster
from itertools import combinations
from scipy.cluster.vq import *
from PIL import Image
from autoxd import myredis
import time
from itertools import combinations
from sklearn.cluster import KMeans
from scipy.cluster import hierarchy

import scipy
import scipy.cluster.hierarchy as sch
from scipy.cluster.vq import vq,kmeans,whiten
import numpy as np
import matplotlib.pylab as plt

import psutil
from autoxd import multi_run

g_list = []
g_report = []   #比较的结果
#pl = publish.Publish(explicit=False)

# 读取样本
g_num = 400
def modify_num_base_cpuinfo():
    global g_num
    #cpu 核心数量
    cpu_num = psutil.cpu_count()
    print('cpu_num:', cpu_num)
    #cpu_ratio = psutil.cpu_times()
    #print('cpu_tims: ', cpu_ratio)
    machine_user_name = psutil.users()[0].name
    print(machine_user_name)
    if cpu_num == 4 and machine_user_name == 'wangkang':
        #it's mac
        g_num = 200
    if cpu_num == 3 and machine_user_name == 'root':
        #docker
        g_num = 2000
    if cpu_num >= 8:
        #remote home
        g_num = 10000
modify_num_base_cpuinfo()        

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

def cmp_bolls(n):
    """return: (int) g_list index"""
    indexs = range(len(g_list))
    indexs = indexs[:n]
    indexs2 = indexs
    #indexs2 = agl.array_shuffle(indexs)
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
    """距离函数, v1: id, g_list的id
    还是加上上下之间的距离， 以最近点的距离作为距离
    (up + down)/2 - up_down_distance*a
    return: float
    """
    assert(type(v1[0]) == np.int64)
    assert(type(v2[0]) == np.int64)
    #print(v1, v2)
    v1 = int(v1[0])
    v2= int(v2[0])
    #print(v1,v2)
    
    v_up = pr.pearson_guiyihua(g_list[v1][0], g_list[v2][0])
    v_down = pr.pearson_guiyihua(g_list[v1][-1], g_list[v2][-1])
    up_down_distance_0 = g_list[v1][0] - g_list[v1][1]
    up_down_distance_1 = g_list[v2][0] - g_list[v2][1]
    up_down_distance_0 = up_down_distance_0[np.isnan(up_down_distance_0) == False]
    up_down_distance_1 = up_down_distance_1[np.isnan(up_down_distance_1) == False]
    up_down_distance_0 = np.min(up_down_distance_0)
    up_down_distance_1 = np.min(up_down_distance_1)
    up_down_distance = np.abs(up_down_distance_0 - up_down_distance_1)
    a = 3
    dist = (v_up + v_down) / 2 - up_down_distance * a
    #if dist < 0:
        #dist = 0.01
    #dist = v_up
    dist = 1-dist
    assert(not np.isnan(dist))
    return dist

def calc_center(clust_elements, distances):
    """计算中心点
    clust_elements: list 传入一个聚类集合的元素列表(indexs)
    distances: dict 全部元素的距离矩阵， 用indexs取两个index之间的距离 , key=(i,j)
    return: index
    """
    assert(len(clust_elements)>1)
    avgs = []
    for i in clust_elements:
        s = 0
        for j in clust_elements:
            if i != j:
                if (i,j) in distances.keys():
                    s += distances[i,j]
                else:
                    s += distances[j,i]
        v = s / (len(clust_elements)-1)
        avgs.append(v)
    pos = agl.array_val_to_pos(np.array(avgs), np.max(avgs))
    print('max_pos = %d, %.2f'%(clust_elements[pos], avgs[pos]))
    pass

def myhclust(indexs):
    """尝试层次聚类"""
    if len(g_list) == 0:
        load_data()
    #indexs = cmp_bolls(g_num)
    print(indexs)
    
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
        
    #在100样本下， 使用0.2比较合适
    tree , distances = hcluster.hcluster(features, distfcn=distfn)
    clusters = tree.extract_clusters(0.2 * tree.distance)
    #for c in clusters:
        #elements = c.get_cluster_elements()
        #print(len(elements), elements)        
        #if len(elements)>3:
            #for index in elements:
                #draw(g_list[index])            
    print('clusters num=', len(clusters))
    def ShowResult():
        for j,c in enumerate(clusters):
            elements = c.get_cluster_elements()
            nbr_elements = len(elements)
            if nbr_elements > 20:
                print(j, elements)
                pl.figure(figsize=(20,10))
                for i, p in enumerate(elements):
                    pl.subplot(max(4,int(np.ceil(len(elements)/5)) ), 5, i + 1)
                    #pl.subplot(4, 5, i + 1)
                    pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
                    #im = array(Image.open(imlist[elements[p]]))
                    #imshow(im)
                    draw(g_list[p])
                    imgname = 'html/%i.png'%(j)
                    pl.savefig(imgname)
                pl.show()
                #pl.clf()
                #pl.close()
    
    #hcluster.draw_dendrogram(tree,imlist,filename='./sunset.png')                
    def combine_clusters():
        """合并一些相近的集合"""
        #watch 
        for i, j in combinations(clusters, 2):
            i = i.get_cluster_elements()
            j = j.get_cluster_elements()
            d = distfn(np.array([i[0]]), np.array([j[0]]))
            print(len(i), len(j), d)
    #combine_clusters()    
    #计算中心点
    for j,c in enumerate(clusters):
        elements = c.get_cluster_elements()
        if(len(elements)>1):
            calc_center(elements, distances)    
    ShowResult()
    print('end')

def test_myhclust():
    load_data()
    indexs = cmp_bolls(g_num)
    myhclust(indexs)
    
def test_multi_myhclust():
    load_data()
    total_len = len(g_list)
    indexs = range(total_len)[:800]
    #myhclust(indexs)
    multi_run.run_fn(myhclust, indexs)
    
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

#def myknn():
    #load_data()
    #indexs = cmp_bolls()
    
    ##写入本地img中
    #fname = 'img_labels/hclust_imgs'
    #agl.removeDir(fname)
    #agl.createDir(fname)
    #imlist = []
    ##for i in range(len(indexs)):
    #for i in indexs:
        #pl.figure
        #draw(g_list[i])
        #fname1 =fname + '/img_%s.png'%(i)
        #pl.savefig(fname1)
        #pl.close()
        #imlist.append(fname1)

    #n = len(indexs)
    ## 计算距离矩阵
    #S = np.array([[ distfn(indexs[i], indexs[j])
    #for i in range(n) ] for j in range(n)], 'f')
    ## 创建拉普拉斯矩阵
    #rowsum = np.sum(S,axis=0)
    #D = np.diag(1 / np.sqrt(rowsum))
    #I = np.identity(n)
    #L = I - np.dot(D, np.dot(S,D))
    ## 计算矩阵L 的特征向量
    #U,sigma,V = np.linalg.svd(L)
    #k = 5
    ## 从矩阵L 的前k 个特征向量（eigenvector）中创建特征向量（feature vector）
    ## 叠加特征向量作为数组的列
    
    #features = np.array(V[:k]).T
    ## k-means 聚类
    #features = whiten(features)
    #centroids,distortion = kmeans(features,k)
    #code,distance = vq(features,centroids)
    ## 绘制聚类簇
    #for c in range(k):
        #ind = np.where(code==c)[0]
        #figure()
        #for i in range(np.minimum(len(ind),39)):
            #im = Image.open(imlist[ind[i]])
            #subplot(4,10,i+1)
            #imshow(array(im))
            #axis('equal')
            #axis('off')
    #show()    

def calcCenterId(clusters):
    """找到集合里中心的点
    clusters: list clust id的集合, indexs
    return: 数据源索引 index"""
    avgs = []
    for i in clusters:
        s = 0
        for j in clusters:
            if i != j:
                s += distfn(i, j)
        v = s / (len(clusters)-1)
        avgs.append(v)
    pos = agl.array_val_to_pos(np.array(avgs), np.max(avgs))
    print('max_pos = %d, %.2f'%(pos, avgs[pos]))
    
def MyKnnImpl():
    """自行实现， 对每个元素， 分别输出70，80，90区间的集合；其实现方式不能简单的套knn和hclust
    并不需要完整的放入集合中
    经过测试，聚类效果比pca等好
    """
    #pl = publish.Publish()

    load_data()
    indexs = cmp_bolls()
    print(indexs)
    
    use_redis = 1
    #key = myredis.gen_keyname(__file__, MyKnnImpl)
    #if not use_redis:
        #myredis.delkey(key)
    #else:
        ##用redis保存
        #indexs = myredis.createRedisVal(key, indexs).get()
    #print(indexs)

    #写入本地img中
    fname = 'img_labels/hclust_imgs'
    if not use_redis:
        agl.removeDir(fname)
        agl.createDir(fname)
    imlist = []
    #for i in range(len(indexs)):
    for i in indexs:
        fname1 =fname + '/img_%s.png'%(i)
        if not use_redis:
            pl.figure
            draw(g_list[i])
            pl.savefig(fname1)
            pl.close()
        imlist.append(fname1)
    if use_redis == 0:
        return


    dist_v = 0.90   #pearson相似度
    n = len(indexs)
    S = np.zeros([n,n])
    for i in range(n):
        for j in range(n):
            S[i,j] = distfn(i, j)
    #print(S)
    
    def IsInClust(i, clusts):
        is_in_clusts = False
        for clust1 in clusts:
            if i in clust1:
                is_in_clusts = True
                break
        return is_in_clusts
    
    #用选择法，把各元素放到它们相近的集合内
    clusts = []
    for i in range(n):
        if IsInClust(i, clusts):
            continue
        clust = []
        for j in range(n):
            if S[i,j] > 0.8:
                #print(S[i,j],)
                if not IsInClust(j, clusts):
                    clust.append(j)
        print(i,clust)
        clusts.append(clust)
        if len(clust)>=4:
            calcCenterId(clust)

    def split_min_and_combo_to_max(clusts):
        """分拆小的集合， 合并到大的集合"""
        pass
        
        #if i>20 and len(clust)>3 and len(clust)<20:
            #print(i, clust)        
            ##print(i, len(clust))
            #if not publish.IsPublish(pl):
                #pl.figure(figsize=(10,8))
            #else:
                #pl.figure
            #for k,j in enumerate(clust):
                #im = Image.open(imlist[j])
                #pl.subplot(4,5,k+1)
                #pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
                #pl.imshow(np.array(im))
                #pl.axis('equal')
                #pl.axis('off')
            #pl.show()
            #print('end')
            ##time.sleep(5)
            #pl.close()
    #pl.publish()
            
    
class MyHCluster:
    """调用scipy的层次聚类
    鉴于层次算法也是需要计算合并后的平均值的，不计算平均值， 给两个图形进行合并，合并成新的图形后再与所有的图形重新比较一次， 再选取最优值合并， 重复这个过程
    """
    def __init__(self):
        load_data()
    def _show(self, cluster_ids):
        pl.figure(figsize=(10,5))
        for i, p in enumerate(cluster_ids):
            pl.subplot(4, 5, i + 1)
            pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
            draw(g_list[p])
        pl.show()
    def _comboBoll(self, id1, id2):
        pass
    
    def clust_person(self):
        points = []
        for i in range(100):
            points.append(np.array([i]))
        points = np.array(points)
        disMat = sch.distance.pdist(points, distfn)
        disMat[np.isnan(disMat)==True] = 0
        print(disMat)
        Z=sch.linkage(disMat,method='average') 
        cluster= sch.fcluster(Z, t=1, criterion='inconsistent') 
        print("Original cluster by hierarchy clustering:\n",cluster)            
        max_clust = np.max(cluster)
        for i in range(max_clust):
            i = i+1
            cluster_ids = np.where(cluster == i)[0]
            print(cluster_ids)
            self._show(cluster_ids)
        print('')
    def sample(self):
        
        points=scipy.randn(20,1)  
        print(points)
        
        #1. 层次聚类
        #生成点与点之间的距离矩阵,这里用的欧氏距离:
        #disMat = sch.distance.pdist(points,'euclidean') 
        #print(disMat)
        def _distfn(u,v):
            return np.sqrt((u-v)**2).sum()
        disMat = sch.distance.pdist(points, _distfn)
        print(disMat)
        #进行层次聚类:
        Z=sch.linkage(disMat,method='average') 
        #将层级聚类结果以树状图表示出来并保存为plot_dendrogram.png
        P=sch.dendrogram(Z)
        plt.savefig('plot_dendrogram.png')
        #根据linkage matrix Z得到聚类结果:
        cluster= sch.fcluster(Z, t=1, criterion='inconsistent') 
        
        print("Original cluster by hierarchy clustering:\n",cluster)            
if __name__ == "__main__":
    #run()
    t = agl.tic_toc()
    #myhclust()
    #test_myhclust()
    test_multi_myhclust()
    #myknn()
    #test_kmeans()
    #MyKnnImpl()
    #MyHCluster().sample()
    #MyHCluster().clust_person()