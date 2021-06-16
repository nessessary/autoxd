#coding:utf8

from autoxd.cnn_boll.pearson_clust import save_result
import pandas as pd
import unittest

class mytest(unittest.TestCase):
    def test_csv_save(self):
        #print('abc')
        df = pd.DataFrame([])
        save_result(df)
    
if __name__ == "__main__":
    unittest.main()