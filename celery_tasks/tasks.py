# 使用celery

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 创建一个celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

# 在任务处理者上加上下面四行代码，Django环境的初始化
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 发邮件
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面的链接激活您的账户<br><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        username, token, token)

    from_email = settings.EMAIL_FROM
    receiver = [to_email]
    # message中有html时，使用html_message。
    send_mail(subject, message, from_email, receiver, html_message=html_message)
