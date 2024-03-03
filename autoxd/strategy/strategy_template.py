#coding:utf8

from autoxd.strategy.five_chengben import Strategy_Boll_Pre
from autoxd.pinyin import stock_pinyin3 as jx
from autoxd import backtest_policy
from autoxd import backtest_runner
from autoxd.backtest_runner import BackTestPolicy
from autoxd.stock import DataSources
from autoxd import stock, agl

class StrategySample(Strategy_Boll_Pre):
    def OnFirstRun(self):
        pass
    def Run(self):
        pass
    def Report(self):
        pass
    def OnCalcTech(self, df_hisdat, df_five_hisdat, df_fenshi):
        pass
    

def Run(codes, task_id=0):
    from autoxd.pypublish import publish
    
    def fnSample(code, dtype='5'):
        from autoxd import warp_pytdx as tdx
        if dtype=='5':
            df = tdx.getFive(code)
            df = df.sort_index()
            return df
        if dtype=='d':
            df = tdx.getHisdat(code)
            df = df.sort_index()
            return df
    
    def setParams(s):
        s.setParams(
            pl=publish.Publish(),
        )
    backtest_policy.test_strategy(codes, StrategySample, setParams,
                                  start_day='', end_day='',
                                  mode=BackTestPolicy.enum.hisdat_mode|BackTestPolicy.enum.hisdat_five_mode,
                                  datasource_mode=DataSources.datafrom.custom,
                                  datasource_fn=fnSample
                                  )

def main_run():        
    cpu_num = 1
    codes = stock.get_codes(stock.myenum.randn, cpu_num)
    #agl.startDebug()
    if agl.IsDebug():
        codes = [jx.ZCKJ.b]
    exec(agl.Marco.IMPLEMENT_MULTI_PROCESS)

if __name__ == "__main__":
    main_run()
    