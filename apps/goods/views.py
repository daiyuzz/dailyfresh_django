from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.views.generic import View
from django.core.cache import cache
from apps.goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection
from apps.order.models import OrderGoods


# Create your views here.

class IndexView(View):
    '''首页'''

    def get(self, request):
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            print('开始缓存数据')
            # 缓存中没有数据
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

            # 设置缓存
            # key,value,timeout
            cache.set('index_page_data', context, 3600)
        # 获取用户购物车中商品的数目
        user = request.user
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        else:
            # 用户未登录
            cart_count = 0
        context.update(cart_count=cart_count)
        return render(request, 'goods/index.html', context=context)


# goods/goods_id
class DetailView(View):
    '''详情页'''

    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在,跳转首页
            return redirect(reverse('goods:index'))
        # 获取商品的分类信息
        types = GoodsType.objects.all()
        # 　获取商品的评论信息（exclude返回不满足的结果）
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(commet='')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')

        # 获取用户购物车中商品的数目
        user = request.user
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        else:
            # 用户未登录
            cart_count = 0

        # 组织模板上下文
        context = {
            'sku': sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'cart_count': cart_count,
        }

        return render(request, 'goods/detail.html', context=context)
