from django.contrib import admin

# Register your models here.

from .models import Dreamreal,Login


admin.site.register(Dreamreal)
admin.site.register(Login)
admin.site.register(Product)
admin.site.register(ProductDetail)
admin.site.register(Store)
admin.site.register(Category)