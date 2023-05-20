#coding:utf8

"""实现自有gym"""
import gym, time
import pyglet
import numpy as np
from numpy.random import randn
from gym.envs.classic_control import rendering
import myplot
from autoxd import myredis, stock, agl
from autoxd import account
from autoxd.pinyin import stock_pinyin3 as jx
from gym import spaces
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy
from autoxd.account import AccountMgr

id = 'autoxd-gym-v0'
data_interval = 30

class ATgymEnv(gym.Env):
    def __init__(self, code, df):
        super(ATgymEnv, self).__init__()
        #v = randn(10)
        #self._plot(v)
        df = df.dropna()
        self.df = df[['boll_up','boll_mid','boll_lower','c']]
        self.index = 0
        self.viewer = None
        self.df_trade = df['trade'].copy()
        self.df_trade.is_copy = False
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

        self.imgs = myplot.df_to_imgs(self.df, data_interval, 128, bInit=True)
        
        self.reward_range = (-100, 100)
    
        self.action_space = spaces.Discrete(3)
    
        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
                low=0, high=255, shape=self.imgs[0].shape, dtype=np.int8)
        
        
    def step(self, action):
        """action: 1,0,-1
        return: observation, reward, done, info
        """
            
        n = data_interval
        reward = action
        info = {}
        code = self.code
        price = self.df['c'][self.index]
        num = 1000
        if action == 0:
            reward = 0
        row = self.df.iloc[self.index]
        if action > 0:
            reward = (row['boll_mid'] - price) / row['boll_mid']
            self.account.Order(0, code, price, num)
            self.df_trade.iat[self.index] = 1
        if action < 0:
            reward = (price - row['boll_mid']) / row['boll_mid']
            self.account.Order(1, code, price, num)
            self.df_trade.iat[self.index] = -1
            
        self.index += 1
        done = False
        if self.index > len(self.df) - 1:
            self.index = data_interval
        #observation = self.df[self.index:self.index+n]
        observation = self._get_observation()
            
            
        acount_mgr = AccountMgr(self.account, price, self.code)
        if abs(acount_mgr.total_money() - self.account.init_money) / self.account.init_money > 0.05:
            done = True
        return observation, reward, done, info

    def reset(self):
        #print('reset')
        self.index = data_interval
        observation = self._get_observation()
        backtester = account.BackTesting()
        self.account = account.LocalAcount(backtester)
        return observation

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
        trades = self.df_trade[self.index:self.index+data_interval]
        for trade_index, sign in enumerate(trades):
            #trade_index = np.random.randint(data_interval)
            pt = v[-1][trade_index]
            #画交易点
            if sign != 0:
                self._draw_arrow(pt, sign<0)
        
        return self.viewer.render(return_rgb_array = mode=='rgb_array')
        
        
    def close(self):
        return

    def seed(self, seed=None):
        return
    
        
    def _get_observation(self):
        """输出一个2d, 把boll及close转换为2d, 同render的转换
        df=>img=>martix
        return: np.ndarray shape(n,n)
        """
        index = self.index - data_interval
        return self.imgs[index]
    
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
    df = stock.TDX_BOLL_df(df)
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
    #为了测试缩短df
    test_len = int(len(df)*0.2)
    #df = df[-test_len:]
    df = genTradeDf(df, int(len(df)/10))
    
    #train
    env = ATgymEnv(code, df)
    model = DQN('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=20000)
    mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)

    observation = env.reset()
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
        reward_total += reward
        if done:
            print('reward_total=', reward_total)
            account = AccountMgr(env.account, df.iloc[-1]['c'], env.code)
            print(account.total_money())
            print(env.account.ChengJiao())
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
