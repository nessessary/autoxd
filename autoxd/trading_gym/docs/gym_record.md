My Plan:

gym render is complete.

plan to implement action.

action = random
observation = img => martix
reward = income or technology

aglorithm 
- DDQN
- DDPG


# 计算过程V1
2019-1-10 v1
imgs = 370
并未收敛
[73]reward_total= 100.0
[74]reward_total= 93.0
[75]reward_total= 103.0
[76]reward_total= 97.0
[77]reward_total= 86.0
[78]reward_total= 88.0
[79]reward_total= 98.0
[80]reward_total= 93.0
[81]reward_total= 100.0
[82]reward_total= 102.0
[83]reward_total= 107.0
[84]reward_total= 105.0
[85]reward_total= 101.0
[86]reward_total= 103.0
[87]reward_total= 110.0

大幅扩大样本， 再尝试一次
imgs = 800-30

```
load imgs length =  18629
[0]reward_total= 3271.0

Elapsed time: 2469.38 seconds / 41.16 min / 0.69 hour  
```

在大样本下貌似效果好一点

load imgs length =  18629
[0]reward_total= 3271.0

Elapsed time: 2469.38 seconds / 41.16 min / 0.69 hour     0:41:09.381131

[1]reward_total= 3251.0

Elapsed time: 2476.19 seconds / 41.27 min / 0.69 hour     0:41:16.187459

[2]reward_total= 3231.0

Elapsed time: 2477.32 seconds / 41.29 min / 0.69 hour     0:41:17.315778

[3]reward_total= 3230.0

Elapsed time: 2472.80 seconds / 41.21 min / 0.69 hour     0:41:12.800751

[4]reward_total= 3291.0

Elapsed time: 2475.86 seconds / 41.26 min / 0.69 hour     0:41:15.855773

[5]reward_total= 3240.0

Elapsed time: 2477.95 seconds / 41.30 min / 0.69 hour     0:41:17.947548

[6]reward_total= 3244.0

Elapsed time: 2474.24 seconds / 41.24 min / 0.69 hour     0:41:14.237451

[7]reward_total= 3349.0

Elapsed time: 2468.58 seconds / 41.14 min / 0.69 hour     0:41:08.580658

[8]reward_total= 3298.0

Elapsed time: 2473.60 seconds / 41.23 min / 0.69 hour     0:41:13.601729

[9]reward_total= 3262.0

Elapsed time: 2472.93 seconds / 41.22 min / 0.69 hour     0:41:12.933161

[10]reward_total= 3347.0

Elapsed time: 2474.19 seconds / 41.24 min / 0.69 hour     0:41:14.186640

[11]reward_total= 3559.0

Elapsed time: 2473.58 seconds / 41.23 min / 0.69 hour     0:41:13.575686

[12]reward_total= 3675.0

Elapsed time: 2475.19 seconds / 41.25 min / 0.69 hour     0:41:15.189189

[13]reward_total= 3712.0


[28]reward_total= 3908.0

Elapsed time: 2471.76 seconds / 41.20 min / 0.69 hour     0:41:11.758464

[29]reward_total= 3897.0

Elapsed time: 2471.85 seconds / 41.20 min / 0.69 hour     0:41:11.854692

[30]reward_total= 3918.0

Elapsed time: 2471.93 seconds / 41.20 min / 0.69 hour     0:41:11.929450

[31]reward_total= 3839.0

在大样本下， dqn能够学到一些规律

#V2
用总收益作为reward = (cur_money-pre_money) / 1000.0
当前交易后总资产减上一次的总资产
交易手数为初始化资金的2%， 初始建半仓

```
load imgs length =  18629
[0]reward_total= 1269.5999999999408

Elapsed time: 2394.03 seconds / 39.90 min / 0.67 hour     0:39:54.034760

[1]reward_total= 1256.7999999999524

Elapsed time: 2392.22 seconds / 39.87 min / 0.66 hour     0:39:52.215220

[2]reward_total= 1265.4999999999445

Elapsed time: 2398.84 seconds / 39.98 min / 0.67 hour     0:39:58.836400

[3]reward_total= 1263.1999999999466

Elapsed time: 2395.74 seconds / 39.93 min / 0.67 hour     0:39:55.743599

[4]reward_total= 1273.1999999999375

Elapsed time: 2392.67 seconds / 39.88 min / 0.66 hour     0:39:52.672665

[5]reward_total= 1263.0999999999467

Elapsed time: 2389.24 seconds / 39.82 min / 0.66 hour     0:39:49.243078

[6]reward_total= 1274.899999999936

Elapsed time: 2391.85 seconds / 39.86 min / 0.66 hour     0:39:51.850374

[7]reward_total= 1260.1999999999493

Elapsed time: 2392.03 seconds / 39.87 min / 0.66 hour     0:39:52.031153

[8]reward_total= 1272.699999999938

Elapsed time: 2389.58 seconds / 39.83 min / 0.66 hour     0:39:49.583496

[9]reward_total= 1281.7999999999297

Elapsed time: 2390.99 seconds / 39.85 min / 0.66 hour     0:39:50.993420

[10]reward_total= 1293.6999999999189

Elapsed time: 2387.00 seconds / 39.78 min / 0.66 hour     0:39:47.002234

[11]reward_total= 1368.299999999851

Elapsed time: 2387.89 seconds / 39.80 min / 0.66 hour     0:39:47.894299

[12]reward_total= 1527.0999999997064

Elapsed time: 2387.37 seconds / 39.79 min / 0.66 hour     0:39:47.370810

[13]reward_total= 1567.4999999996696

Elapsed time: 2390.18 seconds / 39.84 min / 0.66 hour     0:39:50.179105

[14]reward_total= 1570.6999999996667

Elapsed time: 2389.58 seconds / 39.83 min / 0.66 hour     0:39:49.580336

[15]reward_total= 1574.1999999996635

Elapsed time: 2390.05 seconds / 39.83 min / 0.66 hour     0:39:50.048999

[16]reward_total= 1570.1999999996674

Elapsed time: 2389.22 seconds / 39.82 min / 0.66 hour     0:39:49.215178

[17]reward_total= 1561.599999999675

Elapsed time: 2388.49 seconds / 39.81 min / 0.66 hour     0:39:48.490221

[18]reward_total= 1559.0999999996773

Elapsed time: 2390.11 seconds / 39.84 min / 0.66 hour     0:39:50.106846

[19]reward_total= 1568.8999999996684

Elapsed time: 2388.63 seconds / 39.81 min / 0.66 hour     0:39:48.628379

[20]reward_total= 1570.9999999996664

Elapsed time: 2392.07 seconds / 39.87 min / 0.66 hour     0:39:52.071275

[21]reward_total= 1565.8999999996713

Elapsed time: 2391.83 seconds / 39.86 min / 0.66 hour     0:39:51.830622

[22]reward_total= 1561.8999999996747

Elapsed time: 2390.12 seconds / 39.84 min / 0.66 hour     0:39:50.123192

[23]reward_total= 1577.99999999966

Elapsed time: 2388.56 seconds / 39.81 min / 0.66 hour     0:39:48.561318

[24]reward_total= 1573.2999999996644

Elapsed time: 2389.46 seconds / 39.82 min / 0.66 hour     0:39:49.462464

[25]reward_total= 1568.2999999996691

Elapsed time: 2390.03 seconds / 39.83 min / 0.66 hour     0:39:50.032587

[26]reward_total= 1557.7999999996787

Elapsed time: 2392.65 seconds / 39.88 min / 0.66 hour     0:39:52.654215

[27]reward_total= 1555.4999999996805

Elapsed time: 2392.99 seconds / 39.88 min / 0.66 hour     0:39:52.986748

[28]reward_total= 1564.0999999996727

Elapsed time: 2390.89 seconds / 39.85 min / 0.66 hour     0:39:50.893814

[29]reward_total= 1563.1999999996735

Elapsed time: 2388.31 seconds / 39.81 min / 0.66 hour     0:39:48.305994

[30]reward_total= 1567.19999999967

Elapsed time: 2387.69 seconds / 39.79 min / 0.66 hour     0:39:47.688499

[31]reward_total= 1564.3999999996724

Elapsed time: 2386.91 seconds / 39.78 min / 0.66 hour     0:39:46.905310

[32]reward_total= 1563.799999999673

Elapsed time: 2388.91 seconds / 39.82 min / 0.66 hour     0:39:48.911659

[33]reward_total= 1556.39999999968
```

#实现模型保存...
参考之前的实现
分为两个执行， 一个训练， 并在每个批次后保存模型， 另一个为测试， 读取保存的模型， 跑测试
- 保存时使用global_step参数


###尝试用keras-rl实现dqn等增强

## 尝试用技术面来计算奖励值
* 使用计算公式
reward = boll_var*boll_w+(trade_price_var*trade_time_interval)
* 查表归纳法
* 图形识别法
	