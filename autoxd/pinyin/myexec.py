#-*- coding:utf-8 -*-

def myexec(s):
    ##py3
    _locals = locals()
    r = exec(s, globals(), _locals)
    r = _locals['r']
    return r
    ##py2
    #exec(s)    