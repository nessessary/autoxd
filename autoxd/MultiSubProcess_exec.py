#-*- coding:utf-8 -*-
#把主目录放到路径中， 这样可以支持不同目录中的库
import os
def getMainDir():
    add_path = os.path.dirname(__file__) 
    add_path = os.path.abspath(add_path)
    return add_path    
def AddPath():
    from sys import path
    mysourcepath = getMainDir()
    if not mysourcepath in path:
        path.append(mysourcepath)    
    #需要执行的模块目录必须包含进lib path
    strategy_path = mysourcepath+"\\strategy"
    if strategy_path not in path:
        path.append(strategy_path)
#AddPath()
import numpy as np
import pandas as pd
import sys, myredis
from MultiSubProcess import MultiSubProcess
"""作为并行的中间跳板"""
#import wingdbstub
#wingdbstub.Ensure()

def main(args):
    os.chdir(getMainDir())
    i = int(args[0])
    #print 'arg=',i
    pd_task = myredis.get_obj('multi')
    if 0: pd_task = pd.DataFrame
    #print pd_task.iloc[i]
    v = tuple(pd_task.iloc[i].tolist()[1:])#去掉task_id
    #print v
    v += (i,)   #加上task_id
    s = 'import %s\n'%(v[0])
    #module.fn
    s += 'r = %s.%s(%s, %d)'%v
    #print s
    exec(s)
    #print 'result=',r
    #保存结果
    try:
        #r未获取
        myredis.set_obj(MultiSubProcess.getResultName(i), r)
    except:
        pass
    #print "end"
    
if __name__ == "__main__":
    #try:
        args = sys.argv[1:]
        main(args)
    #except:
        #main(None)