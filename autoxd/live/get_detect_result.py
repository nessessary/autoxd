#coding:utf8

"""获取检测结果"""
import subprocess
import os
#import cv2
import pylab as pl
from autoxd import stock, agl
import warnings
import numpy as np

def filter_close(h, l, middle):
    """当在mid上面时用high, 下面时用low
    return c 用合并后的序列作为close
    """
    middle = agl.arrary_fillna(middle)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")	
        return np.where(h>middle, h, l)    

def drawBoll(pl, closes, boll_up, boll_mid, boll_low):
    pl.plot(closes)
    pl.plot(boll_up)
    pl.plot(boll_mid)
    pl.plot(boll_low)

def get_detect_result(img):
    """判断rect at right end
    return : list(int label_index , if none is -1; 
    float right percent)
    """
    # execute and wait 
    #os.system('if exist runs\detect (rmdir /s /q runs\detect)')
    fpath = "run_detect.bat"#runtime
    # for shell
    if not os.path.exists(fpath):
        here = os.path.abspath(__file__)
        fpath = os.path.join(os.path.dirname(here), fpath)
        
    cmd = "%s \"%s\""%(fpath, img)
    print(cmd)
    show_info = subprocess.PIPE

    p = subprocess.Popen(cmd, stdout=show_info)
    p.wait()

    exe_path = r'I:\workc\MyWorkSource\wk\yolo\yolov5\dist\shape_recognition'
    
    exp_path = 'runs/detect'
    label_path = 'labels'
    exp_path = os.path.join(exe_path, exp_path)
    exps = os.listdir(exp_path)
    def mycmp(exp:str):
        exp = exp.replace('exp','')
        if exp == '':
            return 0
        return int(exp)
    exps = sorted(exps, key=mycmp)
    #print(exps)    
    exp = exps[-1]
    img_path = os.path.basename(img).split('.')[0]
    img_path += '.txt'
    label_path = os.path.join(exp_path, exp, label_path, img_path)
    #print(label_path)
    
    rcs = []
    if os.path.exists(label_path):
        with open(label_path, 'r') as f:
            lines = f.readlines()
            #img = cv2.imread(img)
            #img_h,img_w = img.shape[:2]
            for line in lines:
                line = line.replace('\n','')
                label, l,t, w, h = line.split(' ')
                right_percent = float(l)+float(w)
                rcs.append((int(label), right_percent))
                # percent to pixel
                #l = int(img_w*float(l) - img_w*float(w)/2)
                #t = int(img_h*float(t) - img_h*float(h)/2)
                #w = int(img_w*float(w))+1
                #h = int(img_h*float(h))+1
                #rc = [l,t, l+w, t+h]
                #rcs.append(rc)
                
    #os.system('if exist runs\detect (rmdir /s /q runs\detect)')
    return rcs


def gen_img(code, df):
    """df to img, save file
    df: five
    return path(str)
    """
    #assert(len(df) == 100)
    i = 0
    n = 100
    save_path = 'five_img'
    agl.createDir(save_path)
    
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)
    
    pl.figure()
    drawBoll(pl, filter_close(df['h'].values[i:i+n], df['l'].values[i:i+n], middle[i:i+n]),\
                upper[i:i+n], middle[i:i+n], lower[i:i+n])
    #pl.show()
    fname = os.path.join(save_path, code + "_"+str(i)+".png")
    pl.savefig(fname)
    pl.close()
    fname = os.path.abspath(fname)
    
    return fname

def detect(code, df):
    """return: list result"""
    fpath = gen_img(code, df)
    r = get_detect_result(fpath)
    return r

def test():
    from autoxd.pinyin import stock_pinyin3 as jx
    from autoxd import warp_pytdx as tdx
    code = jx.TYXJ天岳先进
    df = tdx.getFive(code, 800)
    detect_path = r'I:\workc\MyWorkSource\wk\yolo\yolov5\dist\shape_recognition\runs\detect'
    os.system('if exist %s (rmdir /s /q %s)'%(detect_path, detect_path))
    for i in range(0,800,100):
        print(detect(code, df[i:i+100]))

    os.system('start %s'%r'I:\workc\MyWorkSource\wk\yolo\yolov5\dist\shape_recognition\runs')
    
if __name__ == "__main__":
    #print(get_detect_result(r'I:\workc\MyWorkSource\wk\yolo\datasets\autoxd-ai\test\000417_519.png'))
    test()