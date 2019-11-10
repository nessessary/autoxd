#coding:utf8
import os
from flask import Flask, request, render_template, Response, send_file, jsonify
#import labels as mylabel    #与route的方法冲突
import labels

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
    
    index = request.args['index']
    labels.save_labels(new_label, str_labels, index)
        
    json = {"msg":"ok"}
    return jsonify(json)

@app.route('/labels', methods=["GET"])
def get_labels():
    obj_label = labels.LabelTable()
    list_label = obj_label.query()
    result = ','.join(list_label)
    return Response(result)

@app.route("/image/<imageid>")
def get_img(imageid):
    cur_path = os.path.abspath(os.path.dirname(__file__)+'/..')
    fname = cur_path + "/%s/000005_%s.png"%('img_labels/imgs', imageid)
    print(fname)
    #image = file(fname)
    #resp = Response(image, mimetype="image/png")
    return send_file(fname, mimetype="image/png")

if __name__ == '__main__':
    #app.debug = True # 设置调试模式，生产模式的时候要关掉debug
    app.run()