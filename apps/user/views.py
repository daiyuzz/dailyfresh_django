import re

from django.http import HttpResponse

from .models import User
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin
from .models import Address


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
                # 获取登录后需要跳转的url
                next_url = request.GET.get('next', reverse('goods:index'))

                response = redirect(next_url)
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


# /user/logout
class LogoutView(View):
    '''退出登录'''

    def get(self, request):
        logout(request)
        # 清除session
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''

    def get(self, request):
        # request.user
        # 如果用户未登录->AnonymousUser 类的一个实例
        # 如果用户登录-> User类的一个实例
        # request.user.authenticated()
        # 除了你给模板文件传递给模板变量之外，Django框架还会把request.user也传递给模板文件。

        # 获取用户的个人信息

        # 获取用户的历史浏览数据

        return render(request, 'user/user_center_info.html', {'page': 'user'})


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''

    def get(self, request):
        # 获取用户的订单信息

        return render(request, 'user/user_center_order.html', {'page': 'order'})


# /user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''

    def get(self, request):
        # 获取用户的收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request, 'user/user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user/user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user/user_center_site.html', {'errmsg': '手机号码格式不正确'})
        # 业务处理：地址添加
        # 如果用户已经存在默认收货地址，新添加的地址不作为默认收货地址，否则作为默认收货地址
        # try:
        #     address = Address.objects.get(user=request.user, is_default=True)
        # except Address.DoesNotExist:
        #     # 默认收货地址不存在
        #     address = None
        user = request.user
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=request.user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))
        # 这一步重定向到地址页面，之前是post方式，重定向后是get方式，相当于AddressView类的get方法返回到模板页
