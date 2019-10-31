from django.conf.urls import url
from . import views
from apps.cart.views import CartAddView

app_name = 'user'

urlpatterns = [
    url(r'^add$', CartAddView.as_view(), name='add')  # 购物车记录添加
]
