#coding:utf8

"""处理labels表, 用csv处理"""
from __future__ import print_function
import os
import pandas as pd
#from autoxd import agl

class LabelTable(object):
    """标签表"""
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
    """更新label表，并写入标签label_ids
    new_label: str
    labels: str split(',')
    index: center_index.csv里的id
    """
    obj = LabelTable()
    if new_label is not None:
        if obj.save(new_label):
            #把新添加的label插入到已记录的结果集合中
            if labels[-1] != ',':
                labels += ','
            labels += str(len(obj.df))
    if labels is not None:
        insert_labels_to_center_table(index, labels)
        
def get_result_table_path():
    cur_dir = os.path.abspath(os.path.dirname(__file__) + '/..')
    fname = cur_dir + '/center_indexs.csv'
    return fname    
def insert_labels_to_center_table(center_id, labels):
    """打开csv修改后写回"""
    fname = get_result_table_path()
    df = pd.read_csv(fname, index_col=0)
    df.loc[center_id, 'label_desc'] = labels
    #print(df.head(), df.columns)
    df.to_csv(fname)

#insert_labels_to_center_table(1, "aa,bbb")

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