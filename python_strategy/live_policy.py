#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

import os
import sys, struct, StringIO,copy, traceback
import numpy as np
import pandas as pd
from ctypes import *
import help,agl,stock
import time

class enum:
    account_ths=0
    account_tc = 1
    account_local = 3
class Live:
    """实时接口"""
    def __init__(self):
        #path = help.GetParentDir(help.GetParentDir(mysourcepath))
        def getCurProcessRunPath():
            """return: 当前exe执行的路径"""
            cur_path = os.path.abspath(__file__)
            cur_path = os.path.dirname(cur_path)
            #cur_path += '\\python_load.txt'
            #path = agl.ReadFile(cur_path)
            path1 = '/../../build/release'
            ret_path = cur_path+path1
            ret_path = os.path.abspath(ret_path)
            if os.path.isdir(ret_path):
                return ret_path
            ret_path = cur_path + '/../'
            ret_path = os.path.abspath(ret_path)
            return ret_path
        path = getCurProcessRunPath()
        #添加该路径到系统path， 因为dll的依赖dll也需要在路径中才能加载
        if not path in os.environ['path']:
            os.environ['path'] +=(path)
        dll = np.ctypeslib.load_library('python_invoke', path)
        #见python_invoke.h
        self.CreateAccount = dll.CreateAccount
        self.GetTotalMoney = dll.GetTotalMoney
        self.GetCanUseMoney = dll.GetCanUseMoney
        self.GetStockList = dll.GetStockList
        self.Buy = dll.Buy
        self.Sell = dll.Sell
        self.GetCurrentCode = dll.GetCurrentCode
        self.GetAllCodes = dll.GetAllCodes
        self.MyTrace = dll.MyTrace   
        self.GetHisdat = dll.GetHisdat
        self.GetFenshi = dll.GetFenshi
        self.GetInfo = dll.GetInfo
        self.HaveWeituo = dll.HaveWeituo
        self.GetLastWeituo = dll.GetLastWeituo
        self.GetBankuaiSort = dll.GetBankuaiSort
        self.Speak = dll.Speak
        self.ShowUI = dll.ShowUI
        self.Cache_Set = dll.Cache_Set
        self.Cache_Get = dll.Cache_Get
        self.Cache_GetLength = dll.Cache_GetLength
        self.HandleRotuer = dll.HandleRotuer
        
        self.account = None
        
        #CreateAccount
        self.CreateAccount.argtypes = [
            c_int, 
            c_char_p,
            c_char_p
        ]
        self.CreateAccount.restype = c_void_p
        #Buy
        self.Buy.argtypes = [
            c_void_p,
            c_char_p,
            c_int, 
            c_double
        ]
        self.Buy.restype = c_int
        #Sell
        self.Sell.argtypes = [
            c_void_p,
            c_char_p,
            c_int, 
            c_double
        ]
        self.Sell.restype = c_int
        #GetTotalMoney
        self.GetTotalMoney.argtypes = [
            c_void_p 
        ]
        self.GetTotalMoney.restype = c_float
        #GetCanUseMoney
        self.GetCanUseMoney.argtypes = [
            c_void_p 
        ]
        self.GetCanUseMoney.restype = c_float
        #GetStockList
        self.GetStockList.argtypes = [
            c_void_p, 
            c_char_p,
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS")
        ]
        self.GetStockList.restype = c_int
        #HaveWeituo
        self.HaveWeituo.argtypes = [
            c_void_p,
            c_char_p,
            c_int, 
            c_double
        ]
        self.HaveWeituo.restype = c_int
        #GetLastWeituo
        self.GetLastWeituo.argtypes = [
            c_void_p, 
            c_char_p,
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS")
        ]
        self.GetLastWeituo.restype = c_int
        #HandleRotuer
        self.HandleRotuer.argtypes = [
            c_void_p, 
            c_char_p,
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS")
        ]
        self.HandleRotuer.restype = c_int
        
        #GetHisdat
        self.GetHisdat.argtypes = [
            c_char_p,
            np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags="C_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags="C_CONTIGUOUS"),
            c_char_p
        ]
        self.GetHisdat.restype = c_int
        #GetFenshi
        self.GetFenshi.argtypes = [
            c_char_p,
            np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags="C_CONTIGUOUS"),
            np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags="C_CONTIGUOUS")
        ]
        self.GetFenshi.restype = c_int
        #GetInfo
        self.GetInfo.argtypes = [
            c_char_p,
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS"),
        ]
        self.GetInfo.restype = c_int
        #GetBankuaiSort
        self.GetBankuaiSort.argtypes = [
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS"),
        ]
        self.GetBankuaiSort.restype = c_int
        #GetCurrentCode
        self.GetCurrentCode.argtypes = [
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS"),
        ]
        self.GetCurrentCode.restype = c_int
        #GetAllCodes
        self.GetAllCodes.argtypes = [
            np.ctypeslib.ndpointer(dtype=np.int8, ndim=1, flags="C_CONTIGUOUS"),
        ]
        self.GetAllCodes.restype = c_int
        #MyTrace
        self.MyTrace.argtypes = [
            c_char_p
        ]
        self.MyTrace.restype = c_int
        #Speak
        self.Speak.argtypes = [
            c_wchar_p
        ]
        self.Speak.restype = c_ulong
        #ShowUI
        self.ShowUI.argtypes = [
            c_char_p
        ]
        self.ShowUI.restype = c_int
        #Cache_Set
        self.Cache_Set.argtypes = [
            c_char_p,
            c_char_p
        ]
        self.Cache_Set.restype = c_int
        #Cache_Get
        self.Cache_Get.argtypes = [
            c_char_p,
            c_char_p
        ]
        self.Cache_Get.restype = c_int
        #Cache_GetLength
        self.Cache_GetLength.argtypes = [
            c_char_p
        ]
        self.Cache_GetLength.restype = c_int
    def get_code(self):
        a = np.array(list("600797"), dtype=np.int8)
        self.GetCurrentCode(a)
        b = ""
        for c in a:
            b += chr(c)
        return b
    def get_codes(self):
        """return: list"""
        a = np.zeros(6*5000, dtype=np.int8)
        l = self.GetAllCodes(a)
        s = agl.ArrayToStr(a[:l])
        r = s.split('|')
        if r[-1] == '':
            return r[:-1]
        return r
    def createAccount(self, account_type, username, pwd):
        """非在线状态无法生成账户"""
        self.account = self.CreateAccount(account_type, username, pwd)
    def get_hisdat(self, code, dtype='day'):
        """ 
        dtype = 0为5分钟， 4为日线
        return: df columns ('hlocv')"""
        #构造数据区, row*6
        row = np.array([-1], dtype=np.int32)
        a = np.array([0], dtype=np.float64)
        self.GetHisdat(code,row,a, dtype)
        l = (row[0], 6)
        a = np.zeros(l[0]*l[1], dtype=np.float64)
        if row[0] > 0:
            self.GetHisdat(code, row, a, dtype)
        d = a.reshape(l)
        df = pd.DataFrame(d[:,0])
        if dtype == 'day':
            df[0] = df[0].map(lambda x: stock.StockTime.s_ToStrDate(x))
        if dtype == '5min':
            df[0] = df[0].map(lambda x:time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(x)) )
        df = pd.DataFrame(d[:,1:], index=pd.DatetimeIndex(df[0]), dtype=float, columns=list('ohlcv'))
        if dtype == '5min':
            df['h'] /= 100.0
            df['l'] /= 100.0
            df['o'] /= 100.0
            df['c'] /= 100.0
        return df
    def get_fenshi(self, code):
        """return: df columns('tpvdb')"""
        #构造数据区, row*5
        row = np.array([-1], dtype=np.int32)
        a = np.array([0], dtype=np.float64)
        self.GetFenshi(code,row,a)
        l = (row[0], 5)
        a = np.zeros(l[0]*l[1], dtype=np.float64)
        if row[0] > 0:
            self.GetFenshi(code, row, a)
        d = a.reshape(l)
        df = pd.DataFrame(d[:,0])
        df[0] = df[0].map(lambda x: stock.StockTime.s_ToStrTime(int(x), agl.CurDay()))
        df = pd.DataFrame(d[:,1:], index=pd.DatetimeIndex(df[0]), dtype=float, columns=list('pvdb'))
        return df
    def get_fiveminhisdat(self, code):
        return stock.LiveData().getFiveMinHisdat(code)
    def get_info(self, code):
        a = np.zeros(1000, dtype=np.int8)
        l = self.GetInfo(code, a)
        return agl.ArrayToStr(a[:l])
    def get_bankuaisort(self):
        a = np.zeros(500*200, dtype=np.int8)
        l = self.GetBankuaiSort(a)
        s = agl.ArrayToStr(a[:l])
        a = np.array(s.split("|"))[:-1]
        a=a.reshape((len(a)/2, 2))
        df = pd.DataFrame(a)
        df[1] = df[1].astype('float')
        return df
    def getTotalMoeny(self):
        return self.GetTotalMoney(self.account)
    def getCanUseMoney(self):
        return self.GetCanUseMoney(self.account)
    def get_stocklist(self, code):
        a= np.zeros(2000, dtype=np.int8)
        l = self.GetStockList(self.account, code, a)
        s = agl.ArrayToStr(a[:l])
        return s.split('|')
    def buy(self, code, num, price):
        """code : str
        num: int
        price: float"""
        return self.Buy(self.account, code, num, price)
    def sell(self, code, num, price):
        return self.Sell(self.account, code, num, price)
    def IsWeituo(self, code, num, price):
        return self.HaveWeituo(self.account, code, num, price)
    def getLastWeituo(self, code):
        a= np.zeros(200, dtype=np.int8)
        l = self.GetLastWeituo(self.account, code, a)
        s= agl.ArrayToStr(a[:l])
        return s.split('|')
    def handleRotuer(self, input_params):
        """使用一个入口来与底层通信， 其它原有account接口暂时废弃
        input_params : str 文本协议 action|params...| 通过对action字段的判断来确定调用的函数, 一般为发送函数
        return: str 返回发送函数获取的结果
        """
        a = np.zeros(20000, dtype=np.int8)
        l = self.HandleRotuer(self.account, input_params, a)
        s = agl.ArrayToStr(a[:l])
        return s
    def log(self, s):
        if isinstance(s, unicode):
            s = help.convert(s)
        if not isinstance(s, str):
            s = str(s)
        b=self.MyTrace(s)
        if b==0:
            print s
    def speak(self, unicode_str, code):
        """unicode_str: 必须为unicode
        code: str, 需要转化为中间带空格的
        return: 0 -执行成功"""
        assert(agl.is_unicode(unicode_str))
        code = ' '.join(list(code))
        code = agl.convert(code)
        unicode_str = code + ' ' + unicode_str
        return self.Speak(unicode_str)
    def speak2(self, s):
        s = agl.convert(s)
        return self.Speak(s)
    def show(self, codename):
        """通知客户端刷新, codename: str代码名称 utf8"""
        try:
            return self.ShowUI(codename)
        except:
            pass
    def cache_set(self, key, val):
        """保存一个值到内存中
        val : str 长度需要小于200"""
        assert(len(val) < 200)
        self.Cache_Set(key, val)
    def cache_get(self, key):
        """从内存中获取一个值
        return: str"""
        a= np.zeros(200, dtype=np.int8)
        l = self.Cache_Get(key, a)
        s = agl.ArrayToStr(a[:l])
        return s
def Reshape(a, cols=6):
    b = []
    for i in range(0, len(a), cols):
        b.append(a[i:i+cols])
    return b

def Test():
    #重定向输出
    logfile = open("log.txt", "w")
    oldstdout = sys.stdout
    sys.stdout = logfile
    
    TestAccont()
    
    #还原输出
    sys.stdout = oldstdout
    logfile.close()
def PrintDf(df, p):
    if 0:df = pd.DataFrame()
    row = df.shape[0]
    for i in range(0, row, 60):
        p.log(str(df[i:i+60]))
        #print df[i:i+60]


def testVoice():
    p = Live()
    s = u'发现突破%s'
    print p.speak(s, '600086')
def main(args):
    #TestCon()
    testVoice()
    #TestConEx()
    print "end"
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)