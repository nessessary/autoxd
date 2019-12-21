#coding:utf8

"""手工设置标签的页面实现， 先跑pearson_clust.py里的genimg"""

import os
from flask import Flask, request, render_template, Response, send_file, jsonify
#import labels as mylabel    #与route的方法冲突
import labels
from autoxd.cnn_boll.pearson_clust import MyCode

app = Flask(__name__)
@app.route('/')
def index():
    #return 'Hello World'
    return render_template('index.html')

@app.route('/api', methods = ["GET"])
def handle_ajax_submit():
    """保存结果"""
    new_label = None
    str_labels = None
    if 'new_label' in request.args.keys():
        new_label = request.args['new_label']
        
    if 'labels' in request.args.keys():
        str_labels = request.args['labels']
        print(str_labels)
    
    index = int(request.args['index'])
    canContinue = labels.save_labels(new_label, str_labels, index)
    print(index, canContinue)    
    #看是不是执行到表的结尾了
    json = {"msg": canContinue}
    return jsonify(json)

@app.route('/labels', methods=["GET"])
def get_labels():
    obj_label = labels.LabelTable()
    list_label = obj_label.query()
    result = ','.join(list_label)
    return Response(result)

@app.route("/image/<imageid>")
def get_img(imageid):
    """ 传入主id， 显示用数据id
    img_labels/imgs/code_index.png
    实现见pearson_clust.py:myhclust
    """
    imageid = int(imageid)
    df = labels.get_data_table()
    imageid = int(df.iloc[imageid]['datas_index'])
    cur_path = os.path.abspath(os.path.dirname(__file__)+'/..')
    code = MyCode.get() #使用genimg设置的code from redis
    fname = cur_path + "/%s/%s_%d.png"%('img_labels/imgs', code, imageid)
    print(fname)
    #image = file(fname)
    #resp = Response(image, mimetype="image/png")
    return send_file(fname, mimetype="image/png")

if __name__ == '__main__':
    #app.debug = True # 设置调试模式，生产模式的时候要关掉debug
    app.run()