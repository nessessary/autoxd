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
        #clrs = []
        #for i in range(4):
            #clr = agl.GenRandomArray(255, 3) / 255
            #clrs.append(clr)
        #key = myredis.gen_keyname(__file__, self.__init__)
        #myredis.delkey(key)
        #clrs = myredis.createRedisVal(key, clrs).get()
        clrs = [[1,0,0],[0,1,0],[0,0,1],[0,0,0]]
        self.clrs = clrs
        
    def step(self, action):
        n = data_interval
        self.index += 1
        done = False
        if self.index >= len(self.df) - n:
            done = True
        observation = self.df[self.index:self.index+n]
        reward = action
        info = None
        return observation, reward, done, info

    def reset(self):
        #print('reset')
        self.index = 0

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
        
        return self.viewer.render(return_rgb_array = mode=='rgb_array')
        
        
    def close(self):
        return

    def seed(self, seed=None):
        return

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
        fname = '../../../cnn_boll/datasource/002304.csv'
        df = pd.read_csv(fname)
        df.index = pd.DatetimeIndex( df[df.columns[0]])
        df = stock.TDX_BOLL_df(df)
        return df        
    key = myredis.gen_keyname(__file__, getData)
    #myredis.delkey(key)
    return myredis.createRedisVal(key, getLocal).get()
    
def test():
    df = getData()
    
    env = ATgymEnv(df)
    for i in randn(100):
        env.reset()
        while True:
            env.render()
            time.sleep(.1)
            action = 1
            observation, reward, done, info = env.step(action)
            if done:
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
