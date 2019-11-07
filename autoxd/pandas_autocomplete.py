#coding:utf8

from pandas import *

class MyDataFrame(DataFrame):
    def __init__(self, df):
        self._data = df
    if 0: get_col = Series
    def get_col(self, i):
        return self._data[self._data.columns[i]]
    
    