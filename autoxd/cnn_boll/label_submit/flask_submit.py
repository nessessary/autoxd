#coding:utf8
import os
from flask import Flask, request, render_template, Response, send_file, jsonify

app = Flask(__name__)
@app.route('/')
def index():
    #return 'Hello World'
    return render_template('index.html')

@app.route('/greeting', methods = ["POST"])
def greeting():
    POST_name = request.form["name"]
    labels = "null"
    print(request.form.keys())
    if "labels" in request.form.keys():    
        labels = request.form["labels"]
    return render_template("greeting.html", name = POST_name, labels=labels)

@app.route('/api', methods = ["GET"])
def handle_ajax_submit():
    form = dict(request.args)
    values = form.keys()
    values = str(form.values())
    print(values)
    json = {"msg":"ok", "result":values}
    return jsonify(json)

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