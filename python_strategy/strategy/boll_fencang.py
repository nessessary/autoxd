#-*- coding:utf-8 -*-

"""boll分仓"""

import boll_pramid
import backtest_policy, stock, myenum

class BollFenCangKline(boll_pramid.Strategy_Boll_Pre):
    """基于日线的boll分仓, 基本指标使用日线Boll以及日线Four"""
    def getParams(self):
        return 1
    def setParams(self, *args, **kwargs):
        pass
    def OnFirstRun(self):
	pass
    def Run(self):
	code = self.data.get_code()
	hisdat = self.data.get_hisdat(code)
	closes = hisdat['c']
	four = stock.FOUR(closes)
	four = four[-1]
	#print self.getCurTime(), four
	price = hisdat.iloc[-1]['c']
	if four<-0.7:
	    self._getAccount().Order(0, code, price, 10000)
	if four>0.7:
	    self._getAccount().Order(1, code, price, 10000)

    @staticmethod
    def test():
        
	def setParams(s):
	    if 0: s = Strategy_Boll
	    s.setParams(trade_num = 300)
	    
	codes = [u'300033']
	#现在的5分钟线在2017-5-15之后才有
	backtest_policy.test_strategy(codes, BollFenCangKline, setParams, day_num=20, mode=myenum.hisdat_mode, 
	                              start_day='2017-4-24', end_day='2017-9-1'
	                              )    
    
if __name__ == "__main__":
    BollFenCangKline.test()