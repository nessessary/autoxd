1. 只能使用技术面来给奖励， 用收益作为奖励不适应当前的设计目标

2. 设计一个公式来计算奖励, 公式计算得分, 与3为二选一; 进行一个组合打分, 满分100
	1） if price > boll_mid: reward = (boll_w - boll_w_pre_corner) / period + (price - boll_up)/price + fn_vol(price, all_prices, all_vols) + four_day
	宽度放大的比率， 当前价格到上轨的距离
	2)  if price < boll_mid: reward = (boll_w - boll_w_pre_corner) / period + (price - boll_down) / price
	
3. 把状态作为图放入cnn_boll进行识别， 识别的结果为分数， 该分数即作为奖励