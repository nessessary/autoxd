#-*- coding:utf-8 -*-

class GrabThsWeb:
    """获取同花顺全部基本面信息F10， 并输出为一个pd.DataFrame"""
    table_names = ['概要','新闻','解禁','历次股本变动','盈利预测','机构推荐',\
                   '财务主要指标_汇报期','财务主要指标_年','财务主要指标_单季度','分红融资']
def getThsResults(refresh=False):
    """获取全部的同花顺F10数据, 结果集是dict包含几个df
    refresh: 是否重新抓取数据, 否则从cache中读取
    return : dict[df[...]]"""
    from huge_dict import huge_dict

    data = huge_dict().get()
    return data
