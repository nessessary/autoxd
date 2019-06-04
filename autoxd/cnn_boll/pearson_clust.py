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
    indexs = range(len(g_list))
    indexs = indexs[:100]
    indexs2 = agl.array_shuffle(indexs)
    for i in indexs:
        j = indexs2[i]
        v = cmp_boll_two(g_list[j], g_list[i], j, i)
        #print(agl.float_to_2(v[0]), agl.float_to_2(v[1]))
    return indexs2
    
def load_data():
    """包含"""
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

def myhclust():
    """尝试层次聚类"""
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
    
    #df = pd.DataFrame(g_report)
    # 转换一下数据
    features = indexs
    #把距离值放入一个id为key的字典
    dict_distance = {}
    for v in g_report:
        ni,nj = v[2:4]
        dict_distance[ni,nj] = (v[0]+v[1])/2
        
    def distfn(v1, v2):
        """距离函数, v1: id
        return: float
        """
        #print(v1, v2)
        v1 = v1.max()
        v2= v2.max()
        #使用负值是因为底层使用更小的数来判断最小值
        #判断最接近1的值
        if (v1,v2) in dict_distance.keys():
            return 1-dict_distance[v1,v2]
        return 10
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
        
if __name__ == "__main__":
    #run()
    myhclust()
    #test_kmeans()
