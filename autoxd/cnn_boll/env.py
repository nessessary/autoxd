#coding:utf8

"""配置环境"""
import os
from autoxd import myredis,agl

class enum:
    ROOT_PATH = 'root_path'
    use_redis = False
    
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
    if enum.use_redis:
        root_path = myredis.get_obj(key)
    else:
        cur_path = agl.get_exec_file_path()
        key_path = "autoxd\\autoxd"
        pos = cur_path.find(key_path)
        if pos <=0 :
            key_path = "autoxd/autoxd"
            pos = cur_path.find(key_path)
        root_path = cur_path[:pos+len(key_path)]
        #cur_path = os.path.abspath(__file__)
        #cur_path = os.path.dirname(cur_path)
        #root_path = os.path.abspath(os.path.join(cur_path, '..'))
    assert(os.path.isdir(root_path))
    return root_path

if __name__ == "__main__":
    print(get_root_path())