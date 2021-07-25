#coding:utf8

"""人工判断一个boll是否能买卖"""
from __future__ import print_function
import os,sys, warnings
def getMainDir():
    cur_file_path = __file__
    if cur_file_path == '':
        cur_file_path = os.path.abspath(os.path.curdir)
    else:
        cur_file_path = os.path.abspath(cur_file_path)
    cur_file_path = os.path.dirname(cur_file_path)
    add_path = cur_file_path + '/..'
    #print(add_path)
    add_path = os.path.abspath(add_path)
    #print(add_path)
    return add_path    
def AddPath():
    from sys import path
    add_path = getMainDir()
    if not add_path in path:
        #print(add_path)
        path.append(add_path)
AddPath()
import math
import numpy as np   
#-------------------------------------------------------------------------------------------
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #NavigationToolbar2TkAgg
#------------------------------------------------------------------------------------------
try:
    import Tkinter as tk
except:
    pass
#------------------------------------------------------------------------------------------
from autoxd import ui, stock
if sys.version > '3':
    from autoxd.pinyin import stock_pinyin3 as jx
else:
    from autoxd import stock_pinyin as jx
#import tushare_handle as th
from autoxd import agl
from autoxd.cnn_boll import env
import pandas as pd
import optparse

mpl.rcParams['font.sans-serif'] = ['SimHei']  #中文显示
mpl.rcParams['axes.unicode_minus']=False      #负号显示

#初始化数据集, 设置codes, 时间不需要设置， 完整使用加载的数据集
#from strategy import basesign
#codes = basesign.switch_codes

g_scope_len = 30  #图片尺寸
g_nohead_df_len = 5    #close只显示后面的一部分
g_is_use_close = True   #是否使用close

def drawBoll(pl,closes, boll_up, boll_mid, boll_low):
    pl.plot(closes)
    pl.plot(boll_up)
    pl.plot(boll_mid)
    pl.plot(boll_low)
    #取消xylabels
    pl.axis('off')
class data_sources():
    def _getPath(self):
        """数据源目录
        """
        sources_path = env.get_root_path() + '/cnn_boll/datasources/'
        return sources_path

    def loadData(self, code):
        """ return: df  five hisdat"""
        data_path = self._getPath()
        return stock.getFiveHisdatDf(code, method='path', path=data_path)
    def loadCodes(self):
        data_path = self._getPath()
        if os.path.isdir(data_path):
            return [ str(f).split('.')[0] for f in os.listdir(data_path)]
        return []
class data_tdx(data_sources):
    def loadCodes(self):
        return [jx.HCGD]
    def loadData(self, code):
        import warp_pytdx as tdx
        df = tdx.getFive(code)
        df = df['2018-10-2':]
        return df
        
data_interface = data_sources()
#data_interface = data_tdx()
codes = data_interface.loadCodes()
def getData(code):
    """return: upper, middle, lower, df, adx
    """
    #加载数据
    #df = stock.LiveData().getFiveMinHisdat(code)
    df = data_interface.loadData(code)
    #df = df[:200]
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)
    highs, lows, closes = df['h'], df['l'], df['c']
    adx = stock.TDX_ADX(highs, lows, closes)
    #closes = df['c'].values
    return upper, middle, lower, df, adx
def getBolls(boll_up, boll_mid, boll_low):
    return [boll_up, boll_mid+(boll_up-boll_mid)/2 , boll_mid, boll_low+(boll_mid-boll_low)/2, boll_low]

def filter_close(h, l, middle):
    """当在mid上面时用high, 下面时用low
    return c 用合并后的序列作为close
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")	
        return np.where(h>middle, h, l)    

f = plt.figure(figsize=(6,6))
def drawfig(index, datas):
    """画5分钟线的boll图
    index : int
    datas : (ary,ary,ary,df)
    """
    assert(index>=100)
    u,m,l,df,adx = datas
    scope_len = g_scope_len  #图片尺寸

    f.clf()
    #plt.plot([1,2,3])
    index_s = index-scope_len
    if index_s < 0:
        index_s = 0
    c = filter_close(df['h'].values[index_s:index], df['l'].values[index_s:index], m[index_s:index])
    if g_nohead_df_len>0:
        index_close_nohead = len(c) - g_nohead_df_len
        c[:index_close_nohead] = np.nan
    if not g_is_use_close:
        c[:] = np.nan
    drawBoll(plt, c, u[index_s:index], m[index_s:index], l[index_s:index])
    
    #绘制价格水平线
    #分上涨和下跌
    #m = m[index_s:index]
    #assert(len(c) == len(m))
    #c = c[c<m] if c[-1]>m[-1] else c[c>m]
    #if len(c)>0:
        #sign = 1 if c[-1]>m[-1] else 0
        #r, v = agl.ClustList2(3, c)
        #clrs = ['LawnGreen', 'Chocolate']
        #ui.DrawHLine(plt, v, scope_len, clrs[sign])
            
    #r, v = agl.ClustList2(3, c)
    #clrs = ['LawnGreen', 'Chocolate']
    #ui.DrawHLine(plt, v, scope_len, clrs[0])
        
    return f

def allow_pos_w_adx(close, boll, boll_w):
    """由技术参数判断当前是否在交易范围
    boll : np.array[5] up,...,low
    """
    if boll_w < 2 and (close > boll[0]  or close < boll[-1]):
        return True
    if (boll_w>2 and boll_w<4.2) and (close>boll[1] or close<boll[-2]):
        return True
    if boll_w>4.2 and (close>boll[2]*1.01 or close<boll[2]*0.99):
        return True
    return False
    #return not (close<boll[1] and close>boll[-2])
    
class From:
    def __init__(self): 
        self.root=tk.Tk()                    #创建主窗体
        self.canvas=tk.Canvas()              #创建一块显示图形的画布
        #self.figure=self.create_matplotlib() #返回matplotlib所画图形的figure对象
        self.code_index = 0
        self.code = codes[self.code_index]
        self.datas = getData(self.code)
        self.index = len(self.datas[-1]) - 100
        self.figure = drawfig(self.index, self.datas)
        self.create_form(self.figure)        #将figure显示在tkinter窗体上面
        #self.root.geometry('600x300')
        self.root.mainloop()
    def _getNext(self):
        """计算index
        return: bool 是否到结尾
        """
        #当前code已到结尾或超过设定时间, 那么跳到下一个code
        while True:
            self.index += 1
            if self.index >= len(self.datas[0]):    #go to next code
                self.code_index += 1
                if self.code_index >= len(codes):   #go to end
                    return False
                self.code = codes[self.code_index]
                self.datas = getData(self.code)
                self.index = len(self.datas[-1]) - 100
            boll_up, boll_mid, boll_low, df, adx = self.datas
            adx = int(adx[self.index])
            bolls = getBolls(boll_up[self.index], boll_mid[self.index], boll_low[self.index])        
            boll_w = 100*abs(boll_up[self.index]-boll_low[self.index])/boll_mid[self.index]
            close = df.iloc[self.index]['c']
            if allow_pos_w_adx(close, bolls, boll_w) and adx > 30:
                return True
        return True
    def create_form(self,figure):
        #把绘制的图形显示到tkinter窗口上
        self.canvas=FigureCanvasTkAgg(figure,self.root)
        self.canvas.draw()  #以前的版本使用show()方法，matplotlib 2.2之后不再推荐show（）用draw代替，但是用show不会报错，会显示警告
        #self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=7)

        #添加button
        x_pos = 300
        y_pos = 10
        label_adx = tk.Label(self.root, text='ADX= ').place(x=250, y= y_pos)
        var_adx = tk.StringVar()
        var_adx.set('0')
        entry_adx = tk.Entry(self.root, textvariable=var_adx)
        entry_adx.place(x = 300, y = y_pos, width=30)
        label_bollw = tk.Label(self.root, text='BollW= ').place(x=0, y= y_pos)
        var_bollw = tk.StringVar()
        var_bollw.set('0')
        entry_bollw = tk.Entry(self.root, textvariable=var_bollw)
        entry_bollw.place(x = 60, y = y_pos, width=50)
        label_four = tk.Label(self.root, text='FOUR= ').place(x=110, y= y_pos)
        var_four = tk.StringVar()
        var_four.set('0')
        entry_four = tk.Entry(self.root, textvariable=var_four)
        entry_four.place(x=170, y=y_pos, width=50)
        mylabel = tk.Label(self.root, text='选择状态: ').place(x=340, y= y_pos)
        var_usr_name = tk.StringVar()
        var_usr_name.set('0-7')
        entry_usr_name = tk.Entry(self.root, textvariable=var_usr_name)
        entry_usr_name.place(x=x_pos + 120, y= y_pos)       
        #加载之前已保存的结果
        df_result = DfResult()
        df_result.clear()
        def write_result(label):
            b = self._getNext()
            #if self.index == 103:
                #b = False
            while b:
                #写结果  
                df = self.datas[-2]
                t = str(df.index[self.index])
                t1 = t.replace(' ', '_')
                t1 = t1.replace(':', '_')
                fname = self.code +'_'+ t1+'.png'
                print(fname)
                #判断是否已经保存过
                
                b = False
                if len(df_result.df) == 0:
                    b = True
                elif not (df_result.df[2] == fname).any():
                    b = True
                if b:  
                    u,m,l,df,adx = self.datas
                    #计算显示的指标值
                    bollw = (u[self.index]-l[self.index])/m[self.index]*100
                    adx = int(adx[self.index])
                    four = stock.FOUR(df[:self.index]['c'])
                    var_four.set(agl.float_to_2(four[-1]*100))
                    var_adx.set(agl.float_to_2(adx))
                    var_bollw.set(agl.float_to_2(bollw))
                    fname1 = df_result.dir_img + fname
                    drawfig(self.index, self.datas)
                    self.canvas.draw()
                    plt.savefig(fname1)
                    result = [self.code, t, fname, label]
                    df_result.insert(result)
                    break
                else:  #发现已经录入
                    b = self._getNext()
                    
            if not b:
                #显示已结束
                f.clf()
                f.text(0.5,0.5,'its end',color='r')
                self.canvas.draw()
                #输出到文件
                df_result.save()
        def button_handle_0():
            var_usr_name.set(0)
            write_result(0)
        def button_handle_1():
            var_usr_name.set(1)
            write_result(1)
        def button_handle_2():
            var_usr_name.set(2)
            write_result(2)
        def button_handle_3():
            var_usr_name.set(3)
            write_result(3)
        def button_handle_4():
            var_usr_name.set(4)
            write_result(4)
        def button_handle_5():
            var_usr_name.set(5)
            write_result(5)
        def button_handle_6():
            var_usr_name.set(6)
            write_result(6)
        fns = [button_handle_0,button_handle_1, button_handle_2,button_handle_3,button_handle_4,button_handle_5,button_handle_6]
        def key(event):
            #print "pressed", repr(event.char)
            c = event.char
            if c>='0' and c<='6':
                #var_usr_name.set(event.char)
                fns[int(c)]()
        for i in range(7):
            button = tk.Button(self.root, text=str(i), command=fns[i], width=10, height=2)
            #button.place(x=170, y=230)
            button.grid(row=i,column=1)
        self.root.bind('<Key>', key)
        def on_closing():
            df_result.save()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)        
        
        #把matplotlib绘制图形的导航工具栏显示到tkinter窗口上
        #toolbar =NavigationToolbar2Tk(self.canvas, self.root) #matplotlib 2.2版本之后推荐使用NavigationToolbar2Tk，若使用NavigationToolbar2TkAgg会警告
        #toolbar.update()
        #self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

class DfResult:
    """df持续化"""
    def __init__(self, reinit=False):
        self.fname='df_img_label.csv'
        self.dir = 'img_labels'
        self.dir_img = self.dir + '/imgs/'
        if not os.path.isdir(self.dir):
            os.mkdir(self.dir)
        if not os.path.isdir(self.dir_img):
            os.mkdir(self.dir_img)
        if reinit:
            self.clear()
        self.df = pd.DataFrame([])
        self.fname = self._getFnamePath()
        self.load()
    def save(self):
        #self.df.to_hdf(self.fname, 'v1', mode='w')
        self.df.to_csv(self.fname, header=True, index=False)
    def load(self):
        if os.path.isfile(self.fname):
            #self.df = pd.read_hdf(self.fname)
            self.df = pd.read_csv(self.fname,dtype='str')   #这里异常了需要删除空文件
            self.df.columns = range(len(self.df.columns))
    def insert(self, l):
        self.df = pd.concat([self.df, pd.DataFrame(l, dtype='str').T])
    def _getFnamePath(self):
        return self.dir + '/' + self.fname
    def clear(self):
        fname = self._getFnamePath()
        if os.path.isfile(fname):
            os.remove(fname)

    @staticmethod
    def test():
        bReInit = False
        #bReInit = True
        c = DfResult(bReInit)
        print(c.df)
        #c.df = pd.DataFrame([])
        c.insert([2,3,4])
        print(c.df)
        c.save()

def IsSide(close, upper, lower, middle):
    """在上下中轨之外"""
    boll_poss = [
        upper[-1],
     (upper[-1] - middle[-1])/2+middle[-1],
     middle[-1],
     (middle[-1] - lower[-1])/2+lower[-1],	     
     lower[-1],
    ]    
    price = close[-1]
    return price > boll_poss[1] or price < boll_poss[-1]
    

def genImgs():
    """从数据直接生成图片"""
    global codes
    dest_dir = 'img_labels/imgs/'
    # 加载数据源
    codes = codes[:5]
    for code in codes:
        datas = getData(code)
        upper, middle, lower, df, adx = datas
        if len(df) < 100:
            continue
        if IsSide(df['c'].values, upper, lower, middle):
            for index in range(100, len(df) - g_scope_len):
                drawfig(index, datas)
                #这里为了简单实现， 只使用index作为编号
                fname = dest_dir + code + '_' + str(index) + '.png'
                plt.savefig(fname)            
    
if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option('-n','--noclick', dest='noclick', action="store_true", help='不使用界面，直接生成')
    parser.add_option('--nohead', dest='nohead', action="store_true", help="close不显示前面的部分")
    parser.add_option('--noclose', dest='noclose', action="store_true", help="close不使用")
    
    options, build_files_arg = parser.parse_args(sys.argv[1:])
    
    if options.nohead is None:
        g_nohead_df_len = 0
    g_is_use_close = options.noclose is None
    
    if options.noclick is None:
        #DfResult.test()
        form=From()
    else:    
        genImgs()
