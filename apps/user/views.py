import re

from django.http import HttpResponse

from .models import User
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.contrib.auth import authenticate, login
from celery_tasks.tasks import send_register_active_email


# Create your views here.


class RegisterView(View):
    """注册类"""

    def get(self, request):
        return render(request, 'user/register.html')

    def post(self, request):
        """进行注册处理"""
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})
        if password != password2:
            return render(request, 'user/register.html', {'errmsg': '两次密码不一致'})
        if not re.match(r'[a-z0-9][\w.-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 校验用户是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'user/register.html', {'errmsg': '用户已存在'})

        # 进行业务处理：注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接 http://127.0.0.1:8000/user/active/1
        # 激活链接中需要包含用户的身份信息,并且要把身份信息进行加密,使用itsdangerous进行加密
        # 加密用户身份信息，生成激活ｔｏｋｅｎ
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        # 加密之后是字节类型，需要编码为utf-8，decode默认为utf-8，所以可直接写为token.decode()
        token = token.decode('utf-8')
        # 发邮件
        # send_register_active_email由app.task修饰，使其有delay属性
        send_register_active_email.delay(email, username, token)

        return redirect(reverse('goods:index'))


# 激活的类
class ActiveView(View):
    '''用户激活'''

    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取激活所需要的信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到首页
            return redirect(reverse('goods:index'))
        except SignatureExpired as e:
            # 激活链已经过期
            return HttpResponse('激活链接已经过期')


class LoginView(View):
    '''登录视图类'''

    def get(self, request):
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'user/login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登录校验'''
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username, password]):
            return render(request, 'user/login.html', {'errmsg': '数据不完整'})
        # 业务处理:登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # 用户已激活
                # 保存用户的登录状态
                login(request, user)
                # 跳转首页
                response = redirect(reverse('goods:index'))
                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')
                # 返回response
                return response
            else:
                # 用户未激活
                return render(request, 'user/login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'user/login.html', {'errmsg': '用户名或密码错误'})


# /user
class UserInfoView(View):
    '''用户中心-信息页'''

    def get(self, request):
        page = 'user'
        return render(request, 'user/user_center_info.html',{'page':page})

# /user/order
class UserOrderView(View):
    '''用户中心-订单页'''

    def get(self, request):
        page = 'order'
        return render(request, 'user/user_center_order.html',{'page':page})

# /user/address
class AddressView(View):
    '''用户中心-地址页'''

    def get(self, request):
        page = 'address'
        return render(request, 'user/user_center_site.html',{'page':page})
