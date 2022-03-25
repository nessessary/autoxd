#coding:utf8

from autoxd import warp_pytdx as tdx
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd import stock, myredis
from win32com import client
import time

class LiveHq(object):
    def __init__(self):
        self.speaker = client.Dispatch('SAPI.SPVOICE')
        self.codes = [jx.GFLY赣锋锂业]
    def speak(self, s):
    
        self.speaker.Speak(s)


    def run(self, df, code):
        upper, middle, lower = stock.TDX_BOLL(df['c'].values)
        adx = stock.ADX(df['h'].values, df['l'], df['c'])
        closes = df['c'].values
        if closes[-1] == 0:
            closes = closes[:-1]
        four = stock.FOUR(closes, days=[5, 10, 20, 60])
        close = closes[-1]
        
        
        sign = 'none'
        if close< middle[-1]:
            sign = '下'
        else:
            sign = '上'
        msg = "[%s %s %s]"%(code, sign, close)
        print(msg)
        return msg
    
   
    def hq_loop(self):
        codes = self.codes
        # get hq
        while 1: 
            for code in codes:
                #df = myredis.gen_data(__file__, hq_loop, lambda: tdx.getFive(code))
                df = tdx.getFive(code)
                msg = self.run(df, code)
                self.speak(msg)
            
            time.sleep(30)

if __name__ == "__main__":
    hq = LiveHq()
    hq.hq_loop()
    