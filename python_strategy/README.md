回测
------

回測使用的账户为一个本地模拟账户(见account.py)， 接口和实盘接口一致， 因此有必要在回測系统里做一下测试

1. 数据源<br>
   请到 [网盘](http://pan.baidu.com/s/1bpto0wv) 下载一个数据源， 包含300033的日线，5分钟线，及分时线, 下载后放置到<br>
   python_strategy\datas目录中<br>
   (现在的数据源仅仅是起一个demo的作用， 要使用全部数据源可以联系作者或者修改框架使用第三方数据源)<br>
   stock_createThs.searial为同花顺F10全部数据, 最后更新日期2017-9-6<br>
   自动加载， 使用见stock.py里的StockInfoThs<br>
   前复权使用同花顺的分红表， 具体见stock.py里的calc_fuquan_use_fenhong<br>

2. 依赖包问题， 如果使用自己的anaconda， 需要32bit python2.7版本的， 其次需要的库为ta-lib, redis, charade等<br>
   或者下载安装包， 里面带一份anaconda， 已经包含了所需要的库， 使用该目录即可

3. 执行
   用ide打开缺省策略boll_pramid.py并执行<br>
   可看见输出的结果图<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result.png)
   也支持中间结果显示TickReport<br>
   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_tick_1.png)

<br>

```python
    def Report(self, start_day, end_day):
	"""回測报告"""
	self._getAccount().Report(end_day)
	#return
	#绘制图形
	#end_day = help.MyDate.s_Dec(end_day, 1)
	bars = stock.CreateFenshiPd(self.code, start_day, end_day)
	if len(bars) == 0:
	    return
	bars = bars.resample('1min').mean()
	bars['positions'] = 0
	bars['c'] = bars['p']
	bars = bars.dropna()
	df = self._getAccount().ChengJiao()
	df_zhijing = self._getAccount().ZhiJing()
	df_zhijing = df_zhijing[bars.index[0]:]
	df_changwei = self._getAccount().ChengJiao()
	cols = ['买卖标志','委托数量']
	df_flag = df_changwei[cols[0]].map(lambda x: agl.where(int(x), -1, 1))
	df_changwei[cols[1]] *= df_flag
	changwei = stock.GuiYiHua(df_changwei[cols[1]].cumsum())
	for i in range(len(df)):
	    index = df.index[i]
	    bSell = bool(df.iloc[i]['买卖标志']=='1')
	    if index in bars.index:
		#bars.ix[index]['positions'] = agl.where(bSell, -1, 1)
		bars.set_value(index, 'positions', agl.where(bSell, -1, 1))
	trade_positions = np.array(bars['positions'])
	ui.TradeResult_Boll(self.code, bars, trade_positions, \
	    stock.GuiYiHua(df_zhijing['资产']), changwei)
```

