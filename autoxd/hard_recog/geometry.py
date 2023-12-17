#-*- coding:utf-8 -*-

"""
处理几何计算
"""
import numpy as np
import cmath
import sys
#import help

########################################################################
class enum:
    """"""
    ANGLE_LEFT=-1
    ANGLE_RIGHT = 1

    #----------------------------------------------------------------------
    def __init__(self, v):
        """Constructor"""
        if v == self.ANGLE_LEFT:
            print("left")
        if v == self.ANGLE_RIGHT:
            print("right")
    
    
#
#----------------------------------------------------------------------
def CutOff(v):
    """"""
    if v>100: v=100
    if v<-100: v=-100
    return v
    
#----------------------------------------------------------------------
def getTwoPointDistance(pt1, pt2):
    """
    用勾股定理得到两点距离
    pt1: 点坐标[x,y]
    pt2: 另一个点
    return : 长度int(d)
    """
    
    x = (abs(pt1[0]-pt2[0]))**2 + (abs(pt1[1]-pt2[1]))**2
    return abs(cmath.sqrt(x))
    
#
#----------------------------------------------------------------------
def getTriangleArea(pts):
    """
    得到三角形面积
    pts: (3,2) 3个坐标点
    return : area
    """
    #取各边长度
    d = []
    for i in range(0, len(pts)):
        pt1 = pts[i]
        t = i+1
        if i == len(pts)-1:
            t=0
        pt2 = pts[t]
        d.append(getTwoPointDistance(pt1, pt2))
        
    #用海伦公式计算
    p = (d[0] + d[1] + d[2]) / 2
    x = p * (p-d[0]) * (p-d[1])*(p-d[2])
    s = cmath.sqrt(x)
    return abs(s)
    
#----------------------------------------------------------------------
def getFourPointArea(pts):
    """
    计算坐标上4个点的面积
    pts: (4,2) 4个坐标点 左上，右上， 左下，右下 , 如果顺序输入错误， 会引起计算错误
    return : area面积
    """
    
    pts1 = [pts[0],pts[1],pts[2]]
    pts2 = [pts[3],pts[1],pts[2]]
    s = getTriangleArea(pts1) + getTriangleArea(pts2)
    return s
    
    
def comput_intersec(line1, line2):
    """
    计算直线交点，直线为结构体，内容为两个节点信息
    line1 : (2, 2)  martix  第一根线
    line2 : (2,2) martix 第二根线
    return : [px, py]   交点坐标
    """
    p1 = line1[0]; p2 = line1[1]; # 第1条边的两点
    p3 = line2[0]; p4 = line2[1]; #第2条边的两点
    x1 = p1[0]; y1 = p1[1];
    x2 = p2[0]; y2 = p2[1];
    x3 = p3[0]; y3 = p3[1];
    x4 = p4[0]; y4 = p4[1];
    # 计算交点
    px = (x1*x3*y2 - x2*x3*y1 - x1*x4*y2 + x2*x4*y1 - x1*x3*y4 + x1*x4*y3 + x2*x3*y4 - x2*x4*y3 )/\
        (x1*y3 - x3*y1 - x1*y4 - x2*y3 + x3*y2 + x4*y1 + x2*y4 - x4*y2);
    py =  (x1*y2*y3 - x2*y1*y3 - x1*y2*y4 + x2*y1*y4 - x3*y1*y4 + x4*y1*y3 + x3*y2*y4 - x4*y2*y3 )/\
            (x1*y3 - x3*y1 - x1*y4 - x2*y3 + x3*y2 + x4*y1 + x2*y4 - x4*y2);
    return [px, py]

#----------------------------------------------------------------------
def getTwoLineAngle(l):
    """
    得到两根直线之间的夹角
    l(4,2) [table  4*2] 矩阵  l1,l3为靠近夹角的点
    return: [a, b] a角度， d方向 (1/-1) 1为夹角在右边， -1为夹角在左边
    """
    assert(len(l)==4)
    [x2,y2] = comput_intersec(l[0:2],l[2:4]);
    #判断夹角的方向
    b = 1
    if x2<=l[2,0]:
        x1=l[1,0]; y1=l[1,1];
        x3=l[3,0]; y3=l[3,1];
        b = enum.ANGLE_LEFT
    else:
        x1=l[0,0];y1=l[0,1];
        x3=l[2,0];y3=l[2,1];
        b = enum.ANGLE_RIGHT
    a = cmath.acos(np.dot([x1-x2,y1-y2],[x3-x2,y3-y2])/\
        (np.linalg.norm([x1-x2,y1-y2]) * np.linalg.norm([x1-x2,y3-y2]))) ;
    a = abs(a*180/cmath.pi)
    return [a, b]
        
#
#----------------------------------------------------------------------
def IsPointAtLineUp(pt, l):
    """
    判断点是否在直线的上面
    pt : [x,y]  点坐标
    l : [l1,l2] 一根线
    return : True/False Up/Down
    """
    x1=abs(l[0,0]-l[1,0]);
    y1=abs(l[0,1]-l[1,1]);
    x2=abs(pt[0]-l[0,0]);
    y2=y1*x2/x1;
    # pt在下降线x1的左边
    if l[1,1]-l[0,1]<0 and pt[0]<l[0,0]:
        y2=l[0,1]+y2;
    # pt在上升线X1的右边
    elif (l[1,1]-l[0,1])>0 and pt[0]>l[0,0]:
        y2=l[0,1]+y2;
    else:
        y2=l[0,1]-y2;
    up = pt[1] - y2;
    if up > 0:
        return True
    return False
    
#----------------------------------------------------------------------
def Unittest():
    """"""

    #子目录引用， 目录就是包， 用from来引用    
    #a = strategy.MyTest()
    
    
    #测试夹角计算
    l = np.array([[0,23], [29,28.4], [11, 23.31], [82,19.45]])
    [a, b] = getTwoLineAngle(l)
    print(a)
    l = np.array([[20,40], [30,30], [20, 20], [30,20]])
    [a, b] = getTwoLineAngle(l)
    print(a, enum(b))
    l = np.array([[20,50], [30,30], [20, 20], [30,20]])
    [a, b] = getTwoLineAngle(l)
    print(l, a, enum(b))
    l = np.array([[0,23], [29,28], [0, 23], [11,22]])
    [a, b] = getTwoLineAngle(l)
    print(l, a, enum(b))
    l = np.array([[2,3], [0,3], [2,3], [4,5]])
    [a, b] = getTwoLineAngle(l)
    print(l, a, enum(b))
    
    
    #测试点是在线的上面还是在下面
    pt = [20,30]
    l = np.array([[20,20],[30,20]])
    print(IsPointAtLineUp(pt, l))
    
    pt = [20,10]
    l = np.array([[20,20],[30,20]])
    print(IsPointAtLineUp(pt, l))
    pt = [25,21]
    l = np.array([[20,30],[30,10]])
    print(IsPointAtLineUp(pt, l))
    pt = [82,19]
    l = np.array([[34,22],[103,21]])
    print(IsPointAtLineUp(pt, l))
    
    #测试两点距离计算
    pt1=[20,30]; pt2=[20,40];
    d = getTwoPointDistance(pt1, pt2)
    #help.print2("测试距离",pt1,pt2, abs(d))
    
    pts = [[0,2], [2,4], [6,2]]
    s = getTriangleArea(pts)
    #help.print2("获取三角形面积", pts, s)

    pts = [[10,10], [100,10], [50,50]]
    s = getTriangleArea(pts)
    #help.print2("获取三角形面积", pts, s)
    
    pts = [[10,10], [10,20], [0,10],[0,20]]
    s = getFourPointArea(pts)
    #help.print2("获取四边形面积", pts, s)

    pts = [[2,4], [6,2],[0,2], [1,0], ]
    s = getFourPointArea(pts)
    #help.print2("获取四边形面积", pts, s)
    
        
def main(args):
    Unittest()
    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)