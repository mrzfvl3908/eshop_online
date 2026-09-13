from django.contrib import admin
from .models import Color,Products,Size


class ProductsAdmin(admin.ModelAdmin):
    list_display = ['title','price','discount','created_at']
    list_filter = ['title']
    search_fields = ['title','description','created_at','price']


admin.site.register(Products,ProductsAdmin)
admin.site.register(Color)
admin.site.register(Size)

