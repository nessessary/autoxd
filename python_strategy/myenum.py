#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457


#交易监测的股票， basesign里引用
allow_traded_codes = ['300457','300384']
#枚举值

#enum
IID_Simulator = 101             #分时
IID_SimulatorCode = 102         #日线
IID_SimulatorOneStock = 103
IID_SimulatorAllData = 104      #直接从AllData数据文件读入全部的日线

#
one = 0	    #一个
some = 2    #固定的列表
all = 3	    #全部遍历
randn = 11
hang_ye = 12
exclude_dapan = 15  #排除大盘指数

#
class Uptrend:
    its_bogu = 1
    its_bofeng = 0

#描述曲线匹配形态
class Curve:
    GouTou = 1              #勾头
    ChaoDieFanTan = 4       #超跌反弹
    YiBanFanTan = 2         #一般反弹
    BigUptrendFanTan = 8
    W = 16
########################################################################
class Hisdat:
    """"""
    high = "high"
    low = "low"
    close = "close"
    open = "open"
    volume= "volume"
    
        
class CurvePosition:    
    dibuxiadie = 1
    dibushangshen = 2
    zhongbuxiadie = 3
    zhongbushangshen = 4
    dingbuxiadie = 5
    dingbushangshen = 6

class DaPan:
    shanghai = '999999'         #上证
    shengzheng = '399001'       #深成
    zhongxiao = '399005'        #中小板
    chuangyeban = '399006'      #创业板
    etf = '510050'              #50etf
    
class boll_type:
    msg = ['布林下中轨', '布林下下中轨','布林下轨','布林中轨','布林上轨','布林上中轨']
    boll_down = 0
    boll_down_mid = 1
    boll_down_mid2 = 2  #中下轨四分之一
    boll_mid = 3
    boll_up_mid = 4
    boll_up = 5
##########################################################
class FenshiBetaTinPaiException(Exception):
    """分时日期区间与板块日期区间不匹配, 主要是因为个股停牌引起"""
    pass