from django.conf.urls import url

from apps.cart.views import CartAddView, CartInfoView, CartUpdateView

app_name = 'cart'

urlpatterns = [
    url(r'^add$', CartAddView.as_view(), name='add'),  # 购物车记录添加
    url(r'^$', CartInfoView.as_view(), name='show'),  # 购物车页面
    url(r'^update', CartUpdateView.as_view(), name='update'),  # 购物车记录更新

]
