#coding:utf8

"""实现自有gym"""
import gym, time
import pyglet
import numpy as np
from numpy.random import randn
#from gym.envs.classic_control import rendering
import myplot
from autoxd import myredis, stock, agl

id = 'autoxd-gym-v0'
data_interval = 30

class ATgymEnv(gym.Env):
    def __init__(self, df):
        #v = randn(10)
        #self._plot(v)
        df = df.dropna()
        self.df = df[['boll_up','boll_mid','boll_lower','c']]
        self.index = 0
        self.viewer = None
        self.df_trade = df['trade']
        #clrs = []
        #for i in range(4):
            #clr = agl.GenRandomArray(255, 3) / 255
            #clrs.append(clr)
        #key = myredis.gen_keyname(__file__, self.__init__)
        #myredis.delkey(key)
        #clrs = myredis.createRedisVal(key, clrs).get()
        clrs = [[1,0,0],[0,1,0],[0,0,1],[0,0,0]]
        self.clrs = clrs

        self.imgs = myplot.df_to_imgs(self.df, data_interval, 128, bInit=False)
        
        self._gen_label()
        
    def step(self, action):
        """action: 1,0,-1
        return: observation, reward, done, info
        """
        n = data_interval
        self.index += 1
        done = False
        if self.index >= len(self.df) - n:
            done = True
        #observation = self.df[self.index:self.index+n]
        observation = self._get_observation()
        reward = action
        info = None
        if action == 0:
            reward = 0
        if action > 0:
            reward = self.label_buy[self.index]
        if action < 0:
            reward = self.label_sell[self.index]
        return observation, reward, done, info

    def reset(self):
        #print('reset')
        self.index = data_interval-1
        observation = self._get_observation()
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
    
    def _gen_label(self):
        """整体计算一次， 在构造中调用"""
        df = self.df
        #有交易机会那么加1
        #一个index是5分钟， 4个小时是48个周期
        n = 48
        r = 0.02
        self.label_sell = np.zeros(len(df))
        self.label_buy = np.zeros(len(df))
        #分别记录买卖的label
        index = 0
        for i, row in df.iterrows():
            cur_close = row['c']
            index2 = min(index+n, len(df)-1)
            after_high = np.max(df['c'][index:index2])
            self.label_sell[index] = (after_high - cur_close) / cur_close > r
            after_low = np.min(df['c'][index:index2])
            self.label_buy[index] = (cur_close - after_low) / cur_close > r
            index += 1

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
    
def getData():
    def get():
        from autoxd.warp_pytdx import getFive
        from autoxd.pinyin import stock_pinyin3 as jx
        code = jx.HWWH
        df = getFive(code)
        df = stock.TDX_BOLL_df(df)
        return df
    def getLocal():
        import pandas as pd
        fname = '../datas/002304.csv'
        df = pd.read_csv(fname)
        df.index = pd.DatetimeIndex( df[df.columns[0]])
        df = stock.TDX_BOLL_df(df)
        return df        
    key = myredis.gen_keyname(__file__, getData)
    #myredis.delkey(key)
    return myredis.createRedisVal(key, getLocal).get()

def genTradeDf(df, num):
    """产生随机交易位置
    return: df"""
    size = len(df)
    indexs = np.random.randint(0, size, num, dtype=int)
    df.is_copy = False
    df['trade'] = 0
    # -1, 0, 1
    a = np.random.randint(0,3, num, dtype=int) - 1
    df.loc[df.index[indexs], 'trade'] = a
    return df
    
def test():
    from autoxd.reinforcement_learning.img_dqn import DQN
    agent = DQN()    
    
    df = getData()
    #为了测试缩短df
    df = df[-200:]
    df = genTradeDf(df, int(len(df)/10))
    
    #train
    env = ATgymEnv(df)
    for i in randn(100):
        observation = env.reset()
        assert(observation is not None)
        print('reset', observation.shape)
        while True:
            try:
                env.render()
                time.sleep(.1)
            except:
                pass
            
            action = agent.egreedy_action(observation)
            print('action=', action)
            next_observation, reward, done, info = env.step(action)
            print('observation=', str(next_observation.shape))
            agent.perceive(observation, action, reward, next_observation, done)
            observation = next_observation
            #print('%d,%d', action, reward)
            print('reward=', reward)
            if done:
                break
    
    #test
        
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
