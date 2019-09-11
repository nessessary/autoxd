#coding:utf8

"""执行并行"""

from concurrent.futures import ProcessPoolExecutor
#from concurrent.futures import ThreadPoolExecutor  #builtins.RuntimeError: main thread is not in main loop
import numpy as np
import math
import os
from autoxd.MultiSubProcess.MultiSubProcess import pp_func_param

def _split_arg(a, cpus):
    splitted_args = pp_func_param(None, a, cpu=cpus)._split(a)
    return splitted_args
    

g_fn=None
def _exec_fn(a, index, timeout=30):
    assert(g_fn)
    return index, g_fn(a)

def run_fn(fn, args):
    global g_fn
    cpu_num = os.cpu_count()
    p = ProcessPoolExecutor(max_workers=cpu_num)
    g_fn = fn
    results = p.map(_exec_fn, _split_arg(args, cpu_num), range(cpu_num))
    p.shutdown(wait=True)
    r2 = []
    for index, r in results:
        r2.append(r)
    return r2

def test():
    def my_test(a):
        print(a)
        l = []
        for x in range(100):
            #判断如果ｘ是素数，则打印，如果不是素数就跳过
            if x <2:
                continue
            for i in range(2,x):
                if x % i == 0:
                    break
            else:
                l.append(x)
        return l
    r = run_fn(my_test, [2,10,3,5,7,8])
    print(r)

#在此例子中if __name__ == "__main__":一定要加，因为没有if __name__会在创建子进程的时候又会运行，导致错误
if __name__ == "__main__": 
    test()