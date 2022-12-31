#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# mail: nessessary@qq.com

import numpy as np
import pylab as pl
import sys,os,codecs
from autoxd import agl
from autoxd.pypublish.policy_report import df_to_html_table

"""模仿matlab的publish, 注意在__main__中调用有可能不会触发析构, pl的绘制放入一个函数中
在当前工作目录中生成一个html\name\name.html
plot生成png，绑定到html中
"""

def publishinfo():
    return sys._getframe(2).f_code.co_filename, sys._getframe(2).f_code.co_name, sys._getframe(2).f_lineno
def IsPublish(pl):
    """判断发布是否已经初始化"""
    return isinstance(pl, Publish)
        
class Publish:
    def __init__(self, explicit=False, is_run_shell=True, is_clear_path=False):
        """编码默认为utf8
        info: 由pushlishinfo获取的元组
        explicit: 弹出页面是否使用显式调用
        is_run_shell: bool 是否跑生成后的start
        is_clear_path: bool 是否清空之前生成的目录文件
        """
        #当前目录
        self.path = os.getcwd() + "/html/"
        if not os.path.isdir("html"):
            os.mkdir("html")        
        if is_clear_path:
            #删除当前目录的文件
            dirPath = self.path
            agl.removeDir(dirPath)
            
        #os_platform
        self.platform_id = 2
        if sys.platform == 'win32':
            self.platform_id = 0
        if sys.platform == 'darwin':
            self.platform_id = 1
            
        info = publishinfo()
        name = os.path.basename(info[0])
        name = name.replace('.py','')
        module = info[1]
        module = str(module).replace('<','')
        module = module.replace('>','')
        name += '_' + module
        
        self.source_startrow = info[2] - 1

        self.explicit = explicit
        #获取模板html
        self.t_html = ''
        f = open(os.path.dirname(__file__)+'/test.html', 'r')
        self.t_html = f.read()
        if agl.IsRunAtCmd() or sys.version>'3':
            self.t_html = self.t_html.replace('utf-8', 'gb2312')
        f.close()
        
        self.name = name 
        self.fig_num = 1

        #当前目录
        self.path = os.getcwd() + "/html/"
        if not os.path.isdir("html"):
            os.mkdir("html")
        #重定向输出
        self.redirect_fname = 'html/log'+str(os.getpid())+'.txt'
        if self.platform_id == 0:
            self.logfile = open(self.redirect_fname, "w")
        else:
            self.logfile = codecs.open(self.redirect_fname,'w', encoding='utf_16')
        self.oldstdout = sys.stdout
        sys.stdout = self.logfile
        
        self.figs = []
        self.imgs = []
        self.use_figure = False
        
        #最后对imgs赋值
        self.myimgs = ''
        self.is_run_shell = is_run_shell
        
    def __del__(self):
        #if self.explicit == False:
            #self.publish() #python 3 can't call open
        # 解除stdout
        sys.stdout = self.oldstdout
    def publish(self):
        """显示页面"""
        self.explicit = True
        
        self.logfile.close()
        sys.stdout = self.oldstdout
        if self.platform_id == 0:
            f = open(self.redirect_fname, "r")
        else:
            f = codecs.open(self.redirect_fname, 'r', encoding='utf_16')
        output = f.read()
        f.close()
        
        self.AddTitle(self.name)
        self.AddImg()
        self.AddOutput(output)
        #f = open(info[0], 'r')
        #source = np.array(f.readlines())
        #f.close()
        #self.AddSource( source[self.source_startrow:info[2]])
        
        #写入html
        fname = self.path+self.name+str(os.getpid())+'.html'
        if self.platform_id == 0:
            f = open(fname,'w', encoding='utf8')
        else:
            f = codecs.open(fname, 'w', encoding='utf_16')
        f.write(self.t_html)
        f.close()
        
        #打开html
        if self.is_run_shell:
            cmds = ['start', 'open', 'x-www-browser']
            command = cmds[self.platform_id]
            command += ' ' + fname
            os.system(command)
        
    
    def figure(self, num=None,  # autoincrement if None, else integer from 1-N
               figsize=None,  # defaults to rc figure.figsize
               dpi=None,  # defaults to rc figure.dpi
               facecolor=None,  # defaults to rc figure.facecolor
               edgecolor=None,  # defaults to rc figure.edgecolor
               frameon=True,
               FigureClass=pl.Figure,
               **kwargs
               ):    
    #def figure(self, id=1):
        #num = self.fig_num
        fig = pl.figure(num, figsize, dpi, facecolor, edgecolor, frameon, FigureClass, **kwargs)
        #fig = pl.gcf()
        self.figs.append(fig)
        #self.fig_num += 1
        return fig
    def subplots_adjust(self, *args, **kwargs):    
        return pl.subplots_adjust(*args, **kwargs)
    def gcf(self):
        return pl.gcf()
    def clf(self):
        pl.clf()
    def text(self, x, y, s, fontdict=None, withdash=False, **kwargs):
        pl.text(x, y, s, fontdict, withdash, **kwargs)
    def plot(self, *args, **kwargs):
        pl.plot(*args, **kwargs)
    def hist(self, *args, **kwargs):
        pl.hist(*args, **kwargs)
    def grid(self, *args, **kwargs):
        pl.grid(*args, **kwargs)
    def ylabel(self, *args, **kwargs):
        pl.ylabel(*args, **kwargs)
    def xlabel(self, *args, **kwargs):
        pl.xlabel(*args, **kwargs)
    def legend(self, *args, **kwargs):
        pl.legend(*args, **kwargs)
    def axis(self, *v, **kwargs):
        pl.axis(*v, **kwargs)
    def bar(self, *args, **kwargs):
        pl.bar(*args, **kwargs)
    def barh(self, *args, **kwargs):
        pl.barh(*args, **kwargs)
    def imshow(self, X, cmap=None, norm=None, aspect=None, interpolation=None, alpha=None,
           vmin=None, vmax=None, origin=None, extent=None, shape=None,
           filternorm=1, filterrad=4.0, imlim=None, resample=None, url=None,
           hold=None, data=None, **kwargs):
        pl.imshow(X, cmap, norm, aspect, interpolation, alpha, vmin, vmax, origin, extent, shape, filternorm, filterrad,
                  imlim, resample, url, hold, data, **kwargs)
    def scatter(self, x, y, s=20, c='b', marker='o', cmap=None, norm=None, vmin=None,
                vmax=None, alpha=None, linewidths=None, verts=None, hold=None,
                **kwargs):
        pl.scatter(x,y,s,c,marker,cmap,norm,vmin,vmax,alpha,linewidths,verts,hold,**kwargs)
    def subplot(self, *args, **kwargs):
        pl.subplot(*args, **kwargs)
    
    def title(self, s, *args, **kwargs):
        pl.title(s, *args, **kwargs)
        
    def savefig(self, *args, **kwargs):
        pl.savefig(*args, **kwargs)
    def close(self, *args, **kwargs):
        pl.close(*args, **kwargs)
    def rc(self, *args, **kwargs):
        pl.rc(*args, **kwargs)
        
    def save(self):
        if len(self.figs) == 0:
            self.use_figure = True
            self.figs.append(pl.gcf())
        sPid = str(os.getpid())
        for i,fig in enumerate(self.figs):
            fname = self.path + self.name + "_" + sPid + '_' + str(i) +".png"
            if self.use_figure:
                fname = self.path + self.name + "_" + sPid + '_' + str(len(self.imgs)) + ".png"
            self.imgs.append(fname)            
            self.cur_img_fname = fname
            #self.figs[-1].savefig(fname, dpi=70)
            pl.savefig(fname, dpi=70)
            if self.myimgs != "":
                self.myimgs += '<img vspace="5" hspace="5" src="'+os.path.basename(fname)+'" alt="">\n'
    def get_CurImgFname(self):
        return self.cur_img_fname
    def attach_imgs(self, new_imgs_html):
        """原来img的位置用新的html代替， 一般是表格html
        其实就是使用新的html"""
        self.myimgs = new_imgs_html
    def reset(self, html):
        self.attach_imgs(html)
    def insertHtml(self, html):
        self.myimgs += html
        
    def AddTitle(self,title):
        self.t_html = self.t_html.replace('<%title%>', title)
        
    def AddSource(self, source):
        #s = ''
        #for str in source:
            #s += str
        self.t_html = self.t_html.replace('<%source%>', source)

    
    def AddImg(self):
        img_html = ''
        #for i in range(len(self.figs)):
            #img_html += '<img vspace="5" hspace="5" src="'+self.name+'_'+str(i)+'.png" alt="">'
        for img_path in self.imgs:
            img_path = os.path.basename(img_path)
            img_html += '<img vspace="5" hspace="5" src="'+img_path+'" alt="">'
        #print img_html
        if self.myimgs != '':
            img_html = self.myimgs
        self.t_html = self.t_html.replace('<%img%>', img_html)
    
    def AddOutput(self, output):
        self.t_html = self.t_html.replace('<%output%>', output)
        import datetime
        year = datetime.datetime.now().year
        self.t_html = self.t_html.replace('<%year%>', str(year))        
        
    def show(self):
        self.save()
    
    def RePublish(self, report):
        """按表格发布
        report_content: list
        """
        import pandas as pd
        from policy_report import df_to_html_table
        df = pd.DataFrame(report)
        self.reset(df_to_html_table(df))
        self.publish()
        
def example():
    #不发布把该行注销
    pl = Publish()
    print('test python html publish.')
    print(u'测试')
    for i in range(2):
        pl.figure(i)
        pl.plot(np.arange(0,10*(i+1)))
    pl.show()

def example2():
    """测试排版输出， 让单元数据在一行内"""
    from autoxd import stock
    import pandas as pd
    print(example2.__doc__)
    pl = Publish(explicit=True)
    codes = stock.get_codes(flag=stock.myenum.randn, n=6)
    result = []
    for code in codes:
        df_five = stock.getFiveHisdatDf(code, method='tdx')
        df_five.plot()
        pl.show()
        pl.close()
        img_name = pl.get_CurImgFname()
        result.append([code, img_name, img_name])
    df = pd.DataFrame(result)
    pl.reset(df_to_html_table(df, df_img_col_indexs=[-2,-1]))
    pl.publish()
    
def main(args):
    example()
    example2()
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)