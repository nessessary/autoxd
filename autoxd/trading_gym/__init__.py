#coding:utf-8

"""渲染环境 """
from __future__ import print_function
from gym.envs.registration import register
import trading_gym

register(id=trading_gym.id,
         entry_point='autoxd.trading_gym:ATgymEnv',
)

