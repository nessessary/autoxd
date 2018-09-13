#-*- coding:utf-8 -*-

"""多个df集成到dict后因为太大无法直接pickle到本地文件中， pickle.load时会报EOFerror
因此，把dict中的单个df进行pickle
"""
from __future__ import print_function
import pandas as pd
import agl, help
import os
import unittest
class mytest(unittest.TestCase):
    def test1(self):
        huge_dict().clear()
        d = {'sdkkf':pd.DataFrame([1,2,3]), 'kkkk':pd.DataFrame([222,333])}
        d = huge_dict(d).get()
        print(d)
        print(huge_dict().get())
        huge_dict().clear()
        
class huge_dict:
    """单件， 定向处理ths_f10, 按单表保存至path
    dict的键值转换为数字， 数字与表名查table_names
    dict映射到目录， 并从目录映射回dict
    clear后由 getThsResults创建
    """
    dir_path = 'datas/huge_dict/'
    def __init__(self, d={}):
        """d: dict"""
        self.d = d
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.dir_path = cur_dir + '/' + self.dir_path
        if self.d != {}:
            help.CreateDir(self.dir_path)
            self._write()
    def get(self):
        """return: dict"""
        if self.d == {}:
            self._read()
        return self.d
    def _read(self):
        """从redis中读取数据"""
        #读表名
        path = self.dir_path + 'table_names.df'
        table_names = pd.read_pickle(path).values.T[0]
        for i, table_name in enumerate(table_names):
            path = self.dir_path + str(i) + '.df'
            self.d[table_name] = pd.read_pickle(path)
    def _write(self):
        """分表写入redis"""
        #先写表名
        table_names = list(self.d.keys())
        path = self.dir_path + 'table_names.df'
        df = pd.DataFrame(table_names)
        df.to_pickle(path)
        for i, k in enumerate(table_names):
            path = self.dir_path + str(i)+'.df'
            df = self.d[k]
            df.to_pickle(path)
            
    def clear(self):
        agl.removeDir(self.dir_path)
            
if __name__ == '__main__':
    unittest.main()