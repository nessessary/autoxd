回测
------

回測使用的账户为一个本地模拟账户(见account.py)， 接口和实盘接口一致， 因此有必要在回測系统里做一下测试
这个回测框架主要关注具体的交易细节， 适合T+0操作

1. 数据源<br>
   请到 [网盘](http://pan.baidu.com/s/1bpto0wv) 下载一个数据源， 包含300033的日线，5分钟线，及分时线, 下载后放置到<br>
   python_strategy\datas目录中<br>
   要使用全部数据源可以联系作者或者修改框架使用第三方数据源, 具体见stock.DataSources<br>
   stock_createThs.searial为同花顺F10全部数据, 可不下, 最后更新日期2017-9-6<br>
   自动加载， 使用见stock.py里的StockInfoThs<br>
   前复权使用同花顺的分红表， 具体见stock.py里的calc_fuquan_use_fenhong<br>

2. 依赖包问题， 如果使用自己的anaconda， 需要32bit python2.7版本的， 其次需要的库为ta-lib, redis, charade等<br>
   或者下载安装包， 里面带一份anaconda， 已经包含了所需要的库， 使用该目录即可

3. 执行
   回测有两种模式， hisdat_mode|tick_mode分别是日线和分时, 日线模式执行比较快， 每天收盘时成交,<br>
   分时执行时间比较长，成交为实际的时间<br>
   1> 分时的例子<br>
   用ide打开缺省策略boll_pramid.py并执行<br>
   或者用命令行<br>
   python boll_pramid.py<br>

   中间结果显示TickReport<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_tick_1.png)<br>
   可看见输出的结果图<br>
   资金0表示没有盈亏， 负值表示亏损， 正值表示盈利, 资金和仓位为归一化结果<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result.png)<br>
   输出窗口可以看见交易明细<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result_kline.png)<br>
   <br>
   2>日线的例子<br>
   支持并行<br>
   boll_fenchang.py<br>

4. 发布
   见boll_fencang.py
   发布输出内容到web页面
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
	
