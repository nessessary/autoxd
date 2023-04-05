#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# mail: nessessary@qq.com

import os
import numpy as np
import pandas as pd
import sys
import redis, pickle
from datetime import datetime

"""保存对象至redis"""

g_redis = None
g_redis: redis.Redis
class Expire(object):
    """记录key过期时间"""
    EXPIRE_KEY = 'REDIS.EXPIRE'
    def __init__(self):
        self.data = get_obj(self.EXPIRE_KEY)
        self.data : dict
        if self.data is None:
            self.data = {}
    def expire(self, key):
        """if the key is expire, del it"""
        if key in self.data.keys():
            save_time, expire_time = self.data[key]
            delta = datetime.now()-save_time
            if delta.total_seconds() > expire_time:
                delkey(key)
                
    def update(self, key, expire_time):
        # update data
        if key in self.data.keys():
            if expire_time != -1:
                self.data[key] = [datetime.now(), expire_time]
                set_obj(self.EXPIRE_KEY, self.data)
                
g_expire = None
g_expire : Expire

def createRedis():
    #assert(False)
    global g_redis
    global g_expire
    if g_redis is None:
        try:
            g_redis = redis.Redis(host='localhost', port=6379, db=0) 
            g_redis.info()
            if g_expire is None:
                g_expire = Expire()
        except:
            #把myredis.com写入hosts
            #g_redis = redis.Redis(host='myredis.com', port=6379, db=0) 
            return None
    return g_redis
def gen_keyname(fname, fn):
    """根据函数堆栈来确定函数名称, 当使用内嵌函数时， 模块为父函数的名称
    fname: __file__
    fn: ptr fn指针
    return: str 模块名.函数名"""
    fname = os.path.basename(fname)
    fname = fname.split('.')[0]
    return str(fname + '.' + fn.__name__)

def set_str(key, s):
    r = createRedis()
    if r is not None:
        r.set(key, s)
def set_obj(key, o, expire_time=-1):
    """无返回值, 记录数据
    expire_time: 设置过期时间, seconds
    """
    r = createRedis()
    if r is not None:
        b = pickle.dumps(o)
        r.set(key, b)
        if expire_time != -1:
            g_expire.update(key, expire_time)
def get_obj(key):
    """用key取值 return: obj 或者 None"""
    r = createRedis()
    if g_expire is not None:
        g_expire.expire(key)
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
    if r is not None:
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
        key = str(key, encoding='utf8')
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


def createRedisVal(key, v):
    """key: str
    v: object or function 值或者使用该函数返回的值; 如果 是函数必须有返回值
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

        
def gen_data(filename, call_fn, process_fn):
    key = gen_keyname(filename, call_fn)
    return createRedisVal(key, process_fn).get()

def gen_data_at_curday(filename, call_fn, process_fn):
    """跨天后重新调用fn; 一天 只跑一次
    return: process_fn()"""
    key = gen_keyname(filename, call_fn)
    cur_day = str(datetime.now()).split(' ')[0]
    keys = getKeys(key)
    if str(key) + cur_day not in keys:
        delKeys(key)
    key = key + cur_day
    return createRedisVal(key, process_fn).get()

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
    
def test_expire():
    o = '123'
    key = 'test'
    expire_time = 30
    set_obj(key, o, expire_time)
    
    o = get_obj(key)
    print(o)
    import time
    time.sleep(expire_time+2)
    o = get_obj(key)
    print(o)
    
    
if __name__ == "__main__":
    test_expire()