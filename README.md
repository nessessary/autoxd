autoxd v0.4 回测框架
------

简单快捷的A股回测环境， 适合编写T+0策略

- 特性
  * 使用pandas编写策略
  * 结果可以在页面显示， 类似matlab的publish
  * 并行执行策略
  * 本地账户， 模拟实盘交易细节， 支持T+0， 交易成本计算
  * 自创FOUR指标， 简单计算多空

- 变更
  * 见docs/changelog.txt
  * v0.4.1 支持macos
  * v0.4 大幅优化速度
  * v0.3 python3支持

- 日线例子

```
	python boll_fencang.py
```

   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result.png)<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result_kline.png)

- 5分钟例子

```
	python five_chengben.py
```

   <img src="https://github.com/nessessary/autoxd/raw/master/pics/five.png"></img>


- 依赖
1. redis
	window可以去[网盘](https://pan.baidu.com/s/1pMoB83h) 下载一个, 调用里面的bat即可安装
2. 支持py2及py3 windows; macos支持py3， linux(非图形状态下)支持py3
3. 用pip install -r requirements.txt安装相关依赖包

- 安装
  * 安装Anaconda
  * 下载autoxd
  ```
  git clone https://github.com/nessessary/autoxd.git
  cd autoxd
  pip install -r requirements.txt
  pip install git+https://github.com/hanxiaomax/pyh.git
  pip install git+https://github.com/matplotlib/mpl_finance.git
  python setup.py install
  ```
  * 安装redis
  * 跑strategy/five_chengben.py, 策略都放在该目录

- 使用

1. 跑five_chengben.py, 定义参数  setParams函数
  实现策略 Run函数, 修改cpu_num可以使用多进程
  ```
  cd strategy
  python five_changben.py
  ```
  
2. 数据源,使用自定义的数据; 注意,已使用ths分红表进行了前复权<br>
      * 使用自定义的第三方数据源， 已实现了一个调用tushare的例子,
      datasource_mode=stock.DataSources.datafrom.custom
      * 5分钟线使用的是pytdx的例子

3. 调用
```python
    #设置策略参数
  def setParams(s):
  	s.setParams(trade_num = 300,
                      pl=publish.Publish()	#发布至页面, 注释则不发布
                      )
  backtest_policy.test_strategy(codes, BollFenCangKline, setParams, mode=myenum.hisdat_mode,
                                start_day='2017-4-10', end_day='2018-9-15',
                                datasource_mode=DataSources.datafrom.custom,
                                datasource_fn=fnSample
                                )
```
