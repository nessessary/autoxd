回测
------
	
	回測使用的账户为一个本地模拟账户(见account.py)， 接口和实盘接口一致， 因此有必要在回測系统里做一下测试

	1) 实现一个结果报告函数

	2) Tick级汇报函数<br>
	   暂未实现

	3) 数据源<br>
	   请到 [网盘](http://pan.baidu.com/s/1kVsr8aV) 下载一个数据源， 包含300033的日线，5分钟线，及分时线, 下载后放置到python_strategy\datas目录中
	
	4) 执行
	   用python直接执行策略py<br>
	   可看见输出的结果图<br>
	   ![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_backtest_result.png)

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

