#coding:utf-8
import pandas as pd
import prettytable
from autoxd import agl
from autoxd import stock

"""单设一个奖励判断， 集成不同的奖励函数
"""


def genBollRewardTable():
    """用svm区分历史的字段, 来进行价值判断
    
    """
    #offset_pos 指price在boll中的位置
    df = pd.DataFrame([['0-1.5','1.5-2.5','2.5-5'], [3,2,1],[1,2,3]], columns=['boll_w','offset_pos','retain'], index=range(3))
    agl.print_prettey_df(df)
    print(df)

"""对于不同的方式， 简单的来说分为当前技术面， 未来技术面， 实际收益， 混合模式"""
def cur_tech(df, action):
    """当前技术面判断, 需要把大的数值转换为1，2等小整数, 类似于归一化； 定义一个价值表， 基于boll_w, price - boll_up
    df: 技术数据
    action : env agent的行为
    return : float reward
    """
    if action == 0:
        return 0
    # 根据技术面进行计算
    boll_w = abs(df.iloc[-1]['boll_up'] - df.iloc[-1]['boll_lower']) / df.iloc[-1]['boll_mid'] * 100
    
    #越过boll且boll宽够大
    if action>0:
        df_boll = df.iloc[-1]['c'] - df.iloc[-1]['boll_up'] 
    else:
        df_boll = df.iloc[-1]['boll_lower'] - df.iloc[-1]['c']
    reward = boll_w * df_boll
    #print(reward)
    return reward

    
def five_four(four, action):
    """只使用four来作为价值评估"""
    threshold = 0.05
    if action == 1 and four < threshold:
        return abs(four) - threshold
    if action <0 and four > threshold:
        return four - threshold
    return 0

def watch_four():
    """观察当前数据源的four情况"""
    from autoxd.pinyin import stock_pinyin3 as jx
    code = jx.ZXJT
    df = stock.getFiveHisdatDf(code, method='tdx')
    #print(df)
    four = stock.FOUR(df['c'].values)
    print(four)
    from autoxd import ui
    from autoxd.pypublish import publish
    pl = publish.Publish()
    ui.DrawTs(pl, four)
    
if __name__ == '__main__':
    #genBollRewardTable()
    watch_four()