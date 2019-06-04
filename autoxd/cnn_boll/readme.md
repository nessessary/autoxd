
##依赖

*  安装PCV，在pkg/PCV-master

##用pearson来对图形聚类
	1) 在矢量状态（时间序列）进行pearson计算， 计算的结果作为knn的距离， 最后用knn来聚类
	2) 读取数据， 以n分钟作为间隔， 生成数据， 数据进行pearson比较， knn分类， 分类结果输出到目录中
	3) 对up，down， mid分别计算, 或只对up，down做计算

##人工打标签
1. 读取数据源， datas， 创建img到img_labels/imgs
```python
	python judge_boll_sign.py -n --nohead
```
	-n 为自动化构建, 否则为人工判断

2. 谱聚类, cluster_img.py

3. knn聚类, ch6_julei_alpha2.py


##一些尝试性的想法
还是使用人工进行识别， 监督学习

不能简单的识别最后的开口， 需要识别为大小大这样的模式, 共8种

摒弃硬编码判断的方式
是否可以尝试用person替换shift的计算来进行聚类

辅助的判断，使用直接计算
- 先用zz对boll_up进行计算， 获得上升(周期,角度)(x,y) tanA=y/x
- 使用person判断曲线
	