#coding:utf8

"""用smtp第三方邮箱发送邮件
qq邮箱的手机通知只显示标题， 因此内容不用写
"""

import smtplib, os
from email.header import Header
from email.mime.text import MIMEText
import json
from autoxd.cnn_boll.env import get_root_path

class email:
    def __init__(self, host, name, pwd):
        self.host = host
        self.name = name
        self.pwd = pwd


def load_user_info():
    """json [user,pwd]"""
    fname = os.path.abspath(get_root_path()+'/../notify/'+'info.json')
    f = open(fname, 'r')
    t = str(f.read())
    f.close()
    t = t.replace('\t','')
    t = t.replace('\n', '')
    return json.loads(t)
    
def MySend():
    """使用sendmail发送, 有密码的话使用第三方发送"""
    smtp, user,pwd,toemail = load_user_info()
    source = email(smtp, user, pwd)
    dest = email(host='', name=toemail, pwd='')
    content = 'aaa__________'
    title = '计算完成123'  # 邮件主题    
    #163需要登录web后才能发送成功
    send_email2(source.host, source.name, source.pwd, dest.name, title, content)
    
def sendEmail():

    message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
    message['From'] = "{}".format(sender)
    message['To'] = ",".join(receivers)
    message['Subject'] = title

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
        smtpObj.login(mail_user, mail_pass)  # 登录验证
        smtpObj.sendmail(sender, receivers, message.as_string())  # 发送
        print("mail has been send successfully.")
    except smtplib.SMTPException as e:
        print(e)

def send_email2(SMTP_host, from_account, from_passwd, to_account, subject, content):
    email_client = smtplib.SMTP(SMTP_host)
    if from_passwd != "":
        email_client.login(from_account, from_passwd)
    # create msg
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')  # subject
    msg['From'] = from_account
    msg['To'] = to_account
    email_client.sendmail(from_account, to_account, msg.as_string())

    email_client.quit()
    
if __name__ == "__main__":
    MySend()