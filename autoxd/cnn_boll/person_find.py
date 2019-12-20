#coding:utf-8

"""输入线段， 用person匹配出结果, 参考pattern_recognition里的实现"""
from __future__ import print_function
import requests
import json
import datetime
import md5
import agl

#url = 'http://www.jiwunote.com.cn/seepic/pptv_pc_sdk/test_post.php'
#data = {'a':1}
#r = requests.post(url, data)
#print r.text
#url = 'http://www.jiwunote.com.cn/seepic/pptv_pc_sdk/test_json.php'
#data = {'a':1}
#r = requests.post(url, None, json.dumps(data))
#print r.text

#测试ott
#url = "https://coapigxpre.cnsuning.com/";
#//MyRequest::Post(params, "", pOutResult, nLen);
#CStringA params;
#CStringA appMethod = "pptv.channel.status.get";
#CStringA t = GetTime();
#CStringA appkey = "834724edf902d894a23b9e1caeb31d7d";
#CStringA Appsecret = "d23b22e90af7b0e050ebb344dee98f0a";
#//Appsecret+ appMethod+ appTime+ appKey+ base64Str(requestbody)
#CStringA siginfo = Appsecret + appMethod + t + appkey;
#params.Format("appMethod=%s&appKey=%s&appRequestTime=%s&signInfo=%s", appMethod, appkey, t, siginfo);
#string strResult;
#MyRequest::Post(url, (const char*)params, strResult);

url = "https://coapigxpre.cnsuning.com/coapi-web/api/http/sopRequest"
appMethod = "pptv.channel.status.get"
appTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
appTime = "2019-05-14 16:13:44"
appkey = "834724edf902d894a23b9e1caeb31d7d"
Appsecret = "d23b22e90af7b0e050ebb344dee98f0a"
siginfo =  Appsecret + appMethod + appTime + appkey
print("siginfo=",siginfo)
siginfo = agl.MD5(siginfo)
print("md5(signinfo)=",siginfo)
data = {"appMethod": appMethod, "appRequestTime":appTime, "appKey":appkey, "signInfo":siginfo}
r = requests.post(url,headers= data)
print(r.text)
#r = requests.post(url, None, json.dumps(data))x
#print r.text

def getChannelId(respone) :
    j = json.loads(respone)
    return j['response']['body']['data']['channelId']
    
print(getChannelId(r.text))