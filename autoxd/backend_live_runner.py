#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

#把主目录放到路径中， 这样可以支持不同目录中的库
from __future__ import print_function
import os
import numpy as np
import pandas as pd
import sys,unittest,  datetime, traceback,win32api
import myredis,stock,agl,fenshi_redis,live_policy,ui,help
from strategy import basesign
from strategy.basesign import Http
from strategy.basesign import send_msg
import pylab as pl
from stock import LiveData

"""执行在线redis数据, 策略执行者"""

#不开盘时间也可以跑
is_force_run = True

class LiveRunner:
    """执行网站策略(stocksign)"""
    def __init__(self):
        #记录策略runlog上次提交的时间
        self.pre_post_runlog = {1:datetime.datetime(2015, 10, 19, 15, 33, 47, 53000)}
        self.ths = stock.createThs()
    def _getUserStrategy(self, downloadStrategyInterval=60):
        """按固定的时间间隔下载用户代码
        downloadStrategyInterval: int default=60 秒
        return: df"""
        k = "SignForWebUser_preLoadTime"
        preLoadTime = myredis.get_obj(k)
        if preLoadTime is None:
            preLoadTime = datetime.datetime(2015, 10, 19, 15, 33, 47, 53000)	#上一次下载的时间
        #判断时间
        if (agl.curTime() - preLoadTime).total_seconds() > downloadStrategyInterval:
            url = "http://stocksign.sinaapp.com/query?cmd=query_strategy"
            result = Http().get(url)
            df_source = pd.read_json(result)
            df_source.columns = ['id', 'user_id', 'title', 'code']
            preLoadTime = agl.curTime()
            myredis.set_obj(k, preLoadTime)
            myredis.set_obj('mysource', df_source)
        else:
            df_source = myredis.get_obj('mysource')
            if df_source is None:
                df_source = pd.DataFrame([])
        return df_source	
    def _checkImport(self, code):
        """执行代码里不允许有import， 防止用户代码进行磁盘操作"""
        if code.find('import')>=0:
            raise "no use import"

    def RunTask(self):
        while True:
            self.Run()
            print('tick')
    def _getCodes(self):
        return stock.get_codes()
    def Run(self):
        if not stock.IsKaiPan() and not is_force_run:
            return
        a = agl.tic_toc()
        codes = self._getCodes()
        #codes = ['300033']
        for code in codes:
            #try:
            self.ExePolicy(code)
            #except Exception as e:
            #print str(e)
        self.LoopEndEvent()
    def LoopEndEvent(self):
        """每次全部的股票遍历完成后执行"""
        pass
    def ExePolicy(self, code):
        df_source = self._getUserStrategy()
        if len(df_source) == 0:
            return
        d =[]
        bHaveCode = False
        for i in range(len(df_source)):
            strategy_code = df_source.irow(i)['code']
            strategy_id = df_source.irow(i)['id']
            try:
                self._checkImport(strategy_code)
                #self._log("run here")
                exec(strategy_code)
                if initialize(None).find(code) >= 0:
                    bHaveCode = True
                    break
            except Exception as e:
                s = str(e)
                d.append({"strategy_id":strategy_id, "title":code, 
                          "code":s, "t":datetime.datetime.now()})
                #一分钟内同一个策略不能提交
                if (d[-1]["t"] - self.pre_post_runlog[strategy_id]).total_seconds() > 60:
                    agl.LOG(str(e))
                    basesign.PostRunLog(d)
                    self.pre_post_runlog[strategy_id] = d[-1]['t']
                continue
        if bHaveCode == False:
            return

        live_data = LiveData()
        df_hisdat = live_data.getHisdat(code)
        df_fenshi = live_data.getFenshi(code)
        if len(df_fenshi) == 0:
            return
        #return

        data = {"code":code, "fenshi":df_fenshi, "hisdat":df_hisdat, 
                'name':stock.GetCodeName(code), 'price':float(df_fenshi.tail(1)['p'])}

        # 取历史redis分时
        df_fenshi_1min = df_fenshi.resample("1min")
        df_fenshi_1min_pre = fenshi_redis.getOneMinFenshiFromRedis(code)
        if df_fenshi_1min_pre is None:
            agl.LOG("分时历史取值失败"+code)
        else:
            df_fenshi_1min = pd.concat([df_fenshi_1min_pre,
                                        df_fenshi_1min])
        df_fenshi_1min = df_fenshi_1min.dropna()
        closes = np.array(df_fenshi_1min['p'])
        data['rsi'] = stock.RSI(closes)[-1]
        # BOLL
        df_fenshi_5min = df_fenshi_1min.resample('5min')
        upper, middle, lower = stock.BOLL(np.array(df_fenshi_5min['p']))
        data['boll_up'] = upper[-1]
        data['boll_mid'] = middle[-1]
        data['boll_down'] = lower[-1]
        # ATR
        atr = stock.ATR(df_fenshi_5min['p'],df_fenshi_5min['p'],df_fenshi_5min['p'])
        data['atr'] = atr[-1]

        #执行用户的代码
        data['msglist'] = []
        for i in range(len(df_source)):
            strategy_code = df_source.irow(i)['code']
            #strategy_code = strategy_code.replace('\n','')
            strategy_id = df_source.irow(i)['id']
            agl.LOG(str(strategy_id))
            data['strategy_id'] = strategy_id
            try:
                self._checkImport(strategy_code)
                exec(strategy_code)
                if initialize(None).find(code) < 0:
                    continue
                sign = handle_data(self, data)
                s = "run sussessful"
                if sign:
                    s += " have sign"
                agl.LOG(s)
            except Exception as e:
                s = str(e)
                #s += '\n'
                s += traceback.format_exc()
            d.append({"strategy_id":strategy_id, "title":code, 
                      "code":s, "t":datetime.datetime.now()})
        #所有用户的策略执行完毕后再提交
        agl.LOG('start post')
        basesign.PostRunLog(d)
        if len(data['msglist']) > 0:
            agl.LOG(data['msglist'])
            basesign.PostMsgList(data['msglist'])
        agl.LOG('end post')

class LiveLocalRunner(LiveRunner):
    """本地redis数据执行"""
    live_dll = None
    _dict_four = {} #为了输出最小的几个four
    def _getCodes(self):
        codes = stock.get_codes()
        #codes = codes.tolist()
        #codes = [x for x in codes if x[0]=='3']
        #codes = ['300244','300033','300032','002695']
        #codes.append('510050')
        return codes
    def Speak(self, s):
        if self.live_dll is None:
            self.live_dll = live_policy.Live()
        self.live_dll.speak2(s)
    def NotifyAutoxdShow(self, code):
        return 0
        #窗口通知
        hwnd = LiveData().getFrameHwnd()
        code = int(code)
        #lparam为整型的股票代码, wparam为补充0的个数
        try:
            win32api.PostMessage(hwnd,0x400+101,code,6-len(str(code)))
        except:
            pass
    def ExePolicy(self, code):
        code = agl.unicode_to_utf8(code)
        live_data = LiveData()
        df_hisdat = live_data.getHisdat(code)
        df_fenshi = live_data.getFenshi(code)
        df_five_hisdat = live_data.getFiveMinHisdat(code)
        if agl.IsNone(df_five_hisdat):
            #print code ,'没有5分钟'
            return
        if len(df_fenshi) == 0:
            return
        if len(df_five_hisdat)<30:
            return
        price = float(agl.FloatToStr(float(df_fenshi.tail(1)['p'])))
        yclose = df_hisdat.ix[df_hisdat.index[-1]]['c']
        zhangfu = stock.ZhangFu(price, yclose)
        rsi = stock.RSI(df_five_hisdat['c'])
        #ui.DrawClosesAndVolumes(pl, df_five_hisdat['c'], rsi)
        upper, middle, lower = stock.TDX_BOLL(df_five_hisdat['c'])
        #ui.DrawTs(pl, df_five_hisdat['c'],mid=middle, high=upper, low=lower)
        highs, lows, closes = df_five_hisdat['h'], df_five_hisdat['l'], df_five_hisdat['c']
        #atr = stock.ATR(highs, lows, closes)
        adx = stock.TDX_ADX(highs, lows, closes)
        closes = np.array(df_hisdat['c'])
        if help.MyDate(agl.datetime_to_date(df_hisdat.index[-1])).d < \
           help.MyDate(agl.CurDay()).d:
            closes = agl.array_insert(closes, len(closes), price)
        four = stock.FOUR(closes)
        #print code, four[-1]
        self._dict_four[code] = four[-1]

        #return
        #ui.DrawClosesAndVolumes(pl, df_five_hisdat['c'], adx)
        boll_up = (price - upper[-1] ) / upper[-1]
        boll_mid = (price - middle[-1] ) / middle[-1]
        boll_down = (lower[-1] -price) / lower[-1]
        boll_width = upper[-1] - lower[-1]
        if abs(zhangfu)>0.098 or boll_width < 0.01:
            return
        if code == '300033':
            codename = stock.GetCodeName(code)
            s = 'rsi = %d %s %s'%(rsi[-1], codename, str(price))
            print(s)
        if (rsi[-1] > 65 or rsi[-1] < 35) and adx[-1]>60:
            codename = stock.GetCodeName(code)
            s = '%s %s'%(codename, str(price))
            sign = False
            #if code in ['300033','510050']:
                #sign = True
            #if adx[-1] > 55:
                #s += ' ADX=%d'%(adx[-1])
                #sign = True
            if boll_up > -0.003:
                s += '  越过布林上轨'
                #sign = True
            if abs(boll_mid) <0.003:
                s += '  布林中轨'
                #sign = True
            if boll_down > -0.003:
                s += '  越过布林下轨'
                sign = True
            if four[-1] > 0.1:
                sign = False

            #sign = False

            if sign:
                #ui.DrawTs(pl, df_five_hisdat['c'],mid=middle, high=upper, low=lower)
                sInfo = self.calcInfo(code,price, zhangfu)
                help.myprint(s, sInfo)
                help.myprint('[%s,%s] %.3f,%.3f,%.3f,%.2f, four=%.2f, adx=%.2f'%(code, stock.GetCodeName(code), boll_up, boll_mid, boll_down, boll_width,four[-1],adx[-1]))
                self.NotifyAutoxdShow(code)
                self.Speak(s)   
    def LoopEndEvent(self):
        """输出four最小的5个"""
        #排序dict_four
        df = pd.DataFrame(self._dict_four.items())
        if len(df)>0:
            df = df.sort_values(by=1, ascending=True)
            print(df.head())
    def calcInfo(self, code, price, zhangfu):
        """计算显示的一些基础信息 return: str"""
        if not stock.IsZhiShuCode(code):
            one = self.ths.createThsOneCode(code,price=price)
            syl = int(one.get_syl())
        else:
            syl = 0
        sInfo = '涨幅%.2f%% 市盈率%d'%(zhangfu*100, syl)
        return sInfo
class mytest(unittest.TestCase):
    def _testGet(self):
        codes = ['600096']
        #codes = stock.get_codes()
        a = agl.tic_toc()
        for code in codes:
            try:
                LiveData().getHisdat(code)
                LiveData().getFenshi(code)
                LiveData().getFiveMinHisdat(code)
            except:
                print('except'+code)
    def _testExePolicy(self):
        code = '300087'
        p = LiveLocalRunner()
        p.ExePolicy(code)
    def _testLoadDll(self):
        """测试加载python_invoke.dll, 测试里面的speak函数"""
        live_dll = live_policy.Live()
        live_dll.speak2("蓝图")
    def test_Speak(self):
        """测试语音, 去控制面板里的语音选择默认语音"""
        live_dll = live_policy.Live()
        live_dll.speak2('测试语音, 去控制面板里的语音选择默认语音')

def main(args):
    #LiveLocalRunner().RunTask()
    unittest.main()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
