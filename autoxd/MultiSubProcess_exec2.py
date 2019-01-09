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

def getImportName(from_module):
    module = from_module.split('import ')[-1]
    module = str(module).strip()
    return module

def main(args):
    #os.chdir(getMainDir())
    if len(args)>0:
        i = int(args[0])
    else :
        i = 0
    print('arg=',i)
    pd_task = myredis.get_obj('multi')
    if 0: pd_task = pd.DataFrame
    #print pd_task.iloc[i]
    v = tuple(pd_task.iloc[i].tolist()[1:])#去掉task_id
    #print v
    v += (i,)   #加上task_id
    s = '%s\n'%(v[0])
    # 获取import模块名
    module_name = getImportName(s)
    #module.fn
    s += 'r=%s'%(module_name)
    s += '.%s(%s, %d)'%(v[1:])
    #print(s)
    
    ##py3
    #_locals = locals()
    #r = exec(s, globals(), _locals)
    #r = _locals['r']
    ##py2
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