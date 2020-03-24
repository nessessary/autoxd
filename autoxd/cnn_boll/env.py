#coding:utf8

"""配置环境"""
import os

#use get_root_path

def get_root_path():
    """因为多个地方在引用, 只能配置成绝对目录
    return: str path
    """
    root_path="~/work/autoxd/autoxd/cnn_boll"
    win_root_path = "c:/workc/autoxd/autoxd/cnn_boll"
    if os.path.exists(win_root_path):
        return win_root_path
    return root_path