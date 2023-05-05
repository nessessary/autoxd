#coding:utf8

"""执行训练好的模型"""

from autoxd.trading_gym import trading_gym, StockTradingEnv
import time
from autoxd.account import AccountMgr
from autoxd import agl
import os
from autoxd.pinyin import stock_pinyin3 as jx
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy

def test():
    code = jx.YHGF洋河股份
    df = trading_gym.getData(code)
    #为了测试缩短df
    test_len = int(len(df)*0.2)
    df = df[-test_len:]
    df = trading_gym.genTradeDf(df, int(len(df)/10))
    
    #train
    env = trading_gym.ATgymEnv(code, df)
    model = DQN('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=20000)
    mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)
    for i in range(30): #现在的速度一天只能跑30次
        observation = env.reset()
        assert(observation is not None)
        
        reward_total = 0
        agl.tic()
        while True:
            
            action,_ = model.predict(observation, deterministic=True)
            #print('action=', action)
            observation, reward, done, info = env.step(action)
            try:
                env.render()
                time.sleep(.05)
            except:
                pass
            
            #print('%d,%d', action, reward)
            #print('reward=', reward)
            reward_total += reward
            if done:
                print('[%d]reward_total='%i, reward_total)
                print(AccountMgr(env.account, df.iloc[-1]['c'], env.code).total_money())
                agl.toc()
                break
            

if __name__ == '__main__':
    test()
    #main()