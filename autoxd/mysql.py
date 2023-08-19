#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# mail: nessessary@qq.com

#to define key is F4
from __future__ import print_function
import MySQLdb, struct
import pandas.io.sql as pdsql
import pandas as pd
import numpy as np
########################################################################

"""在host中配置mydata.com 对应mysql服务器ip"""

class StockMysql:
    """Stock mysql handle"""

    conn = ''
    if 0: cursor = MySQLdb.cursors.Cursor()
    cursor = ''

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.conn = MySQLdb.connect(host='localhost', user='root', passwd='gochina', db='stock', charset='gb2312')
        self.cursor = self.conn.cursor();	

    def getGupiao(self):
        #self.cursor.execute("select * from gupiao where substring(stock_code,1,1)!='3'")
        self.cursor.execute("select DISTINCT stock_code from kline")
        gupiao = []
        for row in self.cursor.fetchall():
            #print row[0], row[1], row[2]
            gupiao.append(row[0])
        #gupiao.append(u'999999')
        #gupiao.append(u'399001')
        return gupiao
    def getGuPiaoList(self):
        sql = "select * from gupiao "
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def getOneGupiao(self, id):
        """return [id, gupiao]"""
        self.cursor.execute("select * from gupiao where substring(stock_code,1,1)!='3' and id>"+str(id)+" limit 1")
        gupiao = []
        id = 0
        for row in self.cursor.fetchall():
            #print row[0], row[1], row[2]
            id = row[0]
            gupiao.append(row[1])
        return [id, gupiao[0]]

    #
    # 获取股票详细信息
    #----------------------------------------------------------------------
    def getGupiaoInfo(self, code):
        """"""
        sql = "select * from gupiao where stock_code='"+code+"'"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def getKline(self, code, start_day='', end_day=''):
        sql = "select * from kline where stock_code='"+code+"'"
        if start_day !='' :
            sql += " and kline_time>='" + start_day + "'"
        if end_day !='' :
            sql += " and kline_time<='" + end_day + "'"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def getKline30(self, code, start_day='', end_day=''):
        sql = "select * from kline30 where stock_code='"+code+"'"
        if start_day !='' :
            sql += " and kline_time>='" + start_day + "'"
        if end_day !='' :
            end_day = help.MyDate(end_day).Add(1)
            end_day = str(end_day)
            sql += " and kline_time<='" + end_day + "'"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def getCurrentPrice(self, code):
        sql = "select * from kline where stock_code='"+code+"' order by kline_time desc limit 1"
        row = self.cursor.execute(sql)
        if row> 0:
            return self.cursor.fetchone()[6]
        return 20
    def __del__(self):
        self.cursor.close();
        self.conn.close();


    #
    #从复权表获取k线
    #----------------------------------------------------------------------
    def getFuQuanKline(self, code, start_day='', end_day=''):
        """"""
        sql = "select * from kline_fuquan where stock_code='"+code+"'"
        if start_day !='' :
            sql += " and kline_time>='" + start_day + "'"
        if end_day !='' :
            sql += " and kline_time<='" + end_day + "'"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    #
    #----------------------------------------------------------------------
    def getFenshi(self, code, date):
        """"""
        sql = "select fenshi_data as a , fenshi_day as b from fenshi where stock_code='"+code+"' and fenshi_day='"+date+"' limit 1"
        self.cursor.execute(sql)
        #print self.cursor.fetchall()
        result = []
        n = 15
        for blob , day in self.cursor.fetchall():
            #	    $format = 'ltime/lprice/lorder/Sd/CbSell';
            for i in range(0, len(blob)/15):
                result.append(struct.unpack("=iiihb", blob[n*i:n*(i+1)]))
            #print day, blob
        return result


    def ExecSql(self, sql):
        """新建一个表"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def DelKlineCode(self, code):
        sql = "delete from kline where stock_code='"+code+"';"
        self.cursor.execute(sql)

import sys

def DeleteSomeCodes():
    """删除指数日线"""
    db = StockMysql()
    sql = "SELECT DISTINCT stock_code FROM kline WHERE SUBSTRING(kline.stock_code,1,2)='88'";
    codes = db.ExecSql(sql)
    for code in codes:
        db.DelKlineCode(code[0])
    db.ExecSql('commit')
def DeleteFenshi(day='2011-1-1'):
    """删除分时表里的早期数据"""
    import h5py
    db = StockMysql()
    sql = "SELECT DISTINCT stock_code FROM fenshi";
    codes = db.ExecSql(sql)
    for code in codes:
        code = code[0]
        print(code)
        sql = "delete from fenshi where fenshi_day<'"+day+"' and stock_code='"+code+"';"
        db.ExecSql(sql)
        db.ExecSql('commit')

def getHisdat(code, start_day='', end_day=''):
    """return: pandas.DateFrame"""
    con = MySQLdb.connect(host='localhost', user='root', passwd='gochina', db='stock', charset='gb2312')
    sql = "select * from kline where stock_code='"+code+"'"
    if start_day !='' :
        sql += " and kline_time>='" + start_day + "'"
    if end_day !='' :
        sql += " and kline_time<='" + end_day + "'"
    d = pdsql.read_sql(sql, con)
    d = np.array(d)
    return pd.DataFrame(d[:,3:-1], index=pd.DatetimeIndex(d[:,2]), dtype=float, columns=list('ohlcv'))

def putHisdat(df):
    tbl_name = 'kline'
    df.to_sql(con=createStockDb().conn, name=tbl_name,if_exists='append', flavor='mysql')
def putHisdatRow(code, date, o,h,l,c,v):
    db = createStockDb()
    sql = "insert into kline (stock_code,kline_time,kline_open,kline_high,kline_low,kline_close,kline_volume) VALUES('%s','%s',%.2f,%.2f,%.2f,%.2f,%f)"%\
            (code, date, o, h, l, c, v)
    db.ExecSql(sql)
    db.ExecSql('commit')
def putFundRow(row):
    cols = 'code,code_name,report_date,ranking,stock_symbol,stock_name,ratio,stock_num,market_value'
    rows = []
    for col in cols.split(','):
        rows.append(row[col])
    db = createStockDb()
    sql = "insert into fund (%s) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s')"%\
            tuple([cols]+rows)
    db.ExecSql(sql)
    db.ExecSql('commit')
def getFund():
    """return: df"""
    con = MySQLdb.connect(host='localhost', user='root', passwd='gochina', db='stock', charset='gb2312')
    sql = "select * from fund"
    return pdsql.read_sql(sql, con)

def getFiveHisdat(code, start_day='', end_day=''):
    """return: pandas.DateFrame"""
    con = MySQLdb.connect(host='localhost', user='root', passwd='gochina', db='stock', charset='gb2312')
    sql = "select * from kline5min where stock_code='"+code+"'"
    if start_day !='' :
        sql += " and kline_time>='" + start_day + "'"
    if end_day !='' :
        sql += " and kline_time<=date_add('" + end_day + "', interval 1 day)"
    d = pdsql.read_sql(sql, con)
    d = np.array(d)
    return pd.DataFrame(d[:,3:], index=pd.DatetimeIndex(d[:,2]), dtype=float, columns=list('ohlcv'))

def putFiveHisdat(df):
    tbl_name = 'kline5min'
    df.to_sql(con=createStockDb().conn, name=tbl_name,if_exists='append', flavor='mysql')
def putFiveHisdatRow(code, date, o,h,l,c,v):
    db = createStockDb()
    sql = "insert into kline5min (stock_code,kline_time,kline_open,kline_high,kline_low,kline_close,kline_volume) VALUES('%s','%s',%.2f,%.2f,%.2f,%.2f,%f)"%\
            (code, date, o, h, l, c, v)
    db.ExecSql(sql)
    db.ExecSql('commit')
    
db = 0
def createStockDb():
    global db
    if db == 0:
        db = StockMysql()
    return db
def get_codes():
    return createStockDb().getGupiao()

class myException(Exception):
    def __init__(self, errorcode, info):
        self.errorcode = errorcode
        self.info = info
        
class TblYc(object):
    """预测表"""
    def __init__(self):
        self.db = createStockDb()
        
    def insert(self, corp, name,code,adjust, jll,yc_year: int,report_date):
        try:
            
            sql = "insert into yc(corp, name,code,adjust,jll,yc_year,report_date) values('%s','%s','%s','%s','%s',%d,'%s');" %\
                (corp, name,code,adjust, jll,yc_year,report_date)
            self.db.ExecSql(sql)
            self.db.ExecSql('commit')
        except MySQLdb.IntegrityError as e:
            # unique conflict
            pass
                
        return True
        
    def get(self, code, year):
        sql = "select * from yc where yc.code=%s and yc.yc_year >= %s" % (code, year)
        return pdsql.read_sql(sql, self.db.conn)
        
class Tc:
    """保存实盘交易信息"""
    class enum:
        zhijin = 'tc_zhijin'
        chenjiao = 'tc_chenjiao'
    def __init__(self):
        self.db = createStockDb().conn
    def getZhiJinCols(self):
        """mysql 表的col return: list"""
        return ['yu_e','ke_yong','shi_zhi','zhi_can']
    def getChenJiaoCols(self):
        """return: list"""
        return ['stock_code','is_sell','num','price','money','trade_id']
    def save(self, df, tbl_name):
        df.to_sql(con=self.db, name=tbl_name,if_exists='append', flavor='mysql')
    def load(self, tbl_name):
        sql = 'select * from %s'%(tbl_name)
        return pdsql.read_sql(sql, self.db)
def main(args):
    #DeleteFenshi()
    print("end")

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)