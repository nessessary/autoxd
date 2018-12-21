#-*- coding:utf-8 -*-

"""把策略使用的部分封装成库"""

from setuptools import setup, find_packages

setup (
    name = 'autoxd',
    version = '0.4.1',
    description="backtest framework",
    author="Kang Wang",
    url="https://github.com/nessessary/autoxd.git",
    license="BSD 3",
    py_modules=['autoxd'],
    packages= find_packages(),

)