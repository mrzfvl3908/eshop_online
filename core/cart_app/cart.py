from product_app.models import Product

CART_SESSION_KEY = 'cart'


def get_cart(request):
    """
    دریافت سبد خرید از Session
    """

    return request.session.get(
        CART_SESSION_KEY,
        {}
    )


def save_cart(request, cart):
    """
    ذخیره سبد خرید در Session
    """

    request.session[CART_SESSION_KEY] = cart

    request.session.modified = True


def make_cart_key(
        product_id,
        color_id=None,
        size_id=None
):
    """
    ساخت یک کلید یکتا برای هر ترکیب:

    Product + Color + Size

    مثال:

    12:3:5
    """

    color_id = color_id or 0
    size_id = size_id or 0

    return f'{product_id}:{color_id}:{size_id}'


def add_to_cart(
        request,
        product,
        quantity,
        color_id=None,
        size_id=None
):
    """
    اضافه کردن محصول به سبد خرید
    """

    cart = get_cart(request)

    cart_key = make_cart_key(
        product.id,
        color_id,
        size_id
    )

    if cart_key in cart:

        cart[cart_key]['quantity'] += quantity

    else:

        cart[cart_key] = {
            'product_id': product.id,
            'color_id': color_id,
            'size_id': size_id,
            'quantity': quantity,
        }

    save_cart(
        request,
        cart
    )


def update_cart_item(
        request,
        cart_key,
        quantity
):
    """
    بروزرسانی تعداد یک آیتم
    """

    cart = get_cart(request)

    if cart_key not in cart:
        return

    cart[cart_key]['quantity'] = quantity

    save_cart(
        request,
        cart
    )


def remove_from_cart(
        request,
        cart_key
):
    """
    حذف یک آیتم از سبد خرید
    """

    cart = get_cart(request)

    if cart_key not in cart:
        return

    del cart[cart_key]

    save_cart(
        request,
        cart
    )


def get_cart_count(request):
    """
    تعداد کل کالاها در سبد خرید

    مثال:

    Product A = 2
    Product B = 3

    نتیجه = 5
    """

    cart = get_cart(request)

    return sum(
        item.get('quantity', 0)
        for item in cart.values()
    )


def get_cart_items(request):
    """
    آماده کردن اطلاعات کامل سبد خرید
    """

    cart = get_cart(request)

    if not cart:
        return []

    product_ids = [
        item.get('product_id')
        for item in cart.values()
    ]

    products = (
        Product.objects
        .filter(
            id__in=product_ids,
            status=True
        )
        .prefetch_related(
            'color',
            'size'
        )
    )

    products_by_id = {
        product.id: product
        for product in products
    }

    cart_items = []

    stale_keys = []

    for cart_key, item in cart.items():

        product = products_by_id.get(
            item.get('product_id')
        )

        if not product:
            stale_keys.append(
                cart_key
            )

            continue

        color = None

        color_id = item.get(
            'color_id'
        )

        if color_id:
            color = next(
                (
                    color_item
                    for color_item
                    in product.color.all()
                    if color_item.id == color_id
                ),
                None
            )

        size = None

        size_id = item.get(
            'size_id'
        )

        if size_id:
            size = next(
                (
                    size_item
                    for size_item
                    in product.size.all()
                    if size_item.id == size_id
                ),
                None
            )

        quantity = int(
            item.get(
                'quantity',
                1
            )
        )

        unit_price = product.final_price

        total_price = (
                unit_price * quantity
        )

        cart_items.append(
            {
                'key': cart_key,
                'product': product,
                'color': color,
                'size': size,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
            }
        )

    # حذف آیتم‌هایی که محصولشان دیگر وجود ندارد
    if stale_keys:

        for cart_key in stale_keys:
            cart.pop(
                cart_key,
                None
            )

        save_cart(
            request,
            cart
        )

    return cart_items
