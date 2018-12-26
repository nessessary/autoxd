#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
import os,traceback
from sys import path
def AddPath():
    from sys import path
    mysourcepath = os.path.abspath('.')
    if not mysourcepath in path:
        path.append(mysourcepath)    
    strategy_path = mysourcepath+"\\strategy"
    if strategy_path not in path:
        path.append(strategy_path)        
#AddPath()
"""在线策略入口"""
import numpy as np
import sys, copy, traceback
import help
import agl
import live_policy
reload(live_policy)
from strategy import qjjy
reload(qjjy)

from strategy import boll_pramid
reload(boll_pramid)

def StartDebug():
    import wingdbstub
    wingdbstub.Ensure()
    
class LivePolicySwitch:
    """策略分流器"""
    def __init__(self):
        self.policys = []
    def Regist(self, policy):
        """注册需要执行的策略"""
        self.policys.append(policy)
    def Run(self):
        for strategy in self.policys:
            try:
                strategy.Run()
            except Exception as e:
                s = str(e)
                s += traceback.format_exc()
                strategy._log(agl.utf8_to_ascii(s))
    @staticmethod
    def Test():
        #StartDebug()
        p = LivePolicySwitch()
        #p.Regist(qjjy.Strategy(live_policy.Live()))
        p.Regist(boll_pramid.Strategy_Boll_Pre(live_policy.Live()))
        #agl.LOG("LivePolicyRun")
        p.Run()
        

def main(args):
    #debug下dll加载出错， 但live方式没问题
    LivePolicySwitch.Test()
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)