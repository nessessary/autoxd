#coding:utf8

from autoxd import warp_pytdx as tdx
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd import stock, myredis
from autoxd import sign_observation as so
from win32com import client
import time

class LiveHq(object):
    def __init__(self):
        self.speaker = client.Dispatch('SAPI.SPVOICE')
        self.codes = [jx.XJN新洁能,jx.XSKJ兴森科技,]
        self.dict_speaked = {}# code, price
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
        boll_poss = stock.boll_poss(upper, middle, lower)
        
        sign = 'none'
        if close< middle[-1]:
            sign = '下'
        else:
            sign = '上'
        sign = ''
        name = stock.GetCodeName(code)
        msg = ''
        if code in self.dict_speaked.keys() and \
           ((self.dict_speaked[code] > close and close < boll_poss[-2]) or (close > boll_poss[2] and close > self.dict_speaked[code])):
            msg = f"{close}"
            self.dict_speaked[code] = close
        if code not in self.dict_speaked.keys():
            msg = "[%s %s %s]"%(name, sign, close)
            self.dict_speaked[code] = close
        if msg != '':
            t = time.strftime('%H:%M:%S', time.localtime(time.time()))
            print(f"{t} {msg}")
        return msg
    
   
    def hq_loop(self):
        codes = self.codes
        count = 100
        # get hq
        while stock.is_livetime(): 
            for code in codes:
                #df = myredis.gen_data(__file__, hq_loop, lambda: tdx.getFive(code))
                try:
                    df = tdx.getFive(code, count)
                    msg = self.run(df, code)
                    self.speak(msg)
                except:
                    pass
            time.sleep(60)

if __name__ == "__main__":
    hq = LiveHq()
    hq.hq_loop()
    