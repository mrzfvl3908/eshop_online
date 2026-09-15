from product_app.models import Category

from .cart import get_cart_count


def shop_context(request):

    return {
        'cart_count': get_cart_count(request),

        'header_categories': (
            Category.objects
            .order_by('name')
        ),
    }