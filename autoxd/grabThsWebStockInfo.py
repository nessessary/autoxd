#-*- coding:utf-8 -*-
from __future__ import print_function
import sys
if sys.version > '3':
    from bs4 import BeautifulSoup
    import stock_pinyin3 as jx
    from urllib import request
else:
    from BeautifulSoup import BeautifulSoup
    import stock_pinyin as jx
    import urllib2 as request
import pandas as pd    
import numpy as np
import re
    
def HtmlTableToDf(table_tag):
    if sys.version > '3':
        return _HtmlTableToDf3(table_tag)
    return _HtmlTableToDf2(table_tag)

def _HtmlTableToDf3(table_tag):
    """把table标签解析为一个df, 根据tr个数来自动分析row和col
    table_tag: BeautifulSoup解析的table, 也可以是包含有table的div等
    return: df 表格里的内容"""
    if 0: table_tag = BeautifulSoup.Tag
    trs = table_tag.findAll('tr')
    row = len(trs)
    tds =  table_tag.findAll(['th', 'td'])
    td_contents = []
    c =	len(tds)	#col_num
    col = int(c / row)

    for td in tds:
        td_contents.append(filter_htmlstr(td.getText()) )

    ths = np.array(td_contents)
    ths = ths.reshape(row, col)
    return pd.DataFrame(ths)

    
def _HtmlTableToDf2(table_tag):
    """把table标签解析为一个df, 根据tr个数来自动分析row和col
    table_tag: BeautifulSoup解析的table, 也可以是包含有table的div等
    return: df 表格里的内容"""
    if 0: table_tag = BeautifulSoup.Tag
    trs = table_tag.findAll('tr')
    row = len(trs)
    tds =  table_tag.findAll(['th', 'td'])
    td_contents = []
    c =	len(tds)	#col_num

    #如果有合并的td， 重新计算col
    rowspan_inserts = []
    for i , td in enumerate( tds):
        df = pd.DataFrame(td.attrs)
        if len(df)>0:
            df = df.set_index(0)
            if 'rowspan' in df.index and int(df.ix['rowspan'][1]) >1:
                rows = int(df.ix['rowspan'][1])
                c += rows -1
                rowspan_inserts.append((i, rows, td.getText().encode('utf8')))
    col = c / row
    #过滤掉不符合规则的项
    while c != row*col:
        del tds[0]
        c = len(tds)
        row -=1
        col = c/ row

    for td in tds:
        td_contents.append(filter_htmlstr(td.getText().encode('utf8')) )

    #分解td
    for i,rows, v in rowspan_inserts:
        for j in range(1,rows):
            td_contents.insert(i+col*j, v)

    ths = np.array(td_contents)
    ths = ths.reshape(row, col)
    return pd.DataFrame(ths)

def filter_htmlstr(s):
    """过滤掉常见的html特殊字符"""
    s = s.replace('&nbsp;', '')
    s = s.replace(' ', '')
    s = re.sub('\s', '', s)
    return s

class GrabThsWeb:
    """获取同花顺全部基本面信息F10， 并输出为一个pd.DataFrame"""
    key_fenhong = 'GrabThsWeb.fenhong.'
    key_gubenbiangen = 'GrabThsWeb.gubenbiangen.'
    def __init__(self, code):
        self.code = code
        self.urls = [
            ['股本结构','http://basic.10jqka.com.cn/%s/equity.html', '_equity'],
            ['分红融资','http://basic.10jqka.com.cn/%s/bonus.html','_bonus'],
        ]
    def GetFenHongKey(self):
        key = self.key_fenhong + self.code
        return key
    def GetGubenbiangenKey(self):
        key = self.key_gubenbiangen+ self.code
        return key
    def getFenHong(self):
        """获取分红表
        return: df
        """
        self._Run()
        return self.df_fenhong
    def getGubenbiangen(self):
        """保留其原始状态，在使用时修改
        return: df"""
        self._Run()
        if hasattr(self, "df_gubenbiangen"):
            return self.df_gubenbiangen
        return None
    def _Run(self):
        """执行遍历下载"""
        for k, url, fn in self.urls:
            url = url % (self.code) 
            html = self._downhtml(url)
            if sys.version > '3':
                self.soup = BeautifulSoup(html, "html.parser")
            else:
                self.soup = BeautifulSoup(html)
            eval('self.%s()'%fn)

    def _downhtml(self,url):
        html = ''
        headers = {
            'User-Agent': r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          r'Chrome/45.0.2454.85 Safari/537.36 115Browser/6.0.3',                
        }
        req = request.Request(url, headers=headers)
        html = request.urlopen(req).read()
        html = html.decode('gbk')
        return html
    def _save(self, key, v):
        key = key + self.code
        myredis.set_obj(key, v)
    def _equity(self):
        """股本结构"""
        #历次股本变动
        ids = ['astockchange']
        for id in ids:
            div = self.soup.find('div', {'id':id})
            if div == None:
                self.table_name_index += 1
            else:
                table = div.find('table')
                self.df_gubenbiangen = HtmlTableToDf(table)
    def _bonus(self):
        """分红融资"""
        table = self.soup.find('table', {'class':'m_table m_hl mt15'})
        if table == None:
            self.table_name_index += 1
            return
        df = HtmlTableToDf(table)
        df.columns = df.iloc[0]
        df = df.drop(0)
        df = df[df['董事会日期']!='--']
        df.index = pd.DatetimeIndex(df['董事会日期'])
        self.df_fenhong = df
        
if __name__ == "__main__":
    code = jx.THS
    print(GrabThsWeb(code).getFenHong())
    #print(GrabThsWeb(code).getGubenbiangen())