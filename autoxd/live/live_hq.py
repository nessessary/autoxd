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
import time,os,sys
#from autoxd import profile
import pandas as pd
try:
    import get_detect_result
    g_have_detect = False
except:
    g_have_detect = False
    pass

# 蒸馏后的形态识别(数值特征, 无需yolo/zmq), 有模型文件即可用
try:
    from autoxd.live import shape_distill
    g_have_distill = os.path.exists(shape_distill.MODEL_PATH)
except:
    g_have_distill = False

# 运行模式: 'boll'=原始布林判断, 'shape'=形态识别, 'all'=两者都开
# 命令行可覆盖: python live_hq.py --mode shape
g_mode = 'all'
for flag in ('--mode', '-mode'):
    if flag in sys.argv:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            g_mode = sys.argv[idx + 1]
        break

def get_custom_codes():
    """获取通达信自选股导出"""
    fname = r'I:\MyApp\zd_zxjtzq\T0002\export\自选股%s.txt'
    
    #获取最新文件
    dir_path = os.path.dirname(fname)
    #获取目录的文件名列表， 降序
    files = os.listdir(dir_path)
    custom_codes = []
    
    files:list
    files.sort(reverse=True)
    filted_files = list(filter(lambda x: x.find('自选股')>=0 and x.endswith('.txt'), files))
    fname = os.path.join(dir_path , filted_files[0])
    
    df = pd.read_csv(fname, sep='\t', encoding='gbk')
    df = df[:-1][df.columns[:2]]
    df = df[df[df.columns[0]].map(lambda x: len(x)==6)]
    
    codes = df[df.columns[0]].tolist()
    codes += custom_codes
    return list(dict.fromkeys(codes))

class LiveHq(object):
    def __init__(self):
        if g_have_speaker:
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
            if g_mode != 'shape':
                msg = "[%s %s %s]"%(name, sign, close)
            self.dict_speaked[code] = close
        else:
            zhangfu = stock.ZhangFu(close, yclose=self.d[code]['c'][-2]) *100
            #print(agl.float_to_2(zhangfu))
            if g_mode in ('boll', 'all') and so.assemble(
               (self.dict_speaked[code] > close and close < boll_poss[-2]) or (close > boll_poss[1] and close > self.dict_speaked[code]),
               #abs(zhangfu) > 0.5,
            ):
                msg = f"{close}"
                self.dict_speaked[code] = close

            # hard_recog check ... (与yolo识别一致: 检测到右端形态才播报)
            if g_mode in ('shape', 'all') and g_have_distill:
                r = shape_distill.predict(df)
                if r is not None:
                    msg = f"{name} {close:.2f}"
                    self.dict_speaked[code] = close
            elif g_mode in ('shape', 'all') and g_have_detect:
                
                # shape recognize
                try:
                    df['upper'] = upper
                    df['middle'] = middle
                    df['lower'] = lower                    
                    r = get_detect_result.zmq_detect(df[-100:])
                    #box[4], conf, class_index
                    if len(r) > 0:
                        msg = f"{name} {close}"
                        self.dict_speaked[code] = close
                except:
                    pass
            
            
        # 涨跌停判断: 主板10%, 创业板/科创板20%, ST股5%
        if msg != '':
            yclose = self.d[code]['c'][-2]
            zhangfu_pct = stock.ZhangFu(close, yclose) * 100
            # 判断涨跌停
            if code.startswith('3') or code.startswith('68'):
                limit_pct = 20  # 创业板/科创板
            else:
                limit_pct = 10  # 主板
            # 接近涨跌停时不播报 (留0.1%余量)
            if abs(zhangfu_pct) >= limit_pct - 0.1:
                msg = ''

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
            try:
                get_detect_result.zmq_close()
            except:
                pass

if __name__ == "__main__":
    print('live_hq mode: %s (boll/shape/all, --mode 可切换)' % g_mode)
    hq = LiveHq()
    hq.hq_loop()
    