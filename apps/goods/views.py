from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django.core.cache import cache
from django.core.paginator import Paginator
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
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取用户购物车中商品的数目
        user = request.user
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户历史浏览记录
            conn = get_redis_connection('default')
            history_key = 'hostory_%d' % user.id
            # 移除列表中的goods_id,
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id插入列表中（左侧插入）
            conn.lpush(history_key, goods_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)

        else:
            # 用户未登录
            cart_count = 0

        # 组织模板上下文
        context = {
            'sku': sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'same_spu_skus': same_spu_skus,
            'cart_count': cart_count,
        }

        return render(request, 'goods/detail.html', context=context)


# 种类id、页码、排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式
class ListView(View):
    '''；列表页'''

    def get(selfj, request, type_id, page):
        # 先获取种类的信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在
            return redirect(reverse('goods:index'))
        # 获取排序的方式
        # sort=default按照默认方式排序，
        # sort = price，按照价格排序
        # sort = hot，按照销量排序
        sort = request.GET.get('sort')
        page = request.GET.get('page')

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')

        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')

        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 获取商品分类信息
        types = GoodsType.objects.all().order_by('id')
        # 对数据进行分页
        paginator = Paginator(skus, 1)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的实例对象
        skus_page = paginator.page(page)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购物车中商品的数目
        user = request.user
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        else:
            cart_count = 0

        # 组织模板上下文
        context = {
            'type': type,
            'types': types,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'sort': sort,
        }

        return render(request, 'goods/list.html')
