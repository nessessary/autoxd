#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os
import numpy as np
import pandas as pd
import sys, agl
import redis, StringIO, cStringIO
if sys.version > '3':
    import _pickle as cPickle
else:
    import cPickle

code = '600100'
def test_save():
    import stock
    r = redis.Redis(host='localhost', port=6379, db=0) 
    ths = stock.createThs()
    #df = stock.Guider(code).ToDataFrame()
    f = cStringIO.StringIO()
    cPickle.dump(ths, f)
    #df.to_csv(f)
    s = f.getvalue()
    f.close()
    print(len(s))
    r.set('ths', s)
def test_read():
    r = redis.Redis(host='localhost', port=6379, db=0) 
    s = r.get('ths')
    #print len(s)
    f = cStringIO.StringIO(s)
    #f = open('1.txt', 'w')
    #f.write(s)
    #f.close()
    #f = open('1.txt', 'r')
    #print f.getvalue()
    #df = pd.read_csv(f)
    df = cPickle.load(f)
    print(type(df))
    f.close()
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
def get(fn, *args, **kwargs):
    """通过redis来cache数据
    fn: 函数, 返回要存储的数据
    return: data fn返回的值"""
    key = gen_keyname(fn)
    r = createRedis()
    #r.flushall()
    if key not in r.keys():
        o = fn(*args, **kwargs)
        #对象序列化为字符串
        f = cStringIO.StringIO()
        cPickle.dump(o, f)
        s = f.getvalue()
        f.close()        
        r.set(key, s)
    s = r.get(key)
    f = cStringIO.StringIO(s)
    o = cPickle.load(f)
    f.close()
    return o
def set(fn, *args, **kwargs):
    """保存键值, 对象太大的还是会出现异常"""
    key = gen_keyname(fn)
    r = createRedis()
    #r.flushall()
    o = fn(*args, **kwargs)
    #对象序列化为字符串
    f = cStringIO.StringIO()
    cPickle.dump(o, f)
    s = f.getvalue()
    f.close()        
    r.set(key, s)
def set_str(key, s):
    r = createRedis()
    r.set(key, s)
def set_obj(key, o):
    """无返回值, 记录数据"""
    r = createRedis()
    f = cStringIO.StringIO()
    cPickle.dump(o, f)
    s = f.getvalue()
    f.close()        
    r.set(key, s)
def get_obj(key):
    """用key取值 return: obj 或者 None"""
    r = createRedis()
    s = r.get(key)
    if agl.IsNone(s):
        return s
    f = cStringIO.StringIO(s)
    o = cPickle.load(f)
    f.close()
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
def clear():
    r = createRedis()
    for key in r.keys():
        r.delete(key)
def getKeys():
    return createRedis().keys()
def main(args):
    #test_save()
    #test_read()
    #test_pickle()
    #print get('a', lambda x: x+'adfkdf', 'bbb')
    def getDataSource(code):
        import stock
        return stock.Guider(code).ToDataFrame()
    print(get(getDataSource, '600779'))
    print(createRedis().keys())
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)