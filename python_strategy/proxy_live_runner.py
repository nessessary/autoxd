#-*- coding:utf-8 -*-

"""入口， 直接执行策略 """
import live_policy_runner, data_interface, stock
import time
import agl
from strategy import boll_pramid

def run_policy():
    p = live_policy_runner.LivePolicySwitch()
    s = boll_pramid.Strategy_Boll_Pre(data_interface.TdxData())
    if agl.is_function(s.setParams):
        s.setParams()
    p.Regist(s)

        
    while 1:
        agl.tic()
        p.Run()
        agl.toc()
        time.sleep(3)
        if stock.IsShouPan():
            break
    
if __name__ == '__main__':
    run_policy()