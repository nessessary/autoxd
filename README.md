回测框架
------

回測使用的账户为一个本地模拟账户(见account.py)， 接口和实盘接口一致， <br>
这个回测框架主要关注具体的交易细节， 适合T+0操作

1. 数据源<br>
   请到 [网盘](http://pan.baidu.com/s/1bpto0wv) 下载一个数据源， 包含300033的日线，5分钟线，及分时线, <br>
   下载该目录放置到python_strategy\datas目录中<br>
   要使用全部数据源可以联系作者或者修改框架使用第三方数据源, 具体见stock.DataSources<br>
   stock_createThs.searial为同花顺F10全部数据<br>
   自动加载， 使用见stock.py里的StockInfoThs<br>
   前复权使用同花顺的分红表， 具体见stock.py里的calc_fuquan_use_fenhong<br>

2. 依赖包问题， 作者主要使用anaconda 32bit python2.7版本， 需要的库为ta-lib, redis, charade等<br>
   64位 python3.x也可使用，估计需要修改部分代码; 作者只在windows下测试通过，linux可能有问题<br>
   建议使用WingIDE来加载项目并执行， 使用命令行执行可能会碰到乱码的问题

3. 执行
   回测有两种模式， hisdat_mode|tick_mode分别是日线和分时, 日线模式执行比较快， 每天收盘时成交,<br>
   分时执行时间比较长，成交为实际的时间<br>
   1> 分时的例子<br>
   用ide打开缺省策略boll_pramid.py并执行<br>

   中间结果显示TickReport<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_tick_1.png)<br>
   可看见输出的结果图<br>
   资金0表示没有盈亏， 负值表示亏损， 正值表示盈利, 资金和仓位为归一化结果<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result.png)<br>
   输出窗口可以看见交易明细<br>

   <br>
   2>日线的例子<br>
   支持并行<br>
   boll_fenchang.py<br>
   图形示例<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result_kline.png)<br>

4. 发布
   见boll_fencang.py
   发布输出内容到web页面, 
   [例子](http://autoxd.applinzi.com/html/boll_fencang_setParams6100.html)
```python
    #设置策略参数
    def setParams(s):
	s.setParams(trade_num = 300, 
                    #pl=publish.Publish()	#发布方式
                    )
    if codes == '':
	codes = [u'300033']
    #执行策略
    backtest_policy.test_strategy(codes, BollFenCangKline, setParams, day_num=20, mode=myenum.hisdat_mode, 
                                  start_day='2016-10-20', end_day='2017-10-1'
                                  )    

```
	
