#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

from __future__ import print_function
import os
import numpy as np
import pandas as pd
from autoxd import help,myenum,myredis
import sys,pickle,os,random,shutil, urllib, dateutil, logging, charade, zipfile, re, math,time, datetime,dateutil,gzip
if sys.version > '3':
    import _pickle as cPickle
else:
    import cPickle
from PIL import Image
from sklearn.utils import shuffle
import traceback
import pprint
from sklearn.cluster import KMeans
def getFunctionName():
    """得到当前调用的函数名称"""
    stack = traceback.extract_stack()
    (filename, line, procname, text) = stack[-2]
    return procname    
def getModuleName(f_path):
    """得到模块名称
    f_path : str __file__
    return: str 文件名称
    """
    module_name = os.path.basename(f_path)
    module_name = module_name.replace('.py', '')
    return module_name
def getFunctionDoc():
    pass
def tic():
    """开始计时"""
    globals()['tt'] = time.clock()

def toc():
    """计时结束"""
    sec = time.clock()-globals()['tt']
    minutie = sec/60.0
    hour = minutie / 60.0
    a = datetime.timedelta(seconds = sec)
    print('\nElapsed time: %.2f seconds / %.2f min / %.2f hour     %s\n' % (sec, minutie, hour, str(a)))
class tic_toc:
    """要赋个值"""
    def __init__(self):
        tic()
    def __del__(self):
        toc()

#
def sign(a):
    """"""
    if a>0:
        return 1
    if a<0:
        return -1
    return 0
def CurYear():
    return str(datetime.date.today().year)
def CurDay():
    """return: str 当前天"""
    return str(datetime.date.today())    
if 0: curTime = datetime.datetime
def curTime():
    """return: datetime 当前时间"""
    return datetime.datetime.now()
def getCurTime():
    """return : str"""
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
def getQuarter(t):
    """获取第几季度 t : datetime
    return: float
    """
    return math.ceil(float(t.month)/3)
def is_valid_date(s):
    '''判断是否是一个有效的日期字符串'''
    try:
        time.strptime(s, "%Y-%m-%d")
        return True
    except:
        return False
def DateTimeToDate(dt):
    """只取日期 return: str"""
    assert(isinstance(dt, str))
    if dt.find(' ') > 0:
        return dt.split(' ')[0]
    return dt
def DateTimeCmp(dt1, dt2):
    """dt1,dt2: str
    return: bool"""
    return dateutil.parser.parse(dt1) == dateutil.parser.parse(dt2)
def DateDec(day1, day2):
    """日期相减
    day1, day2: str
    return :  int 日期数
    """
    return (dateutil.parser.parse(day1) - dateutil.parser.parse(day2)).days
def DateYearAdd(d, n):
    """对日期进行年的加减
    d : str date
    n : int 可以是负值
    return: str
    """
    d = dateutil.parser.parse(d)
    return d

#----------------------------------------------------------------------
def max2(a):
    """
    模仿matlab的max
    return : [v, i] 值和下标
    """
    m = -999999999; I=0;
    for i in range(0, len(a)):
        if a[i] > m:
            m=a[i]
            I = i
    return [m, I]

#
#----------------------------------------------------------------------
def min2(a):
    """"""
    m = 999999999; I=0;
    for i in range(0, len(a)):
        if a[i] < m:
            m=a[i]
            I = i
    return [m, I]

#
def array_del_element(ary, dels):
    """删除列表中的一些元素"""
    for i in range(len(dels)-1, -1, -1):
        del ary[dels[i]]
    return ary    
#----------------------------------------------------------------------
def GetSortedArrayIndexs(a, num=-1):
    """a为一维数组， 返回排序后带索引的值
    a : 29,30,19,50 
    num : default is len(a)
    => (3,50),(1,30),(0,29),(2,19)
    降序
    return : 3, 1, 0, 2
    """
    if num == -1:
        num = len(a)
    #普通数组转换为带下标的矩阵
    m = []
    for i in range(len(a)):
        m.append((i, a[i]))
    dtype = [('index', '<i4'), ('y', '<f8')]
    a = np.array(m, dtype=dtype)
    a = np.sort(a, order=['y'])
    b = []
    for i in range(num):
        i = len(a)-i-1
        b.append(a[i][0])
    return b

def array_equal(a1,a2):
    return (a1[np.isnan(a1)==False] == a2[np.isnan(a2)==False]).all()
def array_val_to_pos(a, v):
    """由值取下标 
    agl.array_val_to_pos(np.array([1,2,3]),3)
    =>2
    return: int 数组下标"""
    assert(type(a) == np.ndarray)
    pos = np.where(a == v)
    return pos[0][0]
    
def array_reverse(a):
    """数组倒序"""
    return np.fliplr([a])[0]
def array_random(size):
    """产生随机数组, 默认范围在[-1, 1]"""
    return 2*np.random.random_sample((size,))-1
def array_transpose(a):
    """一维数组转置 [1,2,3]=[1],[2],[3]"""
    if 0: a = np.ndarray
    #行转列
    if len(a.shape)==1:
        a.shape = (a.shape[0], 1)
        a.transpose()
        return a
    else:#列转行
        return a.T
def array_shuffle(ary):
    """搅乱"""
    return shuffle(ary)    
def Unittest_array_transpose():
    a = np.array([1,2,3])
    print(array_transpose(a))
    a = np.array([[1],[2]])
    print (array_transpose(a))
#----------------------------------------------------------------------
def ArrayToStr(a):
    """"""
    s = ""
    for i in range(len(a)):
        s += str(a[i])
        s += " "
    return s

def MatrixToCsv(a,fname):
    s = ""
    for i in range(len(a)):
        for j in range(len(a[i])):
            s += str(a[i][j])
            if j != len(a[i])-1:
                s += ","
        s += "\n"
    f = open(fname , 'w')
    f.write(s)
    f.close()

def MatrixToStr(a):
    """a : 二维数组"""
    s = ""
    for i in range(len(a)):
        for j in range(len(a[i])):
            s += str(a[i][j])
            s += " "
        s += "\n"
    return s

def StrToMatrix(s):
    a = str(s).split("\n")
    a = a[:-1]
    for i,s1 in enumerate(a):
        b = str(s1).split(" ")
        b = b[:-1]
        for j, c in enumerate(b):
            b[j] = float(c)
        a[i] = b
    return np.array(a)



#----------------------------------------------------------------------
#同矩阵连接
def array_insert(a, index, val):
    """插入矩阵, 横向插入, 注意要使用返回值
    a : array [[1,2],[3,4]]
    index : 横向插入的位置 1
    val : row值 [5,6]
    return : [[1,2],[5,6],[3,4]]
    """
    if len(a) > 0:
        assert (index <= len(a))
    else:
        return np.array([val])
        #assert (np.shape(a)[1] == len(val))
    return np.insert(a, index, val, axis=0)

#
#----------------------------------------------------------------------
def array_insert_col(a, index, val):
    """纵向插入矩阵
    a : [[1,2],[3,4]]
    index : 1
    val : [5,6]
    return : 
    [[1 5 2]
    [3 6 4]]
    """
    return np.insert(a, index, val, axis=1)

#----------------------------------------------------------------------
def distance(a,b):
    """欧式距离"""
    x = a[0]-b[0]
    y = a[1]-b[1]
    return (x**2 + y**2)**0.5

#
#----------------------------------------------------------------------
def get_middle_point_y_val(pts, x):
    """
    对给定的线段， 获取中间某点的y值
    pts : [[x1,y1],[x2,y2]]
    x : x3
    return : y3
    """
    #x2-x1 : y2-y1 = x3-x1 : y3-y1
    x1 = pts[0][0]
    x2 = pts[1][0]
    y1 = pts[0][1]
    y2 = pts[1][1]
    x3 = x
    y3 = (y2-y1)*(x3-x1) / (x2-x1) + abs(y1)
    return y3

def calc_vert(start_x, start_y, end_x, end_y):
    """return: x1, y1, x2,y2"""
    angle = math.atan2(end_y - start_y, end_x - start_x) + 3.14159265358979323846;
    arrow_lenght_ = 30.0;
    arrow_degrees_ = 0.15;
    x1 = end_x + arrow_lenght_ * math.cos(angle - arrow_degrees_);
    y1 = end_y + arrow_lenght_ * math.sin(angle - arrow_degrees_);
    x2 = end_x + arrow_lenght_ * math.cos(angle + arrow_degrees_);
    y2 = end_y + arrow_lenght_ * math.sin(angle + arrow_degrees_);    
    return x1, y1, x2,y2
#
#----------------------------------------------------------------------
def swap(a,b):
    """"""
    c = a
    a = b
    b = c
    return a, b

def removeDir(dirPath):
    """删除目录下的所有文件, 但不删除当前目录"""
    if not os.path.isdir(dirPath):
        return
    files = os.listdir(dirPath)
    try:
        for f in files:
            filePath = os.path.join(dirPath, f)
            if os.path.isfile(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                removeDir(filePath)
        #os.rmdir(dirPath)
    except Exception as e:
        print(e)
def archiveZip(filename, dirSrc):
    """打包目录到zip"""
    f = zipfile.ZipFile(filename,'w',zipfile.ZIP_DEFLATED)  
    startdir = dirSrc
    for dirpath, dirnames, filenames in os.walk(startdir):  
        for filename in filenames:  
            f.write(os.path.join(dirpath,filename))  
    f.close()  	    

def Print(a1, a2='', a3='', a4='', a5='', a6='', a7=''):
    vals = [a1, a2, a3, a4, a5, a6, a7]
    s = ''
    for val in vals:
        if val != '':
            if isinstance(val, str):
                val = val.decode('utf-8')
            if isinstance(val, unicode):
                val = val.encode('gb2312')
                #val = val.decode("utf-8")
            if isinstance(val, float):
                val = round(val, 4)
            s += str(val)
            s += " "
    s += ''
    print(s)

def ReadFile(fname):
    """return: str"""
    f = open(fname, 'r')
    s = f.read()
    f.close()
    return s
def WriteFile(fname, content):
    f = open(fname, 'wb')
    f.write(content)
    f.close()
def ConvertFileGbkToUtf8(fname):
    """把文件转换成utf8"""
    s = ReadFile(fname)
    s = s.decode('gbk')
    s = s.encode('utf8')
    WriteFile(fname, s)
def convert(s):
    """return: utf8"""
    if not isinstance(s, unicode):
        return s.decode('utf8')
    return s
def utf8_to_ascii(s):
    """return: str 中文utf转ascii"""
    return s.decode('utf8').encode('gb2312')
def unicode_to_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s
def utf8_to_unicode(s):
    return s.decode('utf8')
def convert_html(html):
    """html下载的文本中含有gb2312的中文编码， 英文是ascii， 如果先行过滤的话，soup转换为unicode后
    find函数发现不了元素， 因此只能后期再过滤
    return: utf8"""
    #html = 'sdfs\xa8\x8bdfasf\xc2\xb3\xb7\xe1\xbb\xb7\xb1\xa3'
    assert(isinstance(html, unicode))
    cur = ''
    html2 = ''
    for i,c in enumerate(html):
        if ord(c)>256:
            return html.encode('utf8')
        c = chr(ord(c))
        if c > chr(128):
            cur = cur+c
        if c<=chr(128) or i+1==len(html):
            if len(cur)>0:
                try:
                    cur = cur.decode('gb2312').encode('utf8')
                except:
                    cur=''
                    continue
                #print cur
                html2 += cur
                cur = ''
            if c <= chr(128):
                html2 += c
    #print html2
    return html2
def ascii_to_utf8(s):
    """对于中文ascii可用该方法转换, return: utf8"""
    return convert_html(s.decode('gbk'))
#
def GenRandomArray(max_val, length):
    """产生一个length长的随机数组， 值小于max_val
    length:数组长度
    return: np.array"""
    return np.random.randint(0, max_val, size=length)
def ArrayToStr(a):
    b = ""
    for c in a:
        if c < 0:
            c = 256+c
        b += chr(c)
    return b
def StrToArray(s, a):
    for i,s1 in enumerate(s):
        a[i] = ord(s1)
    return a
def StrToNumber(s):
    """获取字符串中的数字及小数点
    return: float 
    """
    return float(filter(str.isdigit, s))
def StrToFloat(s):
    """字符串转数值
    s: 包含有数量单位的字符串
    return: float
    """
    s = str(s)
    unit = 1
    if s.find('亿')>0:
        unit = myenum.YI
    if s.find('万')>0:
        unit = myenum.WAN
    s = re.sub('\D','', s)
    if s == '':
        return np.nan
    return float(s)*unit
def FloatToStr(s):
    """保留小数点后两位"""
    return "%.2f"%s
def float_to_2(f):
    return '{:.2f}'.format(f)
#----------------------------------------------------------------------
def GetIntWeiShu(v):
    """获取最大位数"""
    count = 1
    while(v>1):
        v = v/10
        count += 1
    return count
def DateEq(d1,d2):
    """判断两字符串日期是否相等, return : bool"""
    if isinstance(d1, str):
        d1 = dateutil.parser.parse(d1)
    if isinstance(d2, str):
        d2 = dateutil.parser.parse(d2)
    return d1 == d2
def Eq(price1, price2):
    delta = int(price2*0.1)*0.01+0.01
    return abs(price1 - price2) <= delta
class SerialMgr:
    """处理序列化相关事宜,支持df及np"""
    count = 0
    @staticmethod
    def clearAutoFile(file_name, fn_name):
        """删除searialAuto创建的文件
        fn_name: str"""
        fname = os.path.basename(file_name)
        fname = fname.replace('.py', '')
        fname = 'datas/'+fname+'_'+fn_name+'.df'
        help.FileDelete(fname)
    @staticmethod
    def delFile(fn):
        """删除serialAuto上次生成的文件， 好让其重新生成"""
        caller_name = getCallerName()
        fname = 'datas/' + caller_name +'.searial'	
        help.FileDelete(fname)	
        fname = str(fname).replace('.searial','.df')
        help.FileDelete(fname)
    @staticmethod
    def serialAuto(fn, *args, **kwargs):
        """对于大数据, 进行dump到数据目录, 统一序列化和反序列化
        fn: 数据获取的过程, [注意], 这是函数指针，不要带括号, fn返回的值即保存的值
        **kwargs : restart=True 先删除原来的文件， 亦即重新来一遍
        fname='' 指定文件名
        return: 数据, 例如df"""
        #命名方式,v1 调用的函数名+参数+调用次数
        #v2, 调用文件名+函数名
        #fname = 'datas/'+fn.__name__+str(*args)+str(SerialMgr.count)+'.searial'
        #fname = 'datas/'+fn.__name__+str(*args)+'.searial'
        caller_name = getCallerName()
        data_path = os.path.dirname(__file__) + '/datas/'
        fname = data_path + caller_name +'.searial'	
        if 'fname' in list(kwargs.keys()):
            fname = data_path + kwargs[fname]+'.searial' 
        #删除文件
        if 'restart' in list(kwargs.keys()):
            if kwargs['restart'] == True:
                if help.FileExist(fname):
                    help.FileDelete(fname)
                else:
                    fname = str(fname).replace('.searial','.df')
                    if help.FileExist(fname):
                        help.FileDelete(fname)
        #相对目录转绝对目录
        result = SerialMgr.unserial(fname)
        if isinstance(result, list) and len(result)==0:
            SerialMgr.count += 1
            result = fn(*args)
            SerialMgr.serial(result, fname)
        #print '[serial]:',fname
        return result
    @staticmethod
    def unittest():
        def Test1():
            def Test(a,b,c):
                return [a,b,c]
            print(SerialMgr.serialAuto(Test, 1,2,3))
        def Test2():
            def genDf(a):
                return pd.DataFrame(a)
            print(SerialMgr.serialAuto(genDf, [1,3,23,34,5,'中文'], restart=True))
        def Test3():
            import stock
            codes = stock.get_codes()
            #codes = codes[:10]
            print(SerialMgr.serialAuto(stock.Guider.getDf, codes, ('',''), restart=True))
        Test3()
    @staticmethod
    def serial(result, fname = "temp.bin"):
        if isinstance(result, pd.DataFrame) or isinstance(result, pd.Panel):
            fname = str(fname).replace('.searial','.df')
        elif isinstance(result, np.ndarray):
            fname = str(fname).replace('.searial','.csv')

        if charade.detect(fname)['encoding'] == 'utf-8':
            fname = convert(fname)
        if isinstance(result, pd.DataFrame) or isinstance(result, pd.Panel):
            result.to_pickle(fname)
            #result.to_csv(fname)
        elif isinstance(result, np.ndarray):
            np.savetxt(fname, result, delimiter=',', fmt='%.3f')
        else:	
            f = open(fname,"wb")	    
            p = cPickle.Pickler(f)
            p.clear_memo()
            p.fast = True
            p.dump(result)
            f.close()
    @staticmethod
    def unserial(f_name='temp.bin'):
        """return: 之前serial的结果集"""
        a=[]
        if os.path.isfile(f_name):
            f = open(f_name, 'rb')
            a = cPickle.load(f)
            f.close()
        else:
            f_name = str(f_name).replace('.searial','.df')
            if os.path.isfile(f_name):
                a = pd.read_pickle(f_name)	
                #a = pd.read_csv(f_name)
            else:
                f_name = str(f_name).replace('.searial','.csv')
                if os.path.isfile(f_name):
                    a = np.loadtxt(f_name,delimiter=',')
        return a

def unittest_matrixtostring():
    a = np.array([[1,2],[33,44]])
    s = MatrixToStr(a)
    print(s)
    print(StrToMatrix(s))

def PngToBmp(f):
    # convert a .png image file to a .bmp image file using PIL

    file_in = f+".png"
    img = Image.open(file_in)
    file_out = f+".bmp"
    #print len(img.split())  # test
    if len(img.split()) == 4:
        # prevent IOError: cannot write mode RGBA as BMP
        r, g, b, a = img.split()
        img = Image.merge("RGB", (r, g, b))
        img.save(file_out)
    else:
        img.save(file_out)    
def JpgToBmp(f):
    # convert a .png image file to a .bmp image file using PIL

    file_in = f+".jpg"
    img = Image.open(file_in)
    file_out = f+".bmp"
    #print len(img.split())  # test
    if len(img.split()) == 4:
        # prevent IOError: cannot write mode RGBA as BMP
        r, g, b, a = img.split()
        img = Image.merge("RGB", (r, g, b))
        img.save(file_out)
    else:
        img.save(file_out)            
def SmallImg(f, s):
    """缩小图片 f: 文件路径 s:缩小的比率, 2就是缩小一倍
    """
    img = Image.open(f)
    w,h = img.size[:2]
    out = img.resize((w/s,h/s))
    out.save(f)

def PngToTxt(f):
    """把图像按文本方式输出, f:文件名称 return : 字符串"""
    Palette={'000':'#'#榛�
             ,'010':'@'#鏆楃豢
             ,'020':'/'#缁�
             ,'001':'$'#娣辫摑
             ,'011':'<'#闈�
             ,'021':'"'#浜�豢鑹�
             ,'002':'='#钃�
             ,'012':'\\'#闂�摑鑹�
             ,'022':'_'#娴呯豢
             ,'100':'>'#鏆楃孩
             ,'110':'*'#鏆楅粍
             ,'120':'~'#榛勭豢鑹�
             ,'101':'%'#鏆楃传
             ,'111':'+'#鐏�
             ,'121':'^'#娴呯豢鑹�
             ,'102':'|'#绱�綏鍏�
             ,'112':'!'
             ,'122':'-'
             ,'200':'&'#绾�
             ,'210':';'#姗欒壊
             ,'220':"'"#榛�
             ,'201':')'#娣辩矇鑹�
             ,'211':'.'#绮夌孩鑹�
             ,'221':'`'
             ,'202':']'#绱�
             ,'212':','
             ,'222':' '#鐧�
             }    
    img = Image.open(f)
    if 0: img = Image.Image
    #缩小, 结果比较模糊, 还是用原比例较好
    img = img.resize((60,20))
    w,h = img.size[:2]
    #print w,h
    result = []
    for i in range(h):
        result1 = []
        is_empty_line = True
        for j in range(w):
            pixel = img.getpixel((j,i))[:3]
            #result1.append(Palette[''.join([str(int(x//85.3)) for x in pixel])])
            if pixel==(255,255,255):
                s = '222'
            else:
                s = '110'
                is_empty_line = False
            result1.append(Palette[s])
        #去除空行
        if is_empty_line == False:
            result.append(result1)
    r="\n".join(["".join(x) for x in result])
    return r
    #object_file=os.path.splitext(f)[0]+".txt"
    #open(object_file,'w').write(r)    
def UrlDecode(s):
    return urllib.unquote(s)
def genPwd(num=128):
    s = ''
    key = 'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(num):
        #s += random.choice('abcdefghijklmnopqrstuvwxyz!@#$%^&*()1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        s += random.choice(key)
    print(s)
def genStrMem(n=100):
    s = ''
    for i in xrange(n):
        s += " "
    return s
#----------------------------------------------------------------------
def Unittest():
    """"""
    print(GetIntWeiShu(103294))

def unittest_pickle():
    class t:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    m = t(10,20)
    print(str(pickle.dumps(m)))

def count_char():
    s = "\
//014e0768  0a 00                                            ..\
    "
    count = 0
    for c in s:
        if c=='|':
            count += 1
    print(count)

def PostTask(fn, t, reset=False):
    """每隔t秒执行一次fn
    主要是防止交易接口被短期内多次调用， 造成系统异常
    fn : callback function
    t : 秒
    reset: 重置时间, 立刻执行
    """
    key = 'posttask_'+fn.func_name
    cur_t = curTime()
    if reset:
        myredis.delkey(key)
    pre_t = myredis.get_obj(key)
    if pre_t == None:
        pre_t = cur_t - datetime.timedelta(seconds=t+1)

    if cur_t - pre_t > datetime.timedelta(seconds=t):
        fn()
        myredis.set_obj(key, cur_t)
class TimeDelta:
    @staticmethod
    def FromMinutes(minutes):
        """return: seconds"""
        return minutes*60
    @staticmethod
    def FromHours(hour):
        return hour*60*60
def MoveFile(src, dst):
    shutil.move(src, dst)
def TestMoveFile():
    src = "c:/users/wangkang/appdata/local/liebao/4.7.54.8107/upgrade.dll"
    #src = "c:/windows/upgrade.dll"
    dst = "C:/ProgramData/HiveSoft/AntiFiles/a.dll"
    MoveFile(src, dst)


#日志， 既要把日志输出到控制台， 还要写入日志文件   
_log = None
class Logger():
    def __init__(self, logname, loglevel, logger):
        '''
           指定保存日志的文件路径，日志级别，以及调用文件
           将日志存入到指定的文件中
        '''
        # 创建一个logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.DEBUG)

        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(logname)
        fh.setLevel(logging.DEBUG)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #formatter = format_dict[int(loglevel)]
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    def getlog(self):
        return self.logger    
    @staticmethod
    def CreateInstance():
        global _log
        if _log == None:
            _log = Logger(logname='log.txt', loglevel=1, logger="fox").getlog()
        return _log
    @staticmethod
    def Test():
        Logger.CreateInstance().error("mytest--------")
def LOG(msg):
    """注意： 不用的时候要马上关掉， 否则log文件会越来越大, 当前目录的log.txt"""
    msg = str(msg)
    Logger.CreateInstance().info(msg)
def datetime_to_date(d):
    """return: str"""
    s = str(d)
    if s.find(':')>0:
        return s.split(' ')[0]
    return s
def getCallerName():
    """返回函数调用者的文件名及完全函数名, 在并行进程中调用者堆栈会不一样"""
    import traceback
    s_trace = traceback.extract_stack()
    full_function_name = s_trace[-3][2]
    #获取执行行的函数名
    #s_trace = s_trace[-4]
    #full_function_name = s_trace[-1]
    #s_filters = list('().')
    #for s_filter in s_filters:
        #if full_function_name != None:
            #full_function_name = str.replace(full_function_name, s_filter, '')
        #else:
            #full_function_name = ''
    #文件名， 函数全名
    filename = sys._getframe(2).f_code.co_filename
    filename = os.path.basename(filename)
    filename = filename.split('.')[0]
    return filename + "_" + full_function_name
def IsNone(val):
    """判断值是否为None return: bool"""
    return isinstance(val, type(None))
_DEBUG = False
def startDebug():
    global _DEBUG
    _DEBUG = True
def IsDebug():
    if _DEBUG:
        return _DEBUG
    import psutil
    cmdlines = psutil.Process(os.getpid()).cmdline()
    if len(cmdlines)>2 and cmdlines[2].find('wingdb')>0:
        return True
    return False

_ISRUNATCMD = None
def IsRunAtCmd():
    """当前进程在cmd中执行
    进程打印结果['python', 'agl.py']
    return: boolean
    """
    global _ISRUNATCMD
    if _ISRUNATCMD is None:
        import psutil
        cmdlines = psutil.Process(os.getpid()).cmdline()
        #print(cmdlines)
        _ISRUNATCMD = len(cmdlines)>=2 and cmdlines[0] == 'python'
    return _ISRUNATCMD
    
def is_utf8(s):
    return charade.detect(s)['encoding'] == 'utf-8'
def is_unicode(s):
    return isinstance(s, unicode)
def is_function(fn):
    return hasattr(fn, '__call__')
def df_filter(df, fn):
    for index, row in df.iterrows():
        fn(row)
def df_concat(df1, l):
    """添加list到df1中
    df1: pd.DataFrame
    l : list
    """
    return pd.concat([df1, pd.DataFrame(l).T])
def df_remove_col(df, cols):
    """df删除列 return: df"""
    return df.drop(cols, axis=1)
def df_allow_copy(df):
    df.is_copy=False
    return df
def df_get_str(feild, is_utf=True):
    """把df某个feild转换为字符串
    feild : 从df中取出的字符串字段
    is_utf : 该字符串是否为utf8
    return: asi ii"""
    l = np.array(feild)
    if len(l) == 0:
        return ""
    if not isinstance(l[0], str):
        return ""
    s = l[0]
    if is_utf:
        s = s.decode('utf8')
    return s
def TraceToStr(l):
    ss = ''
    for s in l:
        for f in s:
            ss += str(f) + " "
        ss += "\n"
    return ss
def df_to_html(df):
    s = ''
    for i in range(len(df)):
        s += str(df.irow(i)[0])
        s += '<br>'
    return s
def print_df(df):
    """完整的打印df"""
    #s = df.to_string()
    #s = s.encode('utf8')
    #pprint.pprint(s)
    if 0: df = pd.DataFrame
    i=0
    while i<len(df):
        start_index = i
        i += 50
        v = df.iloc[start_index:i]
        v = v.to_string()
        print(df.iloc[start_index:i])
def print_prettey_df(df):
    from prettytable import PrettyTable
    table = PrettyTable(df.columns.tolist())
    for i,row in df.iterrows():
        table.add_row(row.tolist())
    print(table)
def print_ary(ary):
    """打印数组元素内容"""
    for x in ary:
        print(x)
def print_u(s):
    try:
        print(utf8_to_unicode(s))
    except:
        print(s)
def zip_file(src, dest):
    """把src压缩到dest, 暂时只支持一个文件"""
    f = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)
    f.write(src)
    f.close()
def unzip_file(src, dest):
    """把src解压缩到dest, 暂时只支持一个文件"""
    f = zipfile.ZipFile(src)
    f2 = open(dest, 'wb')
    f2.write(f.read(f.namelist()[0]))
    f2.close()
    f.close()
def compress_file(fn_in, fn_out):  
    f_in = open(fn_in, 'rb')  
    f_out = gzip.open(fn_out, 'wb')  
    f_out.writelines(f_in)  
    f_out.close()  
    f_in.close()  
  
def uncompress_file(fn_in, fn_out):  
    f_in = gzip.open(fn_in, 'rb')  
    f_out = open(fn_out, 'wb')  
    file_content = f_in.read()  
    f_out.write(file_content)  
    f_out.close()  
    f_in.close() 
    
def get_string_digit(s):
    """提取字符串中的数值, s: 字符串 return: float"""
    if not isinstance(s, str):
        s = ''
    if s=='np.nan':
        return -0.01
    s = list(s)
    s_result = ''
    for i, s1 in enumerate(s):
        if s1.isdigit() or s1 =='.' :
            s_result += s1
        if s1 == '-' and i+1 < len(s) and s[i+1].isdigit():
            s_result += s1
    if s_result == '':
        return -0.01
    return float(s_result)
def df_get_pre_date(df, date):
    """获取当前日期的上一个索引日期 return : str(date)"""
    d = df.ix[:date].index[-2]
    d = datetime_to_date(d)
    if d == date:
        #5分钟
        indexs = df.ix[:date].index
        for index in indexs.sort_values(ascending=False):
            d = datetime_to_date(index)
            if d != date:
                break
    return d
def where(con, a, b):
    """条件选择， con条件， 同c的con ? a : b
    (1) variable = a if exper else b
    (2) variable = (exper and [b] or [c])[0]
    (3) variable = exper and b or c
    """
    if con is None:
        return b
    if con:
        return a
    return b
def find_str_use_re(pattern, string, index=0):
    """用正则表达式提取结果, 其中的一个
    pattern: 表达式
    string: 源字符串
    index : 表达式中的结果, 从0开始
    reutrn: str 失败返回空字符"""
    m = re.match(pattern, string)
    if m == None:
        return ""
    if len(m.groups()) < index:
        return ""
    return m.groups()[index]    

def calcGoldCut(v, is_left=True, ratio=0.62):
    """计算黄金分割的位置 sample-  calcGoldCur([10,20], True) => 14.8
    v: list[2], float 数值, v[1]大于v[0]
    is_left: 取靠近左边的点还是右边的点
    ratio: float 分割点
    return: float"""
    #ratio = 0.62
    c=abs(v[1]-v[0])
    cut = float(abs(v[1]-v[0]) ) * ratio
    if is_left:
        return v[0] + (c-cut)
    return v[0] + cut
def IntToQianFenHaoStr(num):
    """数字转带千分号的字符串"""
    return "{:,}".format(num)

def ClustList(n_clusters, X):
    """对一维数组进行聚类, 
    return: list [int,] 从小到大排序"""
    if len(X)<= n_clusters:
        return X
    from sklearn.cluster import KMeans
    results_n = np.zeros((len(X),2))
    results_n[:,0] = 1
    results_n[:,1] = np.array(X)
    #用kmeans聚类
    k = KMeans(n_clusters=n_clusters)
    k.fit(results_n)    
    l = k.cluster_centers_[:,1]
    l.sort()
    return l

def ClustList2(n, X):
    """获取聚类后的最大结果
    return: [(percent, v),...], result_v
    """
    from sklearn.cluster import KMeans
    results_n = np.zeros((len(X),2))
    results_n[:,0] = 1
    results_n[:,1] = np.array(X)
    #用kmeans聚类
    k = KMeans(n_clusters=n)
    k.fit(results_n)    
    result = k.cluster_centers_
    total = len(X)
    for label in np.unique(k.labels_):
        c = float(len(k.labels_[k.labels_== label]))/total
        #print(c)
        result[label, 0] = c
    #按百分比排序，大的在前面
    #print(result)
    max_index = GetSortedArrayIndexs(result[:,0])[0]
    #result.sort()
    #print(result[max_index, 1])
    return result, result[max_index, 1]
    
def ClustMatrix(n, m):
    """n: int 聚类数量
    m: np.ndarray 二维
    return: [(percent, v),...], result_v
    """
    #用kmeans聚类
    k = KMeans(n_clusters=n)
    k.fit(m)    
    result = k.cluster_centers_
    total = len(X)
    for label in np.unique(k.labels_):
        c = float(len(k.labels_[k.labels_== label]))/total
        result[label, 0] = c
    #按百分比排序，大的在前面
    max_index = GetSortedArrayIndexs(result[:,0])[0]
    return result, result[max_index, 1]

def MD5(s):
    import hashlib   

    m2 = hashlib.md5()   
    m2.update(s)   
    return m2.hexdigest()       

class Marco:
    """模拟c的宏机制, 定义一个字符串，然后用eval执行"""
    #调试状态使用单进程
    IMPLEMENT_MULTI_PROCESS = 'if not agl.IsDebug():\n\tfrom autoxd import backtest_policy\n\tbacktest_policy.MultiProcessRun(cpu_num, codes, Run, __file__)\nelse:\n\tRun(codes)\n'

def test_post():
    import requests
    print(requests.__version__)

    
def main(args):
    #TestMoveFile()

    #Unittest()
    #print GetSortedArrayIndexs([29,30,19,50],4)
    #Unittest_array_transpose()
    #x =[[1,2],[3,4]]
    ##print array_insert_col(x, 1, [5,6])
    #print array_insert(x, len(x), np.array([[99,99],[100,100]]))

    #unittest_matrixtostring()    
    #PngToTxt('1.png')
    #genPwd(1024)
    #unittest_pickle()
    #count_char()
    #MatrixToCsv([[1,2,3,2],[2,3,3,4],[23,23,2,3],[23,2,3,3]], "B.txt")
    #print convert_html(u'\xca\xd0\xd3\xaf\xc2\xca(\xb6\xaf\xcc\xac)\xa3\xba70.54')

    #SerialMgr.unittest()
    #NetTest()
    #Logger.Test()
    #removeDir(os.getcwd()+'/html')
    #archiveZip('tmp/my.zip', 'html')
    #a = tic_toc()
    #print(ClustList(3, [100,300,600,300,600,300,600,1200]))
    #print(ClustList(2, [200]))
    #print(IsRunAtCmd())
    test_post()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)