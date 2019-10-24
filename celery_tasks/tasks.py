# 使用celery

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django_redis import get_redis_connection
from django.template import loader,RequestContext
# 创建一个celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://106.12.78.90:6379/8')

# 在任务处理者上加上下面四行代码，Django环境的初始化
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


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


@app.task
def generate_static_index_html():
    '''产生首页静态页'''
    # 获取商品的种类信息
    types = GoodsType.objects.all()
    # 获取首页轮播图信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    # 获取首页促销信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners
    # image_banners和title_banners属性会随着types一起传递

    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners,
    }

    # 使用模板
    # 1.加载模板
    temp = loader.get_template('goods/static_index.html')
    # 2.定义模板上下文
    # context = RequestContext(request,context)
    # 3.模板渲染
    static_index_html = temp.render(context)
    # 生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR,'static/goods/index.html')
    with open(save_path,'w') as f:
        f.write(static_index_html)

