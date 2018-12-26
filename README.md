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
2. 支持py2及py3 windows; macos支持py3， linux未知
3. 推荐使用wingide， 可直接加载wpr项目文件
4. 用pip install -r requirements.txt安装相关依赖包

- 安装
  * 安装Anaconda
  * 下载autoxd
  ```
  git clone https://github.com/nessessary/autoxd.git
  cd autoxd
  pip install -r requirements.txt
  python setup.py install
  ```
  * 如遇到不能用pip安装的包， 请执行搜索安装，估计只有一个pyH需要手动安装的
  ```
  pip install git+https://github.com/hanxiaomax/pyh.git
  ```
  * 安装redis
  * 跑python_strategy/strategy/five_changben.py, 策略都放在该目录

- 使用

1. 数据源,使用自定义的数据; 注意,已使用ths分红表进行了前复权<br>
      * 使用自定义的第三方数据源， 已实现了一个调用tushare的例子,
      datasource_mode=stock.DataSources.datafrom.custom
      * 5分钟线使用的是pytdx的例子

2. 调用
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
