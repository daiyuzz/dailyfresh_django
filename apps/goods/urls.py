from django.conf.urls import url
from . import views
app_name = 'goods'

urlpatterns = [
    url(r'^$',views.index,name='index') # 首页
]