#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457


#2013-9-30
#模拟


import stock,os

from abc import ABCMeta, abstractmethod
import datetime
import help,agl
#import mysql
import random
import copy
import myenum
import numpy as np
import pandas as pd

########################################################################
class ISimulator:
    """"""
    __metaclass__ = ABCMeta #派生类不实现接口会有错误提示
    if 0: p = policy.IPolicy
    p = None
    flag = 0
    
    def Set(self, p, flag):
	'''p = policy, flag=加载股票列表方式'''
	self.p = p
	self.flag = flag
    
    @abstractmethod
    def Travl(self, start_day='', end_day=''):
	pass
    
    #
    #
    #----------------------------------------------------------------------
    @staticmethod
    def getGupiaos(flag=4, n=100):
        """
	flag可以传入list或string
	"""
	assert(False)	#废弃该函数
	gupiaos = []
	#重新定义一个数组来做单元测试
	if flag == myenum.some:
	    gupiaos = ["600779", "000002", "002234", "000596", "600358", "600258"]
	    
	if flag == myenum.one:
	    gupiaos = ["600779", "000002", "002234", "000596", "600358", "600258"]
	    gupiaos = [gupiaos[1]]
	    
	if flag == myenum.rand or flag == myenum.rand10 or flag == myenum.rand100 \
	   or flag==myenum.rand8 or flag == myenum.rand32 or flag == myenum.rand600 or flag==myenum.randn:
	    db = mysql.StockMysql()
	    gupiaos = db.getGupiao()
	    random.shuffle(gupiaos)
	    if myenum.rand10 == flag:
		gupiaos = gupiaos[:10]
	    if myenum.rand ==  flag:
		gupiaos = gupiaos[:2]
	    if myenum.rand100 ==  flag:
		gupiaos = gupiaos[:100]
	    if myenum.rand8 == flag:
		gupiaos = gupiaos[:8]
	    if myenum.rand32 == flag:
		gupiaos = gupiaos[:32]
	    if myenum.rand600 == flag:
		gupiaos = gupiaos[:600]
	    if myenum.randn == flag:
		gupiaos = gupiaos[:n]
	    
	if flag == myenum.all:
	    db = mysql.StockMysql()
	    gupiaos = db.getGupiao()
	
	if flag == myenum.sunxu:
	    db = mysql.StockMysql()
	    id = 0
	    try:
		f = open("c:\\temp_id", "r")
		id = f.readline()
	    except:
		f = open("c:\\temp_id", "w")
		id = 0
	    if id=='':
		id=0
	    f.close()
	    id, gupiao = db.getOneGupiao(id)
	    f = open("c:\\temp_id", "w")
	    f.write(str(id))
	    f.close()
	    gupiaos = [gupiao]
	    
	if isinstance(flag, str):
	    gupiaos = [flag]
	    
	if isinstance(flag, list):
	    gupiaos = flag
	
	if flag == myenum.exclude_cyb:
	    gupiaos = ISimulator.getGupiaos(myenum.all)
	    gupiaos = pd.Series(gupiaos)
	    gupiaos = gupiaos[gupiaos.map(lambda x: x[0] != '3')]
	    gupiaos = gupiaos.tolist()
	if flag == myenum.just_cyb:
	    gupiaos = ISimulator.getGupiaos(myenum.all)
	    gupiaos = pd.Series(gupiaos)
	    gupiaos = gupiaos[gupiaos.map(lambda x: x[0] == '3')]
	    gupiaos = gupiaos.tolist()
	return gupiaos	    
    
#
########################################################################
class SimulatorHisdat(ISimulator):
    """
    只对股票k线进行遍历
    """
    #----------------------------------------------------------------------
    def Process(self, code, start_day='', end_day=''):
        """"""
	help.myprint(self.p.__class__, code)
	guider = stock.Guider(code, start_day,end_day)
	account = stock.Account()
	
	for i in range(0, guider.getSize()):
	    if 0: hisdat = stock.Hisdat
	    hisdat = guider.getData(i)
	    #new_guider = stock.Guider(code, end_day=str(hisdat.date))
	    new_guider = copy.deepcopy(guider)
	    if 0: new_guider = stock.Guider
	    new_guider.hisdats = new_guider.hisdats[:i]
	    #help.myprint("当前天为 ", str(hisdat.date))
	    self.p.OnTick(new_guider, None, account)
	
	account.myprint()    
	return account
    
    #----------------------------------------------------------------------
    if 0: Travl = stock.Account
    def Travl(self, start_day='', end_day=''):
        """
	flag : one/some/rand/all    列表类型
	num :执行的数量
	"""
	account = None
	gupiaos = ISimulator.getGupiaos(self.flag)
    	for gupiao in gupiaos:
	    account = self.Process(gupiao, start_day, end_day)
	return account
            

class SimulatorAllData(SimulatorHisdat):
    """取数据由数据文件"""
    def Travl(self, start_day='', end_day=''):
	#加载文件
	#all_data = stock.Kline.FromFile()
	#for i in range(0, len(all_data[:self.flag])/5):
	    #if (i+1)*5 > len(all_data[:self.flag]):
		#break
	    #self.p.OnTick(all_data[i*5:(i+1)*5], None, None)
	#self.p.EndHandle()
	alldatas = stock.AllDatas()
	for i in range(0, len(alldatas.datas)/5):
	    self.p.OnTick(alldatas.get(i), None, None)
	self.p.EndHandle()
#
    def TravlRandom(self, num):
	"""跑随机, num: 随机的个数"""
	indexs = agl.GenRandomArray(2000, num)
	alldatas = stock.AllDatas()
	for index in indexs:
	    self.p.OnTick(alldatas.get(index), None, None)
	self.p.EndHandle()

    
########################################################################
class SimulatorOneStock(SimulatorHisdat):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
	"""Constructor"""
	
    #
    def Process(self, code, start_day='', end_day=''):
	guider = stock.Guider(code, start_day, end_day)
	self.p.OnTick(guider, None, None)
	return None
    
    
########################################################################
class Simulator(ISimulator):
    """
    按时间顺序进行遍历, 分时遍历， 当只给一个股票时，还原成单个分时
    """
   
    #----------------------------------------------------------------------
    if 0: Travl = stock.Account
    def Travl(self, start_day='', end_day=''):
        """根据日期来遍历全部股票"""
        if 0: start_day = end_day = datetime
        if start_day == '':
            start_day = help.StrToDate("2011-10-11")
        if end_day == '':
            #今天
            end_day = datetime.date.today()
            
        gupiaos = ISimulator.getGupiaos(self.flag)
	
	account = stock.Account()
            
	#为了减少数据库操作， 还是先取出数据再判断日期
	guiders = []
        start_day = help.MyDate(start_day)
	for gupiao in gupiaos:
	    if not self.p.filter(gupiao):
		guider = stock.Guider(gupiao, start_day.ToStr())
		help.myprint("时间策略遍历", guider.code)
		guiders.append(guider)

	#start_day.Add(60)
        while start_day.Next() < end_day:
            day = start_day.ToStr()
            help.myprint(day)

	    for guider in guiders:
		#看当前日期是否存在
		if guider.DateToIndex(start_day.d) == -1:
		    continue
		
		new_guider = copy.deepcopy(guider)
		if 0: new_guider = stock.Guider
		new_guider.resize(start_day.d)
		
		fenshi = stock.Fenshi(guider.code, day)
		fenshi.mean()
		for order in fenshi.orders:
		    if 0: order = stock.Order
		    new_fenshi = copy.deepcopy(fenshi)
		    new_fenshi.resize(order.date)
		    #help.myprint(order.date, order.price)
		    self.p.OnTick(new_guider, new_fenshi, account)

	    
        account.myprint()
	return account
    #

#----------------------------------------------------------------------
if 0: CreateSimulator = ISimulator
def CreateSimulator(id):
    """"""
    if id==myenum.IID_Simulator:
	return Simulator()
    if id == myenum.IID_SimulatorCode:
	return SimulatorHisdat()
    if id == myenum.IID_SimulatorOneStock:
	return SimulatorOneStock()
    if id == myenum.IID_SimulatorAllData:
	return SimulatorAllData()


def main(args):
    print "end"
    
if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        main(args)
    except:
        main(None)