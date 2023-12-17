#coding:utf8

"""基于筹码判断区间, 只处理一个股票"""

from autoxd.live import live_hq, colorprint
from autoxd import stock, ui
import pylab as pl


class Live_Chips(live_hq.LiveHq):
    def __init__(self):
        super(Live_Chips, self).__init__()
        
        self.codes = self.codes[0:1]
        code = self.codes[0]
        #calc chips
        df = stock.getFiveHisdatDf(code, is_Trunover=True)
        self.df_chips = stock.calcChips(df)
        ui.drawChips(pl, self.df_chips, df, title=code)
        huanshou = df[-48*5:]['v'].sum() / 5
        print(huanshou)


    def run(self, df, code):
        #print('aaa', code)
        close = df.iloc[-1]['c']
        # 5日平均换手率
    

def main():
    live = Live_Chips()
    live.hq_loop()
    
if __name__ == "__main__":
    main()