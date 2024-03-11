#coding:utf8

"""实现自有gym"""
import gym, time
import os
import pyglet
import numpy as np
from numpy.random import randn
from gym.envs.classic_control import rendering
from autoxd.trading_gym import myplot
from autoxd import myredis, stock, agl
from autoxd import account
from autoxd.pinyin import stock_pinyin3 as jx
from gym import spaces
#from stable_baselines3 import DQN
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EveryNTimesteps
from stable_baselines3.common.evaluation import evaluate_policy
from autoxd.account import AccountMgr

MAX_ACCOUNT_BALANCE = 2147483647
MAX_NUM_SHARES = 2147483647
MAX_SHARE_PRICE = 5000
MAX_OPEN_POSITIONS = 5
MAX_STEPS = 20000

INITIAL_ACCOUNT_BALANCE = 10000

id = 'autoxd-gym-v0'
data_interval = 30

class ATgymEnv(gym.Env):
    def __init__(self, code, df):
        super(ATgymEnv, self).__init__()
        #v = randn(10)
        #self._plot(v)
        self.df = df.dropna()
        #self.df = df[['boll_up','boll_mid','boll_lower','c']]
        self.index = 0
        self.viewer = None
        #self.df_trade = df['trade'].copy()
        #self.df_trade.is_copy = False
        self.code = code
        #clrs = []
        #for i in range(4):
            #clr = agl.GenRandomArray(255, 3) / 255
            #clrs.append(clr)
        #key = myredis.gen_keyname(__file__, self.__init__)
        #myredis.delkey(key)
        #clrs = myredis.createRedisVal(key, clrs).get()
        clrs = [[1,0,0],[0,1,0],[0,0,1],[0,0,0]]
        self.clrs = clrs

        #self.imgs = myplot.df_to_imgs(self.df, data_interval, 128, bInit=True)
        backtester = account.BackTesting()
        self.account = account.LocalAcount(backtester)
        price = self.df.iloc[0]['c']
        self.account._buy( self.code, price, account.ShouShu(self.account.init_money/2/price), str(self.df.index[0]))
        
        self.reward_range = (-100, 100)
    
        self.action_space = spaces.Discrete(3)
    
        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
                low=0, high=1, shape=self._get_observation().shape, dtype=np.float16)
        
        
    def step(self, action):
        """action: 0,1,2
        return: observation, reward, done, info
        """
        action -= 1

        info = {}
        code = self.code
        price = self.df['c'][self.index]
        num = 500
        row = self.df.iloc[self.index]
        reward = 0
        acount_mgr = AccountMgr(self.account, price, self.code)
        if action > 0:#buy
            if acount_mgr.can_use_money() > num * price:
                self.account._buy(code, price, num, str(self.df.index[self.index]))
                #reward =  acount_mgr.yin_kui() * 0.95 - price
                reward = (row['boll_mid'] - price) / row['boll_mid'] 
                self.df['trade'].iat[self.index] = 1
            #满仓扣分
            else:
                reward = -1
            
        if action < 0:#sell
            if acount_mgr.getCurCanWei() > num:
                self.account._sell(code, price, num, str(self.df.index[self.index]))
                self.df['trade'].iat[self.index] = -1
                #reward = (acount_mgr.last_chengjiao_price() - price) / price
                reward = (acount_mgr.yin_kui() - price) / (price * 2)
                reward = (price - row['boll_mid']) / row['boll_mid'] 
            else:
                reward = -1
                
        if action == 0:
            reward = -0.01
            self.df['trade'].iat[self.index] = 0
            #if len(self.df) > 10 and (self.df['trade'][self.index-10:self.index] == 0).all():
                #reward = 0
            
            
        self.index += 1
        done = False
        if self.index > len(self.df) - 6:
            self.index = 0
            #done = True
        #observation = self.df[self.index:self.index+n]
        observation = self._get_observation()
            
            
        if abs(acount_mgr.total_money() - self.account.init_money) / self.account.init_money > 0.05:
            done = True
            
        #reward = 0
        #if done:
            #reward = self._calc_final_reward()
        
        return observation, reward, done, info

    def reset(self):
        #print('reset')
        self.index = 0
        backtester = account.BackTesting()
        self.account = account.LocalAcount(backtester)
        price = self.df.iloc[0]['c']
        self.account._buy( self.code, price, account.ShouShu(self.account.init_money/2/price), str(self.df.index[0]))
        
        observation = self._get_observation()
        
        return observation
    
    def _calc_final_reward(self):
        # 最终奖励
        account_mgr = account.AccountMgr(self.account, self.df.iloc[-1]['c'], self.code)
        
        return (account_mgr.total_money() - account_mgr.init_money()) / account_mgr.init_money()
    
    def _calculate_reward(self):  
        #即时奖励
        pass
    
    def _calculate_discounted_reward(self, rewards):  
        """计算累计折扣奖励"""  
        discounted_sum = 0  
        for t, reward in enumerate(rewards[::-1]):  
            discounted_sum = reward + self.discount_factor * discounted_sum  
        return discounted_sum
    
    def render(self, mode='human'):
        """把tk的实现移植过来, 添加成交量与收益"""
        #print('render')
        screen_width = 600
        screen_height = 400

        if self.viewer is None:
            from gym.envs.classic_control import rendering
            self.viewer = rendering.Viewer(screen_width, screen_height)
        
        #lines = randn(4, 2) * screen_height
        #lines = np.array([[10,20],[30,40], [100,100],[200,200]])
        #self.viewer.draw_polyline(lines, color=(1,0,0))

        v = myplot.convert(screen_width, screen_height, self.df[self.index:self.index+data_interval])
        #print(v[0])
        for i, lines in enumerate(v): 
            #print(lines[-3:])
            self.viewer.draw_polyline(lines, color=self.clrs[i])

        #标注交易点
        trades = self.df['trade'][self.index:self.index+data_interval]
        for trade_index, sign in enumerate(trades):
            #trade_index = np.random.randint(data_interval)
            pt = v[-1][trade_index]
            #画交易点
            if sign != 0:
                self._draw_arrow(pt, sign<0)
        
        return self.viewer.render(return_rgb_array = mode=='rgb_array')
        
    def _get_observation(self):
        """输出一个2d, 把boll及close转换为2d, 同render的转换
        df=>img=>martix
        return: np.ndarray shape(n,n)
        """
        #index = self.index - data_interval
        #return self.imgs[index]
        
        frame = np.array([
            self.df['boll_up'].iloc[self.index:self.index+5].values / MAX_SHARE_PRICE, 
            self.df['boll_lower'].iloc[self.index:self.index+5].values / MAX_SHARE_PRICE,
            self.df['boll_mid'].iloc[self.index:self.index+5].values / MAX_SHARE_PRICE, 
            self.df['c'].iloc[self.index: self.index+5].values / MAX_SHARE_PRICE,
            self.df['v'].iloc[self.index: self.index+5].values / MAX_NUM_SHARES,
        ])
        
        
        #
        price = self.df.iloc[self.index]['c']
        account_mgr = account.AccountMgr(self.account, price, self.code)
        obs = np.append(frame, [[
                account_mgr.can_use_money() / account_mgr.total_money(),
                self.df['c'].iloc[0] / 300,
                account_mgr.getCanSellNum() *price / account_mgr.total_money(),
                account_mgr.yin_kui() / (price * 2),
                account_mgr.getCurCanWei() *price / account_mgr.total_money(),
                #account_mgr.get_BuyAvgPrice() / MAX_SHARE_PRICE,
                ]], axis=0)
    
        return obs
        
    
    def _draw_arrow(self, pt, is_sell):
        """画交易点, 绘制一个锐角三角形
        pt: (x,y) 为三角形的顶点
        """
        x, y = pt
        if is_sell:
            #向下
            x1,y1, x2,y2 = agl.calc_vert(x, y, x, y+50)
            v = np.array([[x,y], [x1,y1], [x2,y2],[x,y]])
            self.viewer.draw_polygon(v, color=[0,1,0])
        else:
            #向上
            x1,y1, x2,y2 = agl.calc_vert(x, y, x, y-50)
            v = np.array([[x,y], [x1,y1], [x2,y2],[x,y]])
            self.viewer.draw_polygon(v, color=[1,0,0])
    
def getData(code):
    from autoxd.warp_pytdx import getFive
    df = getFive(code)
    #df = stock.TDX_BOLL_df(df)
    return df

def genTradeDf(df, num):
    """产生随机交易位置
    return: df"""
    size = len(df)
    indexs = np.random.randint(0, size, num, dtype=int)
    df.is_copy = False
    df['trade'] = 0
    # -1, 0, 1
    #a = np.random.randint(0,3, num, dtype=int) - 1
    #df.loc[df.index[indexs], 'trade'] = a
    return df
    
def test():
    code = jx.YHGF洋河股份
    df = getData(code)
    upper, mid, lower = stock.TDX_BOLL(df['c'])
    df['boll_up'] = upper
    df['boll_mid'] = mid
    df['boll_lower'] = lower
    df['trade'] = 0
    df = df[20:]
    
    #train
    env = ATgymEnv(code, df)
    #model = DQN('MlpPolicy', env, verbose=1)
    #model.learn(total_timesteps=20000)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=20000*1)
    if 0:
        # 创建一个CheckpointCallback，用于保存最优模型
        checkpoint_callback = CheckpointCallback(save_freq=1000, save_path='./logs/')    
        best_model_path = os.path.join(checkpoint_callback.save_path, 'best_model.zip')
        if not os.path.exists(best_model_path):
            model.learn(total_timesteps=20000*1, callback=checkpoint_callback, tb_log_name="ppo_stocktrade")
            model.save(best_model_path)
        if os.path.exists(best_model_path):
            model = PPO.load(best_model_path, env=env)

    #mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)


    observation = env.reset()
    reward_total = 0
    agl.tic()
    while True:
        
        action,_ = model.predict(observation, deterministic=True)
        print('action=', action)
        observation, reward, done, info = env.step(action)
        if env.index >= len(env.df) - 7:
            done = True
        try:
            env.render()
            time.sleep(.05)
        except:
            pass
        
        print('%d,%d' % (action, reward))
        reward_total += reward
        if done:
            print('reward_total=', reward_total)
            account = AccountMgr(env.account, df.iloc[-1]['c'], env.code)
            print(account.total_money())
            df = env.account.ChengJiao()[str('成交日期|成交时间|证券代码|证券名称|买0卖1|买卖标志|委托价格|委托数量').split('|')]
            print(df.to_markdown())
            agl.toc()
            break
        
def test2():        
    env = gym.make('CartPole-v0')
    env = env.unwrapped
    total_steps = 0
    for i_episode in range(100):
        observation = env.reset()
        while True:
            env.render()
            action = 1
            observation_, reward, done, info = env.step(action)
            if done:
                break
            observation = observation_
            total_steps += 1    
    
if __name__ == "__main__":
    test()
    #test2()
