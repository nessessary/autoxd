#-*- coding:utf-8 -*-

"""把策略使用的部分封装成库"""

from setuptools import setup, find_packages
import sys
import autoxd
if sys.version > '3':
    #myexclude=('*cnn_boll',)
    myexclude = ()
else:
    #setup.py install需要删除build等目录
    #只能过滤掉目录，不能过滤文件
    myexclude = ('*pinyin','*cnn_boll',)

setup (
    name = 'autoxd',
    version = autoxd.__version__,
    description ="backtest framework",
    author = "Kang Wang",
    author_email = "nessessary@qq.com",
    url="https://github.com/nessessary/autoxd.git",
    license = "BSD 3",
    #py_modules=['autoxd'],
    packages= find_packages(exclude=myexclude),
    data_files = [('autoxd/pypublish',['autoxd/pypublish/test.html']),
                  ('autoxd/datas', ['autoxd/datas/tdx_codes.csv', 
                                    'autoxd/datas/tdx_gan_codes.csv', 
                                    'autoxd/datas/fenhong.csv', 
                                    'autoxd/datas/astockchange.csv'])
                  ]
)