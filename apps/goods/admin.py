from django.contrib import admin
from apps.goods.models import GoodsType,IndexPromotionBanner
# Register your models here.

class IndexPromotionBannerAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或更新表中数据时调用'''

admin.site.register(GoodsType)
admin.site.register(IndexPromotionBanner)