回测框架
------

回測使用的账户为一个本地模拟账户(见account.py)， 接口和实盘接口一致， <br>
这个回测框架主要关注具体的交易细节， 适合T+0操作

- 例子
	python boll_fencang.py<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result.png)<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result_kline.png)<br><br>

- 依赖
1. redis
	window可以去[网盘](https://pan.baidu.com/s/1pMoB83h) 下载一个, 调用里面的bat即可安装
2. 支持py2及py3 windows， linux及macos未知
3. 推荐使用wingide， 可直接加载wpr项目文件
4. 用pip install -r requirement.txt安装相关依赖包

- 使用

1. 数据源<br>
   1) 使用[客户端](https://pan.baidu.com/s/1pMoB83h) 下载数据, 编制config.ini填写需要下载的代码, 
      下载后放置到redis里, 见datasource_mode=stock.DataSources.datafrom.livedata
   2) 使用自定义的第三方数据源， 已实现了一个调用tushare的例子, 
      datasource_mode=stock.DataSources.datafrom.custom

2. 调用
```python
    #设置策略参数
    def setParams(s):
	s.setParams(trade_num = 300, 
                    #pl=publish.Publish()	#发布方式
                    )
    #执行策略, 5分钟线
    backtest_policy.test_strategy(codes, BollFenCangKline, setParams,
				  mode=BackTestPolicy.enum.hisdat_mode|BackTestPolicy.enum.hisdat_five_mode, 
                                  #start_day='2016-10-20', end_day='2017-10-1',
				  datasource_mode=stock.DataSources.datafrom.online	#从网上下载测试数据
                                  )    

```
	
