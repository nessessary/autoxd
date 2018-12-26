#-*- coding:utf-8 -*-

"""观察信号组合"""
import traceback
import numpy as np
import pandas as pd
from autoxd import myredis,agl
is_allow = False
key_prefix = 'so._getFunctionArgs.'

def init():
    #print 'init'
    myredis.delKeys(key_prefix)
if is_allow:    
    init()
def assemble(*args, **kwargs):
    """组合信号, 分析信号触发次数, 并显示参数表达式
    args: tuple boll
    return: bool
    """
    #需要获取参数的文中状态输入， 比如four<-0.3, 需要获取表达式
    #打开调用者文件， 获取调用处行号， 手工获取参数
    if is_allow:
        s_trace = traceback.extract_stack()
        if len(s_trace)>=2:
            #print s_trace[-2]
            fname,line,mod,fn_name = s_trace[-2]
            fn_name = s_trace[-1][-2]
            args_text = _getFunctionArgs(fname, line, fn_name)
            #print args_text
    #print args
    args = np.array(args)
    return args.all()

def _getFunctionArgs(fname, line, fn_name):
    """分析文件文本获取参数表达式"""
    key = key_prefix+agl.MD5(fname+str(line)+fn_name)
    val = myredis.createRedisVal(key, [])
    if len(val.get())>0:
        return val.get()
    f = open(fname, 'r')
    s = f.readlines()
    f.close()
    line -= 1
    while line>=0:
        if s[line].find(fn_name)>=0:
            break
        line -= 1
    #print line
    s = s[line:]
    #过滤出表达式
    full_s = ''
    for s_l in s:
        cur_line_s = s_l.strip()
        if cur_line_s[0] == '#':
            continue
        full_s += cur_line_s
        if cur_line_s.find(')')>=0:
            break
    full_s = full_s.replace(fn_name, '')
    full_s = full_s.replace('(','')
    full_s = full_s.replace(')','')
    if full_s[-1] == ',':
        full_s = full_s[:-1]
    #print full_s
    args = full_s.split(',')
    #print args
    val.set(args)
    return args
if __name__ == "__main__":
    assemble(1>2,
             #3>3,
             4<5,
             )
    if assemble(1<2):
        print('aaa')
