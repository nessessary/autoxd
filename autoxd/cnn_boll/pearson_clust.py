#coding:utf8

"""尝试用pearson来聚类图像
1. 引入已实现的数据加载
2. 对单副图进行pearson比较
3. 比较的结果作为knn的距离
并行处理
1. 在虚拟机docker里， 样本不能设置的过大， 单个进程处理4000会引起内存错误， 3000太慢， 可能2000正好
2. 找到聚类后的中心点， 作为该集合的代表， 记录在原始数据中的索引， 再把这些中心点做一次聚类， 最后根据图形来设置编号label
3. 测试数据源的分段， 一次处理掉全部的数据， 分段抛入执行， 记录数据偏移
4. 产生的数据集需要带上一个id， 带上时间， 数值
5. 保存中心点的基于数据源的索引, 加上切片偏移
"""
from __future__ import print_function
import os, optparse, sys
import pandas as pd
import autoxd.cnn_boll.judge_boll_sign as jbs
from autoxd import pattern_recognition as pr
from autoxd import agl, ui
#import pylab as pl
import matplotlib.pyplot as pl
import numpy as np
from pypublish import publish
from autoxd import policy_report
#from PCV.clustering import hcluster
import autoxd.cnn_boll.hcluster_person as hcluster
from itertools import combinations
from scipy.cluster.vq import *
from PIL import Image
from autoxd import myredis, stock
from autoxd.cnn_boll.env import get_root_path
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
from autoxd.MultiSubProcess import MultiSubProcess

#数据源取值间隔步长
g_data_interval = 3

g_report = []   #比较的结果
#pl = publish.Publish(explicit=False)
class MyCode:
    g_code_name = "pearson_clust.code"
    @staticmethod
    def get():
        key = MyCode.g_code_name
        code = myredis.get_obj(key)
        if code is None:
            code = "000005"
        return code
    @staticmethod
    def set(code):
        key = MyCode.g_code_name
        myredis.set_obj(key, code)

# 读取样本
def get_process_block_num():
    """根据机器的cpu数量来获取数据块长度"""
    num = 400
    #cpu 核心数量
    cpu_num = psutil.cpu_count()
    print('cpu_num:', cpu_num)
    #cpu_ratio = psutil.cpu_times()
    #print('cpu_tims: ', cpu_ratio)
    machine_user_name = psutil.users()[0].name
    print(machine_user_name)
    if cpu_num == 4 and machine_user_name == 'wangkang':
        #it's mac
        num = 200
    if cpu_num == 3 and machine_user_name == 'root':
        #docker
        num = 1500
    if cpu_num >= 8:
        #remote home
        num = 4000
    return num

def draw(b):
    """根据boll值画图"""
    boll_up, boll_mid, boll_low = b
    closes = np.nan
    #ui.drawBoll(pl, closes, boll_up, boll_mid, boll_low)
    pl.plot(closes)
    pl.plot(boll_up)
    pl.plot(boll_mid)
    pl.plot(boll_low)
    pl.axis('off')

def draw_multi(datas, clusts_index, datas_offset, ids, center_index):
    """画多个id到一幅图上"""
    elements = ids
    pl.figure(figsize=(20,10))
    for i, p in enumerate(elements):
        pl.subplot(max(4,int(np.ceil(len(elements)/5)) ), 5, i + 1)
        #pl.subplot(4, 5, i + 1)
        pl.subplots_adjust(wspace =0.01, hspace =0.01, left=0, right=1, bottom=0,top=1)
        #im = array(Image.open(imlist[elements[p]]))
        #imshow(im)
        draw(datas[p])
        #如果是中心点，右上角画一个点， 或画一个红色的外框
        if p+datas_offset == center_index:
            boll_up, boll_mid, boll_low = datas[p]
            h = np.max(boll_up)
            l = np.min(boll_low)
            left = 0
            right = len(boll_low)-1
            ui.Rectangle(pl, datas[p], h, l, left, right, clr='r', linewidth=1)
        imgname = 'html/%i_%s.png'%(clusts_index+datas_offset, str(os.getpid()) )
        pl.savefig(imgname)
    pl.show()
    #pl.clf()
    #pl.close()

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

def load_data(code=''):
    """加载数据, 加载注册的code
    return: list, bolls
    """
    l = []
    if code == "":
        code = MyCode.get()
    codes = [code]
    for code in codes:
        datas = jbs.getData(code)   # from local
        upper, middle, lower, df, adx = datas
        if len(df) < 100:
            continue
        for index in range(100, len(df) - jbs.g_scope_len, g_data_interval):
            l.append(getBolls(index, datas))
    return l

def load_csv_data(islast=False):
    """从csv中获取数据， 为第一次计算的结果, 同load_data
    return: np.ndarray"""
    fname = get_result_mid_csv_path()
    if islast:
        fname = get_result_csv_path()
    df = pd.read_csv(fname)
    df = df[df.columns[0]]
    indexs = np.array(df.tolist())
    datas = load_data()
    datas = np.array(datas)
    return datas[indexs]

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

   
def distfn(v1, v2, l):
    """距离函数, v1: id, g_list的id
    还是加上上下之间的距离， 以最近点的距离作为距离
    (up + down)/2 - up_down_distance*a
    return: float
    """
    assert(type(v1[0]) == np.int64 or type(v1[0]) == np.int32)
    assert(type(v2[0]) == np.int64 or type(v2[0]) == np.int32)
    #print(v1, v2)
    v1 = int(v1[0])
    v2= int(v2[0])
    #print(v1,v2)
    
    v_up = pr.pearson_guiyihua(l[v1][0], l[v2][0])
    v_down = pr.pearson_guiyihua(l[v1][-1], l[v2][-1])
    up_down_distance_0 = l[v1][0] - l[v1][1]
    up_down_distance_1 = l[v2][0] - l[v2][1]
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
    #assert(len(clust_elements)>1)
    if len(clust_elements) == 1:
        return clust_elements[0]
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
    #print('max_pos = %d, %.2f'%(clust_elements[pos], avgs[pos]))
    return clust_elements[pos]

g_fname_csv = 'center_indexs.csv'
g_fname_mid_csv = 'center_indexs_mid.csv'
def genImgToFile(code):
    """产生图形到文件
    """
    datas = load_data()
    #    indexs: list 数据偏移索引
    df = pd.read_csv(get_result_csv_path(), index_col=0)
    indexs = df['datas_index'].values
    cur_dir = get_root_path()
    fname = cur_dir + '/img_labels/imgs'
    if not os.path.exists(fname):
        agl.createDir(fname)
    for i in indexs:
        i = int(i)
        fname1 =fname + '/%s_%d.png'%(code, i)
        print(fname1)
        pl.figure
        draw(datas[i])
        pl.savefig(fname1)
        pl.close()

def myhclust(datas, indexs):
    """尝试层次聚类, 因为大样本会造成计算速度过慢， 因此不能2000的切片
    datas: list or np.ndarray 数据源
    indexs: array 索引, 按顺序的索引列表，不支持打乱
    return: df 中心点
    """
    offset = indexs[0]
    #l = load_data()
    l = datas
    print("num=%d, total_num = %d"%(len(indexs), len(l)))
    l = l[indexs[0]:indexs[-1]]
    indexs = range(indexs[-1]-indexs[0])
    assert(len(indexs) == len(l))

    #原始数据集
    code = MyCode.get()
    tick_period = jbs.g_scope_len    
    df_datas = jbs.getData(code)[3]

    #写入本地img中
    fname = 'img_labels/hclust_imgs'
    #agl.removeDir(fname)
    #agl.createDir(fname)
    #imlist = []
    ##for i in range(len(indexs)):
    #for i in indexs:
        #fname1 =fname + '/img_%s.png'%(i)
        ##pl.figure
        ##draw(g_list[i])
        ##pl.savefig(fname1)
        ##pl.close()
        #imlist.append(fname1)
    
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
    tree , distances = hcluster.hcluster(features, l, distfcn=distfn)
    clusters = tree.extract_clusters(0.2 * tree.distance)
    center_indexs = []        # 保存中心点       
    center_indexs_columns = ['datas_index', 'code', 'dt', 'tick_period',  'clust_id', 'label_id', 'label_desc']
    print('clusters num=', len(clusters))
    def ShowResult():
        img_dir = 'html/'
        agl.removeDir(img_dir)
        for j,c in enumerate(clusters):
            elements = c.get_cluster_elements()
            nbr_elements = len(elements)
            center_index = calc_center(elements, distances) + offset
            
            #添加的字段
            dt = df_datas.index[center_index]
            clust_id = j
            label_id = 0
            label_desc = ''
            
            center_indexs.append([center_index, code, dt, tick_period, clust_id, label_id, label_desc])
            print(j, center_index, len(elements),elements)
            #if nbr_elements >= 6:
                #draw_multi(l, j, offset, elements, center_index)
    
    #hcluster.draw_dendrogram(tree,imlist,filename='./sunset.png')                
  
    ShowResult()
    df = pd.DataFrame(center_indexs, columns=center_indexs_columns)
    print(df)
    return df

def run_myclust():
    """按切片顺序跑完整个数据源"""
    datas = load_data()
    block_len = 300
    split_indexs = np.array_split(range(len(datas)), len(datas)/block_len)
    for i, indexs in enumerate(split_indexs):
        print("it's batchid=%d [%d,%d]"%(i,indexs[0], indexs[-1]))
        df = myhclust(datas, indexs)

def myclust_split_run(indexs):
    """把indexs再切片执行"""
    datas = load_data()
    block_len = get_process_block_num()
    print(indexs)
    split_block = len(indexs)/block_len
    if split_block < 1:
        split_block = 1
    split_indexs = np.array_split(indexs, split_block)
    df = pd.DataFrame([])
    for i , indexs in enumerate(split_indexs):
        print("it's batchid=%d [%d,%d]"%(i,indexs[0], indexs[-1]))
        df_cur = myhclust(datas, indexs)
        df = pd.concat([df, df_cur])
    return df

def test_myhclust():
    """跑单进程小数据"""
    a = range(900)
    a = a[300:600]
    #df = myhclust(load_data(), a)
    df = myclust_split_run(a)
    #np.savetxt('center_indexs.txt', center_indexs)
    save_result(df)
def save_result(df):    
    fname = get_result_mid_csv_path()
    cur_dir = os.path.dirname(fname)
    print(cur_dir)
    agl.createDir(cur_dir)
    assert(os.path.exists(cur_dir))
    df.to_csv(fname)
    
def test_second_myhclust():
    """对已经聚类的点再聚类一次"""
    datas = load_csv_data()
    indexs = range(len(datas))
    df = myhclust(datas, indexs)
    
    #替换为mid表的记录
    fname = get_result_mid_csv_path()
    df_mid = pd.read_csv(fname)
    for i, row in df.iterrows():
        index = row['datas_index']
        df.at[i, 'datas_index'] = df_mid.iloc[index]['datas_index']
        col = 'dt'
        df.at[i, col] = pd.Timestamp(df_mid.iloc[index][col])
    
    fname = get_result_csv_path()
    df.to_csv(fname)
    

def get_result_path():
    cur_dir = get_root_path()
    dir_path = 'datas/' + MyCode.get() + '/'
    cur_dir += '/'
    cur_dir += dir_path
    agl.createDir(cur_dir)
    return cur_dir
def get_result_mid_csv_path():
    return get_result_path() + g_fname_mid_csv
def get_result_csv_path():
    return get_result_path() + g_fname_csv

def test_multi_myhclust():
    datas = load_data()
    #datas = datas[:6000]
    a = range(len(datas))
    df, = MultiSubProcess.run_fn(myclust_split_run, a, __file__)
    save_result(df)
    
if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('--single', dest='single', action="store_true", help='单进程执行')
    parser.add_option('--multi', dest='multi', action="store_true", help="多进程执行")
    parser.add_option('--second', dest='second', action="store_true", help="第二阶段")
    parser.add_option('--genimg', dest='genimg', action="store_true", help="生成图片文件")
    parser.add_option('--code', dest='code', action="store", type="string", help="get codes")
    
    options, args = parser.parse_args(sys.argv[1:])
    
    #run()
    agl.tic()
    if options.code is not None:
        code = options.code
        if code == 'next':
            code = MyCode.get()
            codes = stock.get_codes()
            codes = np.array(codes)
            index = int(np.argwhere(codes == code))
            if index +1 < len(codes):
                code = codes[index+1]
                MyCode.set(code)
                print("index=%d"%(index))
            else:
                print("end")
        else:
            MyCode.set(code)
        print("current_code=%s"%(code))
    else:
        print('\t--single\t单进程执行\n\t--multi\t多进程执行\n\t--second \t第二阶段\n\t--code=code or next\t\n')
        
    #run_myclust()
    if options.single is not None:
        test_myhclust()
    elif options.multi is not None:
        test_multi_myhclust()
    elif options.second is not None:
        test_second_myhclust()
    elif options.genimg is not None:
        code = MyCode.get()
        genImgToFile(code)
    
    agl.toc()