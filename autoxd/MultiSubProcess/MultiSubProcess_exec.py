#-*- coding:utf-8 -*-
#把主目录放到路径中， 这样可以支持不同目录中的库
import os

import numpy as np
import pandas as pd
import sys
from autoxd import myredis
from autoxd.MultiSubProcess import MultiSubProcess

"""作为并行的中间跳板"""
#import wingdbstub
#wingdbstub.Ensure()
def getMainDir():
    add_path = os.path.dirname(__file__) 
    add_path = os.path.abspath(add_path)
    return add_path    

def getImportName(fname):
    bname = os.path.basename(fname)
    module = bname.split('.')[0]
    return module

from sys import path
def AddPath(spath):
    """spath : 绝对地址"""
    #print(spath)
    mysourcepath = os.path.dirname(spath)
    if not mysourcepath in path:
        #print(mysourcepath)
        path.append(mysourcepath)    
        
def main(args):
    #os.chdir(getMainDir())
    if len(args)>0:
        i = int(args[0])
    else :
        i = 0
    #print('arg=',i)
    pd_task = myredis.get_obj('multi')
    if 0: pd_task = pd.DataFrame
    #print pd_task.iloc[i]
    v = tuple(pd_task.iloc[i].tolist()[1:])#去掉task_id
    #print(v)
    v += (i,)   #加上task_id
    fname = v[0]
    #print('fname=',fname)
    AddPath(fname)
    module_name = getImportName(fname)
    s = 'import %s\n'%(module_name)
    # 获取import模块名
    #module.fn
    s += 'r=%s'%(module_name)
    s += '.%s(%s)'%(v[1:-1])
    #print(s)
    
    if sys.version > '3':
        from autoxd.pinyin.myexec import myexec
        r = myexec(s)
        #_locals = locals()
        #r = exec(s, globals(), _locals)
        #r = _locals['r']        
    else:
        exec(s)
    
    #print(type(r))
    #print('result=',r)
    #保存结果
    try:
        myredis.set_obj(MultiSubProcess.getResultName(i), r)
        #print('save successful.', MultiSubProcess.getResultName(i))
    except:
        print("MultiSubProcess result save failed.")
    #print "end"
    
if __name__ == "__main__":
    #try:
        args = sys.argv[1:]
        main(args)
    #except:
        #main(None)