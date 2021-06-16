#coding:utf8

"""执行训练好的模型"""

from autoxd.trading_gym import trading_gym
from autoxd.reinforcement_learning.img_dqn import DQN
import time
from autoxd.account import AccountMgr
from autoxd import agl
import os

def test():
    
    agent = DQN()    
    
    df = trading_gym.getData()
    #为了测试缩短df
    test_len = int(len(df)*0.2)
    df = df[-test_len:]
    df = trading_gym.genTradeDf(df, int(len(df)/10))
    
    #train
    env = trading_gym.ATgymEnv(df)
    for i in range(30): #现在的速度一天只能跑30次
        observation = env.reset()
        assert(observation is not None)
        
        reward_total = 0
        agl.tic()
        while True:
            try:
                env.render()
                time.sleep(.05)
            except:
                pass
            
            action = agent.egreedy_action(observation)
            #print('action=', action)
            next_observation, reward, done, info = env.step(action)
            #print('observation=', str(next_observation.shape))
            observation = next_observation
            
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