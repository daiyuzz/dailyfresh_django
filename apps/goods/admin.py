from django.contrib import admin
from django.core.cache import cache
from apps.goods.models import GoodsType, IndexPromotionBanner, IndexTypeGoodsBanner, IndexGoodsBanner,GoodsSKU,Goods


# Register your models here.

class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或更新表中数据时调用'''
        super().save_model(request, obj, form, change)
        from celery_tasks.tasks import generate_static_index_html
        # 发出任务让celery worker重新生成首页静态页
        generate_static_index_html.delay()
        # 清除首页的缓存存储
        cache.delete('index_page_data')


    def delete_model(self, request, obj):
        '''删除表中的数据时调用'''
        super().delete_model(request.obj)
        from celery_tasks.tasks import generate_static_index_html
        # 发出任务，让celery work重新生成首页静态页
        generate_static_index_html.delay()
        # 清除缓存
        cache.delete('index_page_data')


# class GoodsTypeAdmin(BaseModelAdmin):
#     pass
#
#
# class IndexGoodsBannerAdmin(BaseModelAdmin):
#     pass
#
#
# class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
#     pass
#
#
# class IndexPromotionBannerAdmin(BaseModelAdmin):
#     pass


# admin.site.register(GoodsType, GoodsTypeAdmin)
# admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
# admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
# admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(IndexGoodsBanner, BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseModelAdmin)
admin.site.register(IndexPromotionBanner, BaseModelAdmin)
admin.site.register(GoodsSKU)
admin.site.register(Goods)