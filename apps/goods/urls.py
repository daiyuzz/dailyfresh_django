from django.conf.urls import url
from apps.goods.views import IndexView, DetailView

app_name = 'goods'

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),  # 首页
    url(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail')  # 详情页
]
