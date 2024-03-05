import os
import random
import json
import gym
from gym import spaces
import pandas as pd
import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EveryNTimesteps
import datetime as dt
from autoxd import stock, agl
from autoxd.pinyin import stock_pinyin3 as jx

MAX_ACCOUNT_BALANCE = 2147483647
MAX_NUM_SHARES = 2147483647
MAX_SHARE_PRICE = 5000
MAX_OPEN_POSITIONS = 5
MAX_STEPS = 20000

INITIAL_ACCOUNT_BALANCE = 10000


class StockTradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, df):
        super(StockTradingEnv, self).__init__()

        self.df = df

        self.reward_range = (0, MAX_ACCOUNT_BALANCE)

        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Box(
            low=np.array([0, 0]), high=np.array([3, 1]), dtype=np.float16)
        
        obs_shape = self.reset().shape
        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
            low=0, high=1, shape=obs_shape, dtype=np.float16)

    def _next_observation(self):
        # Get the stock data points for the last 5 days and scale to between 0-1
        frame = np.array([
            self.df.loc[self.current_step: self.current_step +
                        5, 'Open'].values / MAX_SHARE_PRICE,
            self.df.loc[self.current_step: self.current_step +
                        5, 'High'].values / MAX_SHARE_PRICE,
            self.df.loc[self.current_step: self.current_step +
                        5, 'Low'].values / MAX_SHARE_PRICE,
            self.df.loc[self.current_step:self.current_step+5, 'ma60'].values / MAX_SHARE_PRICE, 
            self.df.loc[self.current_step:self.current_step+5, 'ma5'].values / MAX_SHARE_PRICE, 
            self.df.loc[self.current_step: self.current_step+5, 'Close'].values / MAX_SHARE_PRICE,
            self.df.loc[self.current_step: self.current_step+5, 'Volume'].values / MAX_NUM_SHARES,
        ])
        #print(frame, self.current_step)
        #assert frame.shape == (4, 6)

        # Append additional data and scale each value to between 0-1
        obs = np.append(frame, [[
            self.balance / MAX_ACCOUNT_BALANCE,
            self.max_net_worth / MAX_ACCOUNT_BALANCE,
            self.shares_held / MAX_NUM_SHARES,
            self.cost_basis / MAX_SHARE_PRICE,
            self.total_shares_sold / MAX_NUM_SHARES,
            self.total_sales_value / (MAX_NUM_SHARES * MAX_SHARE_PRICE),
        ]], axis=0)

        return obs

    def _take_action(self, action):
        # Set the current price to a random price within the time step
        current_price = random.uniform(
            self.df.loc[self.current_step, "Open"], self.df.loc[self.current_step, "Close"])

        action_type = action[0]
        amount = action[1]

        if action_type < 1:
            # Buy amount % of balance in shares
            total_possible = int(self.balance / current_price)
            shares_bought = int(total_possible * amount)
            prev_cost = self.cost_basis * self.shares_held
            additional_cost = shares_bought * current_price

            self.balance -= additional_cost
            self.cost_basis = (
                prev_cost + additional_cost) / (self.shares_held + shares_bought)
            self.shares_held += shares_bought

        elif action_type < 2:
            # Sell amount % of shares held
            shares_sold = int(self.shares_held * amount)
            self.balance += shares_sold * current_price
            self.shares_held -= shares_sold
            self.total_shares_sold += shares_sold
            self.total_sales_value += shares_sold * current_price

        self.net_worth = self.balance + self.shares_held * current_price

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        if self.shares_held == 0:
            self.cost_basis = 0

    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)

        self.current_step += 1

        if self.current_step >= len(self.df) - 5:
            self.current_step = 0 

        delay_modifier = (self.current_step / MAX_STEPS)

        reward = self.balance * delay_modifier
        done = self.net_worth <= 0
        #if not done:
            #done = self.current_step >= len(self.df) - 6
        
        obs = self._next_observation()

        return obs, reward, done, {}

    def reset(self):
        # Reset the state of the environment to an initial state
        self.balance = INITIAL_ACCOUNT_BALANCE  #余额
        self.net_worth = INITIAL_ACCOUNT_BALANCE    #净值( 总值)
        self.max_net_worth = INITIAL_ACCOUNT_BALANCE    #最大净值
        self.shares_held = 0    #持有股份
        self.cost_basis = 0     #持股平均成本
        self.total_shares_sold = 0
        self.total_sales_value = 0

        # Set the current step to a random point within the data frame
        self.current_step = 0
        self.current_step = random.randint(
                    0, len(self.df.loc[:, 'Open'].values) - 6)        

        return self._next_observation()

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        profit = self.net_worth - INITIAL_ACCOUNT_BALANCE   #盈利
        
        if self.current_step != 3168:
            return

        print(f'Step: {self.current_step}')
        print(f'Balance: {self.balance}')
        print(
            f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})')
        print(
            f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})')
        print(
            f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})')
        print(f'Profit: {profit}')


def test():
    #df = pd.read_csv('./data/AAPL.csv')
    #df = df.sort_values('Date')
    
    df = stock.getHisdatDf(code=jx.THS同花顺, method='mysql')
    df.columns = ['High', 'Low','Open', 'Close', 'Volume']
    df['Date'] = df.index
    
    # calc ma
    df['ma5'] = stock.MA(df['Close'])
    df['ma60'] = stock.MA(df['Close'], 60)
    df = df[60:]
    df.index = range(len(df))   #  step id == index id
    print(len(df))
    
    # The algorithms require a vectorized environment to run
    env = DummyVecEnv([lambda: StockTradingEnv(df)])
    
    #model = PPO2(MlpPolicy, env, verbose=1)
    model = PPO("MlpPolicy", env, verbose=1)
    # 创建一个CheckpointCallback，用于保存最优模型
    checkpoint_callback = CheckpointCallback(save_freq=1000, save_path='./logs/')    
    best_model_path = os.path.join(checkpoint_callback.save_path, 'best_model')
    if not os.path.exists(best_model_path):
        model.learn(total_timesteps=20000*10, callback=checkpoint_callback, tb_log_name="ppo_stocktrade")
        #model.learn(total_timesteps=20000)
        model.save(best_model_path)
    if os.path.exists(best_model_path):
        model = PPO.load(best_model_path, env=env)
    
    obs = env.reset()
    for i in range(20000):
        action, _states = model.predict(obs)
        obs, rewards, done, info = env.step(action)
        
        env.render()

    #for i in range(10):
        #while True:
            #action, _states = model.predict(obs)
            ##print(obs, action)
            #obs, rewards, dones, info = env.step(action)
            #if dones:
                #env.render()
                #break
    
    #output = env.get_output(visualize=True)
    #output.to_csv(f'{env.title}_输出结果.csv', header=True, encoding='utf-8')

if __name__ == "__main__":
    test()