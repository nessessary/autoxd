#coding:utf8

"""配置环境"""
import os
from autoxd import myredis

class enum:
    ROOT_PATH = 'root_path'

def registe_root_path(dir):
    """在入口函数处调用"""
    key = enum.ROOT_PATH
    o = dir
    myredis.set_obj(key, o)
    
def get_root_path():
    """因为多个地方在引用, 只能配置成绝对目录
    return: str path
    """
    key = enum.ROOT_PATH
    root_path = myredis.get_obj(key)
    assert(os.path.isdir(root_path))
    return root_path