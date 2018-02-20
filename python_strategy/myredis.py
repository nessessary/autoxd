#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

import os
import numpy as np
import pandas as pd
import sys
import redis, pickle

"""保存对象至redis"""

g_redis = 0
def createRedis():
    global g_redis
    if g_redis == 0:
        g_redis = redis.Redis(host='localhost', port=6379, db=0) 
    return g_redis
def gen_keyname(fn):
    """根据函数堆栈来确定函数名称, 当使用内嵌函数时， 模块为父函数的名称
    return: str 模块名.函数名"""
    return fn.__module__ + '.' + fn.__name__

def set_str(key, s):
    r = createRedis()
    r.set(key, s)
def set_obj(key, o):
    """无返回值, 记录数据"""
    r = createRedis()
    b = pickle.dumps(o)
    r.set(key, b)
def get_obj(key):
    """用key取值 return: obj 或者 None"""
    r = createRedis()
    o = r.get(key)
    try:
        if o is not None:
            o = pickle.loads(o)
    except:
        o = _get_obj_at_2(key)
    return o
def get_Bin(key):
    r = createRedis()
    return r.get(key)
def isexist(key):
    r = createRedis()
    return key in r.keys()
def delkey(key):
    r = createRedis()
    r.delete(key)
def delKeys(k):
    """删除包含关键字的key
    k: str 关键字"""
    r = createRedis()
    for key in r.keys():
        if key.find(k)>=0:
            r.delete(key)
    
def clear():
    r = createRedis()
    for key in r.keys():
        r.delete(key)
def getKeys():
    return createRedis().keys()

def ForceGetObj(k,v):
    """如果没有该值， 那么存储"""
    v1 = get_obj(k)
    if v1 is None:
        if hasattr(v, '__call__'):
            v1 = v()            
        else:
            v1 = v
        set_obj(k, v1)
    return v1

if 0: createRedisVal = Val
def createRedisVal(key, v):
    ForceGetObj(key, v)
    return Val(key)
class Val(object):
    def __init__(self, key):
        self.key = key
    def get(self):
        return get_obj(self.key)
    def set(self, v):
        set_obj(self.key, v)

#记录一些公用的key
class enum:
    KEY_CODES = 'stock.Codes'
    KEY_THS = 'stock.ths'
    KEY_CODENAME = 'stock.codename'
    KEY_BANKUAIS = 'stock.bankuais'
    KEY_THS_GAIYAO = 'stock.ths.gaiyao'     #概要表, 因为整体导入redis会造成out of memory, 因此分表导入
    KEY_BANKUAI_AVG_SYL = 'stock.ths.bankuai_syl'   #板块平均市盈率
    KEY_JLL = 'stock.ths.jll'   #净利润表
    KEY_YEAR = 'stock.ths.year' #净利润表年
    KEY_HISDAT_NO_FUQUAN = 'stock.hisdat.nofuquan'  #保存未复权的hisdat
        

#因为2和3的pickle流不通用， 虽然代码可以使用一份， 但用2导出到redis的流在3里不认， 两者自行使用没有问题
#使用json作为中间流来处理df的存储
def _get_obj_at_2(key):
    """在3中获取2序列化到redis的值"""
    #先使用2获取pickle流
    exe2_path = "C:\\ProgramData\\Anaconda2\\python.exe"
    if not os.path.exists(exe2_path):
        exe2_path = "c:\\anaconda2\\python.exe"
    cmd = exe2_path + ' -c "import myredis;myredis._convert_obj_to_json_for_3(\'' + key + '\')"'
    key += '.json'
    if  key in getKeys():
        df = get_Bin(key)
        return df
    import subprocess
    p = subprocess.Popen(cmd)
    p.wait()
    #print(cmd)
    s = get_Bin(key)
    df = pd.read_json(s)
    return df
def _convert_obj_to_json_for_3(key):
    """从redis中取出并转化为json再次存入, 并修改key为key.json"""
    df = get_obj(key)
    if 0: df = pd.DataFrame()
    s = df.to_json()
    key = key + '.json'
    set_str(key, s)

import unittest
class mytest(unittest.TestCase):
    def _test_obj(self):
        o = {'ad':1}
        import pickle
        key = 'temp'
        b = pickle.dumps(o)
        r = createRedis()
        r.set(key, b)
        print(pickle.loads(r.get(key)))
    def test_convert_at_3(self):
        code = '300033'
        df = _get_obj_at_2(code)
        print(df)
    
if __name__ == "__main__":
    unittest.main()