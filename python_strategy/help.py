#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

import os
import time
import datetime
import sys
import shutil
import subprocess


def info(object, spacing=10,collapse=1):
    """打印方法和DOC字符串             把 模块,类,列表,字典 或者 字符串."""
    methodList = [method for method in dir(object) if callable(getattr(object, method))]     
    processFunc = collapse and (lambda s : " ".join(s.split())) or (lambda s: s)     
    print("\n".join(["%s %s" % (method.ljust(spacing), processFunc(str(getattr(object, method).__doc__))) for method in methodList]))

def prn_obj(obj):
    print (', '.join(['%s:%s' % item for item in obj.__getitem__.items()]))


#
def shell_env():
    import os
    os.chdir("C:\\chromium\\src\\autoxd3\\python")     
#
def getPythonPath():
    return os.getenv('AUTOXD_PYTHON')
#----------------------------------------------------------------------
def getMartixRow(a, row):
    """
    获取一个二维数组的一个整列
    """
    return a[:][:,row]

#
#----------------------------------------------------------------------
def Norm(high,low, v):
    """"""
    # high-low : v = 100 : x
    return v*100/(high-low)


#----------------------------------------------------------------------
def sign(a):
    """"""
    if a>0:
        return 1
    if a<0:
        return -1
    return 0


#----------------------------------------------------------------------
#def OutputString(s):
        #""""""
        #p = wave.Wavelet_Filter()
        #p.OutputString(s)

#----------------------------------------------------------------------
def myprint(a1, a2='', a3='', a4='', a5='', a6='', a7=''):
    """"""
    global g_s
    global g_w
    vals = [a1, a2, a3, a4, a5, a6, a7]
    s = '['
    for val in vals:
        if val != '':
            if hasattr(val, "myprint"):
                val.myprint()
                continue
            if isinstance(val, str):
                val = val.decode('utf-8')
            if isinstance(val, unicode):
                val = val.encode('gb2312')
                #val = val.decode("utf-8")
            if isinstance(val, float):
                val = round(val, 4)
            s += str(val)
            s += " "
    s += ']'
    print( s)
    #g_s += s
    #g_s += "\n"
    #g_w.WriteMemFile(s)
    #f = open('e:\\apache\\apache\\htdocs\\stock\\data.txt', 'a')
    #f.write(s)
    #f.write("\n")     
def convert(val):
    if isinstance(val, str):
        #val = val.decode('utf-8')
        val = val.decode('gbk')
    elif isinstance(val, unicode):
        try:
            val = val.encode('gb2312')
        except:
            val = val.encode('gbk')
    return val     
#得到当前目录的上一级目录
def GetParentDir(path):
    return os.path.abspath(os.path.join(path, os.path.pardir))
def CreateDir(path):
    if not os.path.isdir(path):
        os.mkdir(path)
def FileExist(path):
    return os.path.isfile(path)
def FileDelete(path):
    if FileExist(path):
        os.remove(path)
def print2(a1, a2='', a3='', a4='', a5='', a6='', a7=''):
    """"""
    global g_s
    global g_w
    vals = [a1, a2, a3, a4, a5, a6, a7]
    s = '['
    for val in vals:
        if val != '':
            if hasattr(val, "myprint"):
                val.myprint()
                continue
            if isinstance(val, str):
                val = val.decode('utf-8')
            if isinstance(val, unicode):
                val = val.encode('gb2312')
                #val = val.decode("utf-8")
            if isinstance(val, float):
                val = round(val, 4)
            s += str(val)
            s += " "
    s += ']'
    print(s)
#
#----------------------------------------------------------------------


#
#浮点等于
def float_EQ(price1, price2):
    """"""
    return price1 < price2+0.01 and price1 > price2-0.01


#
#勾股定理
#----------------------------------------------------------------------
def calcPTLength(x, y):
    """"""
    return (x**2 + y**2)**0.5

#
########################################################################
class MyDate:
    """一个简单的日期计算类"""
    d = ''

    #----------------------------------------------------------------------
    def __init__(self, date):
        """Constructor"""
        if isinstance(date, str):
            self.d = StrToDate(date)
        else:
            assert(isinstance(date, datetime.date))
            self.d =  date
    #    
    #----------------------------------------------------------------------
    def Add(self, daynum):
        """daynum 加减的天数"""
        if daynum > 0:
            self.d += datetime.timedelta(days = daynum)
        else:
            self.d = self.d - datetime.timedelta(days = abs(daynum))
        return self.d

    #
    def GetDate(self):
        """ return : datetime"""
        return self.d
    #----------------------------------------------------------------------
    def Next(self):
        """下一天"""
        return self.Add(1)
    #
    #----------------------------------------------------------------------
    def ToStr(self):
        """转换为字符串"""

        s = str(self.d.year) + "-" + str(self.d.month) + "-" + str(self.d.day)
        return s
    #----------------------------------------------------------------------
    def echo(self):
        """"""
        s = self.ToStr()
        return s
        #return self.d.strftime("%Y-%m-%d")
    @staticmethod
    def s_Dec(day, daynum):
        """直接对日期做加减法 
        day : str
        return: str date"""
        d = MyDate(day)
        d.Add(daynum)
        return d.ToStr()

#----------------------------------------------------------------------
def StrToDate(date):
    """2013-4-24 => datetime"""
    if date == '':
        date = str(datetime.date.today())
    date = date.split("-")

    return datetime.date(int(date[0]), int(date[1]), int(date[2]))
def getPercentString(percent):
    if percent == None:
        return ""
    if percent == "":
        return ""
    return ("%.2f"%(percent*100)) + "%"
def p(p):
    return ("%.2f"%(float(p)))
#
#找到数组最大值下标
#----------------------------------------------------------------------
def FindArrayMaxPos(a):
    """"""
    m = 0
    max_pos = 0
    for i in range(0, len(a)):
        if a[i] > m :
            m = a[i]
            max_pos = i

    return max_pos


#
#日期转整数
#----------------------------------------------------------------------
def DateToInt(date):
    """"""

    if isinstance(date, str):
        date.replace("-", "")
    else:
        if 0:date = datetime.date
        date = date.year*10000 + date.month*100 + date.day
        date = int(date)
    return date


#数组唯一
#----------------------------------------------------------------------
def array_unique(a):
    """"""

    i = 0
    while(i<len(a)) :
        cur = a[i]
        i += 1
        j = i
        while(j<len(a)):
            if cur == a[j]:
                del a[j]
                #print a
            j += 1


#
def array_find(a, v):
    """
    find a value at array
    a : [array] one dim
    v : value of array
    return : Ture or False
    """

    for x in a:
        if x == v:
            return True
    return False

#
#----------------------------------------------------------------------
def array_last(a):
    """"""
    return a[len(a)-1]

#
#----------------------------------------------------------------------
def DataToMatlabCsv(a):
    """把数据写入csv文件"""
    all_the_text = ""
    for s in a:
        all_the_text += str(s)
        all_the_text += ","
    file_object = open('c:\\matlab_source\\stock.txt', 'w')
    file_object.write(all_the_text)
    file_object.close( )     
    myprint("数据个数", len(a))

#----------------------------------------------------------------------
def SpliteDate(s, e, n):
    """
    把一个时间段平均分成几分
    @s 开始时间
    @e 结束时间
    @n 分成几份
    return : 分割后的时间字符串
    """

    #计算总天数
    d1 = StrToDate(s)
    d2 = StrToDate(e)
    d = d2 - d1
    day = d / n

    res = []
    d1 = MyDate(s)
    res.append(d1.echo())
    for i in range(0, n):
        d1.Add(day.days+1)
        res.append(d1.echo())
    return res



#----------------------------------------------------------------------
def ClearDir(path):
    """删除目录中的文件"""
    for root, dirs, files in os.walk( path ):
        for f in files:
            f = path + f
            os.remove(f)

#
#----------------------------------------------------------------------
def ClearPath(path):
    """删除目录, 需要先把目录的只读属性取消"""
    for root, dirs, files in os.walk( path ):
        for f in dirs:
            print(f)
            if str(f).find(".svn") >= 0:
                f = root + "\\" + f +"\\"
                shutil.rmtree(f)


########################################################################
class StatReport:
    """通过遍历info来统计回测结果"""

    lose_num = 0     
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""

    #----------------------------------------------------------------------
    def ReadLine(self, line):
        """"""
        v = str(line).split(" ")
        return float(v[2])

    #----------------------------------------------------------------------
    def ReadFileLastLin(self, fname):
        """"""
        f = open(fname)
        lastline = ""
        for line in f.readlines():
            lastline = line
        v = self.ReadLine(lastline)
        #print v
        if v < 50000.0:
            self.lose_num += 1
        f.close()

    #----------------------------------------------------------------------
    def Travl(self, path):
        """"""
        total_num = 0
        for root, dirs, files in os.walk( path ):
            for f in files:
                f = path + f
                self.ReadFileLastLin(f)
                total_num += 1

        return [self.lose_num, total_num]


#
def MoveRadixPoint(h, l, n, k):
    i = 0
    if h-l > n*k:
        while ( h-l > n*k):
            h = h / 10.0
            l /= 10.0
            i += 1
    else:
        while h-l < n:
            h *= 10.0
            l *= 10.0
            i -= 1
    return [h,l,i]
#
#----------------------------------------------------------------------
def MutiS(n):
    """"""
    val = 1
    while n >0:
        n -= 1
        val *= 10
    while n <0:
        n += 1
        val /= 10.0
    return val
#
#----------------------------------------------------------------------
def DecS(n):
    """"""
    i = 0
    while n >1 :
        n /= 10
        i += 1
    if(i>0):
        i -= 1
    return i

#----------------------------------------------------------------------
def AnalyzeNavtiveInt(high, low, grid):
    """"""
    max_grid = 6
    #dec_num = DecS(high-low)

    grids = [grid]


    result = []
    for g in grids:
        high1, low1, move_num = MoveRadixPoint(high, low, g, max_grid)
        if move_num == 0:
            for i in range(low1/g+1, high1/g+1):
                result.append( i*g*MutiS(move_num))
            return result


    for g in grids:
        high1, low1, move_num = MoveRadixPoint(high, low, g, max_grid)
        grid_num = (high1 - low1) / g
        if grid_num<= max_grid :
            #print grid_num
            for i in range(low1/g+1, high1/g+1):
                result.append( i*g*MutiS(move_num))
            return result
    return result
#
#----------------------------------------------------------------------
def findMaxAnalyzeNavtiveInt(high, low):
    """"""
    print(high, low)
    grids = [5, 10, 20,30]
    results = []
    size_len = 0
    index = 0
    for i in range(0, len(grids)):
        c = AnalyzeNavtiveInt(high, low, grids[i])
        if len(c) > size_len:
            size_len = len(c)
            index = i
        results.append(c)

    print(results[index])
#
#----------------------------------------------------------------------
def ExecMatlabFunction(fn_name):
    """
    执行matlab函数
    fn_name : 函数名称
    """

    t = time.time()
    #if os.path.isfile(os.getcwd() + '\\1.txt'):
            #os.remove(os.getcwd() + '\\1.txt')
    #用文件
    f_name = os.getcwd()+'\\1.txt'
    cur_cmd = 'C:\\Program Files (x86)\\MATLAB\\R2013a\\bin\\matlab.exe'
    cur_cmd += " "
    cur_cmd += '-nodesktop -nosplash -nodisplay -r "'
    cur_cmd += fn_name
    cur_cmd += '" -logfile 1.txt'
    p = subprocess.Popen(cur_cmd, \
                         stdin = subprocess.PIPE,\
                         stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)


    p.wait()

    time.sleep(1)
    b = False
    while(1):
        if os.path.isfile(f_name):
            f = open(f_name,'r')
            for line in f.xreadlines():
                print(line)
                if line == '----\n':
                    b=True
                    break

            f.close()
            if b is True:
                break
        time.sleep(1)
    print2("耗时", str(time.time()-t))

def main(args):
    #ExecMatlabFunction('test([1,2])')
    print2(u'\u7cfb\u7edf\u627e\u4e0d\u5230\u6307\u5b9a\u7684\u9a71\u52a8\u5668\u3002\r\n')

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)     