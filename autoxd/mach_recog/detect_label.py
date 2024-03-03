#coding:utf8

import os
from autoxd.mach_recog.trt_detect import Detector
from autoxd.agl import LOG

def visualize(img,bbox_array):

    LOG("---")
    cls = None
    for temp in bbox_array:
        bbox = [temp[0],temp[1],temp[2],temp[3]]  #xywh
        cls = int(temp[4])
        score = temp[5]
        LOG((bbox[1] + bbox[3]) / 640)
        # right < 20%
        #if (bbox[1] + bbox[3]) / 640 < 0.8:
            #return None
        #print(cls, score)
    return cls
        #cv2.rectangle(img,(int(temp[0]),int(temp[1])),(int(temp[0]+temp[2]),int(temp[1]+temp[3])), (105, 237, 249), 2)
        #img = cv2.putText(img, "class:"+str(cls)+" "+str(round(score,2)), (int(temp[0]),int(temp[1])-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (105, 237, 249), 1)
    return None

g_det = None
def get_Label(image):
    """image: ndarray'
    return: None or str(u1|d1) """
    global g_det
    if g_det is None:
        dll_path = r'I:\workc\MyWorkSource\wk\seepic\seecomic_ocr\ocr\easyocr_impl\yolo_colordetect\YOLOv8_Tensorrt-master\build\Release\yolov8.dll'
        assert os.path.exists(dll_path)
        trt_path = r'I:\workc\MyWorkSource\wk\deepl_work\stock\yolo\best.trt'
        model_path = bytes(trt_path,encoding='utf-8')
        g_det = Detector(model_path=model_path,dll_path=dll_path)  # b'' is needed
    result = g_det.predict(image)

    label = visualize(image,result)
    if label is not None:
        names = ['d1','u1']
        return names[label]
    #assert False
    return None
    #cv2.imshow("img",img)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    
if __name__ == "__main__":
    image = r'I:\workc\MyWorkSource\wk\deepl_work\stock\yolo\datasets\autoxd-ai2\images\000001_119.png'
    #image = "I:\\workc\\MyWorkSource\\wk\\seepic\\seecomic_ocr\\ocr\\easyocr_impl\\yolo_colordetect\\colordetect\\images\\collet389.png"
    import cv2
    image = cv2.imread(image)
    l = get_Label(image)
    print(l)