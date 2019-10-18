from django.conf.urls import url

from apps.user.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView

from django.contrib.auth.decorators import login_required

app_name = 'user'

urlpatterns = [
    url(r'^register/', RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login/', LoginView.as_view(), name='login'),

    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户中心-信息页
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户中心-订单页面
    # url(r'^address$', login_required(AddressView.as_view()), name='address'),  # 用户中心-地址页面

    url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    url(r'^order$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页面
    url(r'^address$', AddressView.as_view(), name='address'),  # 用户中心-地址页面
]
