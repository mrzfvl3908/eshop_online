from django.contrib import admin

from .models import (
    Product,
    Color,
    Size,
    Category,
    Review,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'price',
        'discount',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'category',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
    )

    prepopulated_fields = {
        'slug': ('title',)
    }

    filter_horizontal = (
        'category',
        'size',
        'color',
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'user',
        'rating',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'rating',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'product__title',
        'user__username',
        'comment',
    )

    ordering = (
        '-created_at',
    )


admin.site.register(Color)
admin.site.register(Size)
admin.site.register(Category)