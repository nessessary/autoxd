#coding:utf8

"""获取检测结果
v5的废弃，只用v8的，且用zmq方式传递
"""
import subprocess
import os
import pylab as pl
from autoxd import stock, agl
import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import cv2
import io
import PIL
import PIL.Image as Image
import zmq, pickle

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

def fig_to_numpy():
    canvas = FigureCanvasAgg(plt.gcf())
    canvas.draw()
    img = np.array(canvas.renderer.buffer_rgba())
    img = img[:, :, :3]
    #r = img[:, :, 0]
    #b = img[:, :, -1]
    #img[:, :, 0] = b
    #img[:, :, -1] = r
    
    # 重构成w h 4(argb)图像
    #buf = img
    #w, h = canvas.get_width_height()
    #buf.shape = (w, h, 4)
    ## 转换为 RGBA
    #buf = np.roll(buf, 3, axis=2)
    ## 得到 Image RGBA图像对象 (需要Image对象的同学到此为止就可以了)
    #image = Image.frombytes("RGBA", (w, h), buf.tostring())
    ## 转换为numpy array rgba四通道数组
    #image = np.asarray(image)
    ## 转换为rgb图像
    #rgb_image = image[:, :, :3]
    #img = rgb_image
    
    #print(img)
    return img

def fig_to_numpy2():
    buffer_ = io.BytesIO()
    plt.savefig(buffer_,format = 'png')
    
    #从内存读取,转换为array,通过opencv显示
    dataPIL = PIL.Image.open(buffer_)
    data = np.asarray(dataPIL)
    #释放缓存
    plt.close()
    buffer_.close()
    
    
    
    return data

def fig_to_numpy3(fig):
    fig.canvas.draw()
    buf = fig.canvas.tostring_rgb()
    ncols, nrows = fig.canvas.get_width_height()
    #print("to verify, our resolution is: ",ncols,nrows)
    return np.frombuffer(buf, dtype=np.uint8).reshape(nrows, ncols, 3)
    
    
def gen_nparray(df):
    fig = pl.figure()

    drawBoll(pl, filter_close(df['h'].values, df['l'].values, df['middle'].values),\
                df['upper'].values, df['middle'].values, df['lower'].values)
    #pl.show()
    r = fig_to_numpy3(fig)
    pl.close()
    return r
    #return fig_to_numpy()

g_zmq = None
def zmq_init():
    global g_zmq
    if g_zmq is None:
        context = zmq.Context()
        #print("Connecting to hello world server...")
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5555")
        socket: zmq.context.Socket
        #socket.setsockopt(zmq.Rcv)
        g_zmq = socket
        
    return g_zmq
        
    
def zmq_detect(df):
    img = gen_nparray(df)
    g_zmq = zmq_init()
    g_zmq : zmq.socket.Socket
    #g_zmq.send_string(pickle.dumps(img))
    g_zmq.send_pyobj(img)
    
    result = g_zmq.recv_pyobj()
    return result

def zmq_close():
    g_zmq.send_pyobj('close')
    
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
    
def testV8():
    from autoxd.pinyin import stock_pinyin3 as jx
    from autoxd import warp_pytdx as tdx
    code = jx.TYXJ天岳先进
    df = tdx.getFive(code, 800)
    upper, middle, lower = stock.TDX_BOLL(df['c'].values)
    df['upper'] = upper
    df['middle'] = middle
    df['lower'] = lower
    
    def myshow():
        
        img = gen_nparray(df[200:200+100])
        print(img.shape)
    
        pl.close()
        pl.figure()    
        pl.imshow(img)
        pl.show()    
        
        #cv2.imshow('win', img)
        #cv2.waitKey(0)
        
    def send_zmq():
       r = zmq_detect(df)
       print(r)
       
    send_zmq()
    g_zmq.send_pyobj('close')
    
if __name__ == "__main__":
    #print(get_detect_result(r'I:\workc\MyWorkSource\wk\yolo\datasets\autoxd-ai\test\000417_519.png'))
    testV8()
