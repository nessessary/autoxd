#coding:utf8

"""处理labels表, 用csv处理"""
from __future__ import print_function
import os
import pandas as pd
#from autoxd import agl

class LabelTable(object):
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
        """"""
        df = pd.DataFrame([new_label])
        if len(self.df) >0:
            df.columns = self.df.columns
        self.df = pd.concat([self.df,df], ignore_index=True, axis =0)
        self.df.to_csv(self.fname)
    
def test():
    obj = LabelTable()
    obj.save('aaaa')
    #print(obj._get_datas_dir())
    print(obj.df)
test()  
test()