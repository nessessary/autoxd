#coding:utf8

from autoxd import warp_pytdx as tdx
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd import stock, myredis, agl
from autoxd import sign_observation as so
try:
    from win32com import client
    g_have_speaker = True
except:
    g_have_speaker = False
import time,os
#from autoxd import profile
import pandas as pd
try:
    import get_detect_result
    g_have_detect = False
except:
    g_have_detect = False
    pass

def get_custom_codes():
    """获取通达信自选股导出"""
    fname = r'I:\MyApp\new_zxjt_ctp\T0002\export\自选股%s.txt'
    if not os.path.exists(fname):
        # 手工输入自定义
        codes = [
            jx.XSKJ兴森科技,
            jx.YGDY阳光电源,
        ]
        return codes
    
    #获取最新文件
    dir_path = os.path.dirname(fname)
    #获取目录的文件名列表， 降序
    files = os.listdir(dir_path)
    files:list
    files.sort(reverse=True)
    filted_files = list(filter(lambda x: x.find('自选股')>=0, files))
    fname = os.path.join(dir_path , filted_files[0])
    
    df = pd.read_csv(fname, sep='\t', encoding='gbk')
    df = df[:-1][df.columns[:2]]
    df = df[df[df.columns[0]].map(lambda x: len(x)==6)]
    
    return df[df.columns[0]].tolist()

class LiveHq(object):
    def __init__(self):
        if g_have_detect:
            self.speaker = client.Dispatch('SAPI.SPVOICE')
        self.codes = get_custom_codes()
        self.dict_speaked = {}# code, price
        
        self.d = {} # hisdat day kline
        for code in self.codes:
            self.d[code] = tdx.getHisdat(code)
        
    def speak(self, s):
        if g_have_speaker:
            self.speaker.Speak(s)


    def run(self, df, code):
        upper, middle, lower = stock.TDX_BOLL(df['c'].values)
        adx = stock.ADX(df['h'].values, df['l'], df['c'])
        closes = df['c'].values
        if closes[-1] == 0:
            closes = closes[:-1]
        #four = stock.FOUR(closes, days=[5, 10, 20, 60])
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
        if code not in self.dict_speaked.keys():
            msg = "[%s %s %s]"%(name, sign, close)
            self.dict_speaked[code] = close
        else:
            zhangfu = stock.ZhangFu(close, yclose=self.d[code]['c'][-2]) *100
            #print(agl.float_to_2(zhangfu))
            if so.assemble(
               (self.dict_speaked[code] > close and close < boll_poss[-2]) or (close > boll_poss[1] and close > self.dict_speaked[code]),
               #abs(zhangfu) > 0.5, 
            ):
                msg = f"{close}"
                self.dict_speaked[code] = close
            
            # hard_recog check ...
            if g_have_detect:
                
                # shape recognize
                try:
                    df['upper'] = upper
                    df['middle'] = middle
                    df['lower'] = lower                    
                    r = get_detect_result.zmq_detect(df[-100:])
                    #box[4], conf, class_index
                    if len(r) > 0:
                        msg = f'detected {close}'
                        self.dict_speaked[code] = close
                except:
                    pass
            
            
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
                try:
                    df = tdx.getFive(code, count)
                    msg = self.run(df, code)
                    self.speak(msg)
                except:
                    pass
            time.sleep(60)
        for code in codes:
            try:
                df = tdx.getFive(code, count)
                close = df['c'].values[-1]
                msg = "[%s  %s]" % (stock.GetCodeName(code), close)
                if msg != '':
                    t = time.strftime('%H:%M:%S', time.localtime(time.time()))
                    print(f"{t} {msg}")                
                self.speak(msg)
                
            except:
                pass
        if g_have_detect:
            get_detect_result.zmq_close()

if __name__ == "__main__":
    hq = LiveHq()
    hq.hq_loop()
    