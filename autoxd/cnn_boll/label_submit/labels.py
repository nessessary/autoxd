#coding:utf8

"""处理labels表, 用csv处理"""
from __future__ import print_function
import os
import pandas as pd
#from autoxd import agl
from autoxd.cnn_boll.pearson_clust import get_result_csv_path

class LabelTable(object):
    """标签表, datas/cnn_boll_label.csv"""
    def __init__(self):
        fname = 'cnn_boll_label.csv'
        self.fname = self._get_datas_dir() + "/" + fname
        if os.path.isfile(self.fname):
            self.df = pd.read_csv(self.fname,index_col=0)
        else:
            self.df = pd.DataFrame([])
        #print(self.df)
    def _get_datas_dir(self):
        cur_dir = os.path.abspath(os.path.dirname(__file__) + '/..')
        cur_dir += '/datas'
        return cur_dir
    def query(self):
        """return: list"""
        return self.df[self.df.columns[0]].values
    def save(self, new_label):
        """需要保持唯一
        return: bool 插入是否成功"""
        if new_label in self.query():
            return False
        df = pd.DataFrame([new_label])
        if len(self.df) >0:
            df.columns = self.df.columns
        self.df = pd.concat([self.df,df], ignore_index=True, axis =0)
        self.df.to_csv(self.fname)
        return True
    
def test():
    obj = LabelTable()
    obj.save('aaaa')
    #print(obj._get_datas_dir())
    print(obj.df)
#test()  
#test()

#主入口函数
def save_labels(new_label, labels, index):
    """更新label表(datas/cnn_boll_label.csv)，并写入(center_indexs_mid.csv?)标签label_ids
    \n:new_label: str
    \n:labels: str split(',') "1,4,6"
    \n:index: center_index.csv里的id
    \n:return: bool 是否已经处理完了
    """
    assert(isinstance(index, int))
    assert(labels is not None)
    table = LabelTable()
    if len(new_label)>0:
        if table.save(new_label):
            #把新添加的label插入到已记录的结果集合中
            if len(labels)> 0:
                if labels[-1] != ',':
                    labels += ','
            labels += str(len(table.df)) + ","
    return insert_labels_to_center_table(index, labels)
        
def get_result_table_path():
    return get_result_csv_path()

def insert_labels_to_center_table(i, labels):
    """打开csv修改后写回
    i: int df的索引
    labels: str "2,3"
    return: bool i大于df长度
    """
    fname = get_result_table_path()
    df = pd.read_csv(fname, index_col=0)
    df[df.columns[-1]] = df[df.columns[-1]].astype(str)
    df.iat[i, -1] = labels
    #print(df.head(), df.columns)
    df.to_csv(fname)
    if i == len(df)-1:
        #已到结尾
        return False
  
    return True

#insert_labels_to_center_table(1, "aa,bbb")
def get_data_table():
    """return: df"""
    fname = get_result_table_path()
    df = pd.read_csv(fname, index_col=0)
    return df    

def test_save_labels():
    new_label = 'kkk'
    labels = '1,3'
    index = 2
    save_labels(new_label, labels, index)    
    print(LabelTable().query())
    fname = get_result_table_path()
    df = pd.read_csv(fname, index_col=0)
    print(df.head())
if __name__ == "__main__":
    test_save_labels()