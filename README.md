Autoxd
======

A-share automated trading tool

一个A股的自动化交易工具

概述
----
鉴于现有的工具用起来不太顺手， 成熟的行情软件自动交易方面又比较弱， 因此编写了该软件。该软件在有合适策略的情况下， 可以自动进行交易， 策略由python编写。
适合使用该软件的目标人群<br>
1. 希望使用quant方式交易的投资者， 
2. 有一定的python编程经验, 可以自行实现策略的 
3. 希望策略在本地执行的， 本软件承诺不上传任何用户数据

功能
----
1. 行情， 系统自动下载行情保存到数据池中
2. 交易接口， 暂时只支持中信建投证券
3. 由python实现的策略， 通过编写策略从而实现自动化交易

使用
----
1. 下载安装文件 [网盘](http://pan.baidu.com/s/1kUHK3Dd)
2. 安装后运行， 需要的软硬件要求如下<br>
	WIN7 8G内存 硬盘10G以上空间
3. 一个典型的执行过程如下
	1) 填写资金账号， 成功后下次不用再输入, 帐号以加密形式存储在本地， 并不容易泄露
	![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_main.png)
	2) 账号输入后， 系统即开始运行， 下载行情，并登录交易账号, 成功后类似下图
	![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_enter.png)
	3) 行情下载完成后即会执行策略， 默认策略是一个简单的demo， 仅仅是读取交易账户中股票列表的第一行， 如果有买入股票的话
	![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_stocklist.png)

	4) 委托下单
	![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_weituo.png)
4. 如果不想使用交易接口， 只使用行情部分的话， 只需要输入一个短帐号，比如用户名为1， 密码为1， 那么下次就不会提示输入交易帐号了。
5. 半自动交易， 如果没有合适的策略， 那么可以采用半自动交易方式， 在策略中加入条件判断， 符合条件时进行语音播报同时通知界面显示
	![image](https://github.com/nessessary/autoxd/raw/master/pics/autoxd_sign_speak.png)

```python
	    #信号发生时语音播报, 并通知界面回显
	    if price > boll_poss[1] or price < boll_poss[-2]:
		codename = stock.GetCodeName(code)
		s = '%s, %.2f'%(codename, price)
		self.data.show(codename)    #通知界面显示
		self.data.speak2(s)	    #语音播报
```

升级
----
本软件安装包比较大， 如果装过一次后，可以使用升级包来覆盖主文件，
1. 查看[changlog](https://github.com/nessessary/autoxd/blob/master/changelog.txt) 看更新了什么
2. [下载升级包](http://pan.baidu.com/s/1o83HxIq)   把里面的文件覆盖至安装目录

回测
----
使用该系统前可以先进行策略的回测开发, 毕竟有一个好的策略才能进行自动化交易
请迁出python_strategy目录， 先在该目录中跑一个回测， 执行boll_pramid.py将得到一个默认回测
具体过程查询 [回测文档](https://github.com/nessessary/autoxd/blob/master/python_strategy/README.md)

策略
----
1. Python环境
	1) 安装文件附了一份Anaconda2
	2) 包含Redis一份， 如果本地安装了将不生效
	3) 主要使用pandas库
	4) 策略目录在python_strategy\strategy
	   默认使用的策略文件为boll_pramid.py
2. 策略入口, 见boll_pramid.py<br>
	注意：系统安装或升级都会覆盖默认策略， 删除时策略目录也会删除;因此最好有两个目录，一个回测目录和一个执行目录<br>
	回测目录为git迁出的目录， 执行目录就是安装后的目录<br>
	另外， 自动化交易适合高频一些的策略， 因此默认策略就是一个基于boll的区间交易策略， 并且会持续优化，直至可以稳定的执行
	1) 系统会遍历下载的股票， 同时调用Run
	2) 锁定策略处理的股票， 填写AllowCode里的list

```python
class Strategy_Boll_Pre(qjjy.Strategy):
    """为了实现预埋单"""
    def AllowCode(self, code):
	codes = ['300033']		 #自己想交易的股票
	return code in codes
    
    #入口函数
    def Run(self):
	"""每个股票调用一次该函数, 调用后会释放， 因此不能使用简单的全局变量， 而需要使用redis来持续化
	另外， 交易接口要慎用， 比如列表查询， 可保存至redis， 
	不要每进入函数都查询一下， 下单则无这种情况， 因为都是条件触发， 所以直接调即可
	"""
        #self._log('Strategy_Boll_Pre')
	account = self._getAccount()	#获取交易账户
	def run_stocklist():
	    df = account.StockList()	#查询股票列表
	    self._log(df.iloc[0])
	PostTask(run_stocklist,	100)	#每100秒执行一次
	
	#以下为交易测试
        code = self.data.get_code()	#当前策略处理的股票
	if not self.is_backtesting and not self.AllowCode(code):
	    return

        self._log(code)
	df_hisdat = pd_help.Df(self.data.get_hisdat(code))	#日k线
	df_fenshi = pd_help.Df(self.data.get_fenshi(code))	#日分时
	if len(df_fenshi.df) == 0:
	    self.data.log(code+u"停牌")
	    return
	price = df_fenshi.getLastPrice()    #当前股价
        closes = df_hisdat.getCloses()
	yestoday_close = closes[-2]	    #昨日收盘价
	self._log(price)
	self._log(yestoday_close)
	
	def buy_at_price_once():
	    """在某一个价位下一个单"""
	    cur_price = price * (1-0.02)
	    if cur_price < yestoday_close*0.901:
		cur_price = yestoday_close*0.901
		cur_price = agl.FloatToStr(cur_price)
	    account.Order(0, code, cur_price, 100)	#买入
	#测试下单请放开下行的注释
	#PostTask(buy_at_price_once, 60*60*3)	
	return	
```

3. 行情
	1) 现只获取日k线, 5分钟线和分时线
	2) 具体获取的股票行情见config.ini, 一般的只针对关注的股票获取行情并执行策略会快很多, 修改后下次启动后执行<br>
	   修改listinfo_codes中的股票为你的自选股
```python
#取列表方式 0/1		取全部、取部分
#测试版本只支持取部分, 且不超过20个个股
listinfo_type=1
listinfo_codes="002074|002108|300399|300384|300033|300059|002174"
```

4. 如何调用交易接口
	1) 正确输入账号进入系统后， 交易账号即会登录， 且保持在线， 注意， 本系统使用的是通信协议登录方式，不影响其他软件，
	   也就是一个机器上可以多个软件同时登陆
	2) 上面的例子可以看见使用了股票列表查询account.StockList(), 和买入account.Order(0, code, cur_price, 100)
	   全部的交易接口见tc.py
	3) 使用命令行方式调用接口
	   在ipython中
```python
import tc
tc.Buy('300033', 60.1, 100)
#tc.Buy(tc.ths, 60.1, 100)
```


反馈
----
本软件现处于测试期， 功能比较简单， bug也再所难免，希望使用了的同学能提供宝贵意见， 让作者有继续开发下去的动力<br>
遇到崩溃， 请把安装目录下的dmp文件提交到群里, 或者联系作者，作者会解决bug<br>

交流请加qq群 213155151 <br>
