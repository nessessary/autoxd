#coding:utf8

"""标注聚类结果
[id, datas_index, code, dt, tick_period, clust_id, label_id, label_desc]

废弃，手工输入描述
"""
assert(False)
import os, time
import pearson_clust
import judge_boll_sign
import numpy as np
import tkinter as tk
from abc import ABCMeta, abstractmethod
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #NavigationToolbar2TkAgg

class WinDelegate(object):
    __metaclass__ = ABCMeta
    def createFig(self):
        return None
    
class Win(WinDelegate):
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas()
        self._create_win()
        self.root.mainloop()
    def _create_win(self):
        fig = self.createFig()
        self.canvas = FigureCanvasTkAgg(fig, self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=7)
        
        #add text
        x_pos = 10
        y_pos = 10
        label_adx = tk.Label(self.root, text='Desc= ').place(x=250, y= y_pos)
        var_adx = tk.StringVar()
        var_adx.set('0')
        x_pos += 150
        y_pos += 20
        entry_adx = tk.Entry(self.root, textvariable=var_adx)
        entry_adx.place(x = x_pos, y = y_pos, width=500)
        
        #add button
        def OnButton():
            #tk的edit不支持中文输入法
            print('button click', entry_adx.get())
            
        button = tk.Button(self.root, text='submit', command=OnButton, width=10, height=2)
        button.grid(row=5,column=2)
        
        def on_closing():
            self.root.destroy()
        self.root.protocol("WM_DELETE_WINDOW", on_closing)            
    def set_datas(self, datas):
        self.datas = datas
        
class Labeler(Win):
    """用一个界面来标注图形, 每个界面标注一个？"""
    def __init__(self):
        self.load()
        super().__init__()
    def load(self):
        """ 加载数据源, 聚类结果"""
        datas = pearson_clust.load_data()
        #datas = pearson_clust.load_csv_data()
        self.set_datas(datas)
    def show(self):
        """显示界面"""
        pass
    def OnSubmit(self):
        """响应button事件"""
        pass
    def OnExit(self):
        pass
    def _save(self):
        """保存结果"""
        pass
    def createFig(self):
        f = plt.figure(figsize=(6,6))
        f.clf()
        b = self.datas[100]
        boll_up, boll_mid, boll_low = b
        closes = np.array(range(len(boll_low)))
        closes[:] = np.nan
        judge_boll_sign.drawBoll(plt, closes, boll_up, boll_mid, boll_low)
        return f
    
class FromInput:
    """显示一个图， 输入一段信息"""
    def __init__(self):
        self.datas = pearson_clust.load_data()
        self.createFig()
        plt.show()
    def _show(self):
        pass
    def createFig(self):
        f = plt.figure(figsize=(6,6))
        f.clf()
        b = self.datas[100]
        boll_up, boll_mid, boll_low = b
        closes = np.array(range(len(boll_low)))
        closes[:] = np.nan
        judge_boll_sign.drawBoll(plt, closes, boll_up, boll_mid, boll_low)
        return f    
    
if __name__ == "__main__":
    FromInput()
    print('end')
    desc = input('desc=')
    print(desc)
    