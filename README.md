autoxd 回测框架
------

简单快捷的A股回测环境， 适合编写T+0策略

- 特性
  * 使用pandas编写策略
  * 结果可以在页面显示， 类似matlab的publish
  * 并行执行策略(需要安装redis)
  * 本地账户， 模拟实盘交易细节， 支持T+0， 交易成本计算
  * 自创FOUR指标， 简单计算多空

- 变更
  * v0.4.7 恢复机器学习相关, 添加静态硬识别, 当前开发版本python3.7.4
  * 拼音简写增加港股通
  * v0.4.6 变更拼音简写的表示方式, 简写后面直接跟中文名; 会影响之前的版本
  * v0.4.5 删除机器学习相关
  * v0.4.4 复权计算使用的分红表原来是动态抓网页， 现在使用静态方式， 从数据目录中取
  * v0.4.3 废弃python2支持，python3.6 pandas 1.0
  * v0.4.1 支持macos
  * v0.4 大幅优化速度
  * v0.3 python3支持

- 数据维护
  * datas目录下的数据是需要维护的， 一般一个月更新股票列表，同时更新拼音简写, 一个季度更新分红表
  * 更新时间2020-11-5
  * 2021/3/24
  * 2021/5/27
  * 2021/6/15
	* 2021/7/25
	* 2021/8/8

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
1. redis 推荐
2. 支持各平台py3, py2已不维护
3. 用pip install -r requirements.txt安装相关依赖包; python=3.7.4

- 安装
  * 安装Anaconda
  * 下载autoxd
  ```
  git clone https://github.com/nessessary/autoxd.git
  cd autoxd
  pip install -r requirements.txt
  pip install git+https://github.com/hanxiaomax/pyh.git
  python setup.py install
  ```

- 使用

1. 数据源,使用自定义的数据; 注意,已使用ths分红表进行了前复权<br>
      * 使用自定义的第三方数据源， 已实现了一个调用tushare的例子,
      datasource_mode=stock.DataSources.datafrom.custom
      * 5分钟线使用的是pytdx的例子
	  * tdx行情ip查询connect.cfg, 然后修改warp_pytdx.py里的ip

2. 先进行静态的单一状态识别
   ```
   python autoxd\hard_recog\single_boll.py
   ```
   通过调整技术指标的判断来触发信号

3. 跑five_chengben.py, 根据静态分析的结果来定义参数  setParams函数
  实现策略 Run函数, 修改cpu_num可以使用多进程
  ```
  cd strategy
  python five_changben.py
  ```
  调用
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

4. gym增强学习, 实现了一个gym的环境，套了一个dqn的算法，功能有限，只是作为一个例子
   ```
   python autoxd\trading_gym\gym_eval.py
   ```
