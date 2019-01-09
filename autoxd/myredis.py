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

g_redis = None
def createRedis():
    global g_redis
    if g_redis is None:
        try:
            g_redis = redis.Redis(host='localhost', port=6379, db=0) 
            g_redis.info()
        except:
            #把myredis.com写入hosts
            g_redis = redis.Redis(host='myredis.com', port=6379, db=0) 
    return g_redis
def gen_keyname(fname, fn):
    """根据函数堆栈来确定函数名称, 当使用内嵌函数时， 模块为父函数的名称
    fname: __file__
    fn: ptr fn指针
    return: str 模块名.函数名"""
    fname = os.path.basename(fname)
    fname = fname.split('.')[0]
    return fname + '.' + fn.__name__

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
        return None
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
        if str(key).find(k)>=0:
            r.delete(key)
    
def clear():
    r = createRedis()
    for key in r.keys():
        r.delete(key)
def getKeys(k=''):
    keys = list(createRedis().keys())
    if k == '':
        return keys
    find_keys = []
    for key in keys:
        if key.find(k)>=0:
            find_keys.append(key)
    return find_keys

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
    """key: str
    v: object or function 值或者使用该函数返回的值
    return: class Val
    """
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
        

def dump_redis(host, key='*'):
    """从目标redis倾倒数据到当前redis"""
    db_host = redis.Redis(host=host, port=6379, db=0)
    db_me = redis.Redis(host='localhost', port=6379, db=0) 
    keys = db_host.keys(pattern=key)
    for key in keys:
        v = db_host.get(key)
        db_me.set(key, v)
    
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
    def test_obj2(self):
        keys = getKeys()
        print(len(keys))
        #print(get_obj(keys[2]))
    def _test_dump(self):
        dump_redis(host='192.168.3.4', key='')
    
if __name__ == "__main__":
    unittest.main()