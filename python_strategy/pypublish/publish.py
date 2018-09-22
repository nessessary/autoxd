#-*- coding:utf-8 -*-
# Copyright (c) Kang Wang. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# QQ: 1764462457

import numpy as np
import pylab as pl
import sys,os,psutil

"""模仿matlab的publish, 不用怀疑，只是最简单的模拟
在当前工作目录中生成一个html\name\name.html
plot生成png，绑定到html中
2014-3-7 耗时4小时
"""

def publishinfo():
    return sys._getframe(2).f_code.co_filename, sys._getframe(2).f_code.co_name, sys._getframe(2).f_lineno
def IsPublish(pl):
    """判断发布是否已经初始化"""
    return isinstance(pl, Publish)
        
class Publish:
    def __init__(self, explicit=False, is_run_shell=True):
        """编码默认为utf8
        info: 由pushlishinfo获取的元组
        explicit: 弹出页面是否使用显式调用
        is_run_shell: bool 是否跑生成后的start
        """
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
        f.close()
        
        self.name = name 
        #当前目录
        self.path = os.getcwd() + "\\html\\"
        if not os.path.isdir("html"):
            os.mkdir("html")
        #重定向输出
        self.redirect_fname = 'html/log'+str(os.getpid())+'.txt'
        self.logfile = open(self.redirect_fname, "w")
        self.oldstdout = sys.stdout
        sys.stdout = self.logfile
        
        self.figs = []
        self.imgs = []
        self.use_figure = False
        
        #最后对imgs赋值
        self.myimgs = ''
        self.is_run_shell = is_run_shell
        
    def __del__(self):
        if self.explicit == False:
            self.publish()
    def publish(self):
        """如果执行了publish, 那么析构时就不要再执行了"""
        self.explicit = True
        
        self.logfile.close()
        sys.stdout = self.oldstdout
        f = open(self.redirect_fname, "r")
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
        f = open(fname,'w')
        f.write(self.t_html)
        f.close()
        
        #打开html
        if self.is_run_shell:
            command = 'start ' + fname
            os.system(command)
        
    
    def figure(self, id=1):
        fig = pl.figure(id)
        self.figs.append(fig)
        return fig
    def gcf(self):
        return pl.gcf()
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
    def bar(self, *args, **kwargs):
        pl.bar(*args, **kwargs)
    def barh(self, *args, **kwargs):
        pl.barh(*args, **kwargs)

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
            pl.savefig(fname, dpi=70)
    def get_CurImgFname(self):
        return self.cur_img_fname
    def attach_imgs(self, new_imgs_html):
        """原来img的位置用新的html代替， 一般是表格html
        其实就是使用新的html"""
        self.myimgs = new_imgs_html
    def reset(self, html):
        self.attach_imgs(html)
        
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
        
def example():
    #不发布把该行注销
    pl = Publish()
    print('test python html publish.')
    for i in range(2):
        pl.figure(i)
        pl.plot(np.arange(0,10*(i+1)))
    pl.show()
    
def main(args):
    example()
    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)