from ctypes import *
import cv2
import numpy as np
import numpy.ctypeslib as npct

class Detector():
    def __init__(self,model_path,dll_path):
        try:
            self.yolov8 = CDLL(dll_path, winmode=0)# 高版本只能从可信位置加载dll
        except:
            self.yolov8 = CDLL(dll_path)
        
        self.yolov8.Detect.argtypes = [c_void_p,c_int,c_int,POINTER(c_ubyte),npct.ndpointer(dtype = np.float32, ndim = 2, shape = (100, 6), flags="C_CONTIGUOUS")]
        self.yolov8.Init.restype = c_void_p
        self.yolov8.Init.argtypes = [c_void_p]
        self.c_point = self.yolov8.Init(model_path)

    def predict(self,img):
        rows, cols = img.shape[0], img.shape[1]
        res_arr = np.zeros((100,6),dtype=np.float32)
        self.yolov8.Detect(self.c_point,c_int(rows), c_int(cols), img.ctypes.data_as(POINTER(c_ubyte)),res_arr)
        self.bbox_array = res_arr[~(res_arr==0).all(1)]
        return self.bbox_array

def visualize(img,bbox_array):
    for temp in bbox_array:
        bbox = [temp[0],temp[1],temp[2],temp[3]]  #xywh
        cls = int(temp[4])
        score = temp[5]
        print(cls, score)
        cv2.rectangle(img,(int(temp[0]),int(temp[1])),(int(temp[0]+temp[2]),int(temp[1]+temp[3])), (105, 237, 249), 2)
        img = cv2.putText(img, "class:"+str(cls)+" "+str(round(score,2)), (int(temp[0]),int(temp[1])-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (105, 237, 249), 1)
    return img

def test():
    
    det = Detector(model_path=b"./best.trt",dll_path="./yolov8.dll")  # b'' is needed
    img = cv2.imread("I:\\workc\\MyWorkSource\\wk\\seepic\\seecomic_ocr\\ocr\\easyocr_impl\\yolo_colordetect\\colordetect\\images\\collet389.png")
    result = det.predict(img)
    img = visualize(img,result)
    cv2.imshow("img",img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test()