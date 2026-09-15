from django.contrib import messages
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)
from django.views import View

from product_app.models import Product

from .cart import (
    add_to_cart,
    get_cart_items,
    remove_from_cart,
    update_cart_item,
)


class CartAddView(View):

    def post(
            self,
            request,
            product_id,
            *args,
            **kwargs
    ):

        product = get_object_or_404(
            Product,
            id=product_id,
            status=True
        )

        color_id = request.POST.get(
            'color_id'
        )

        size_id = request.POST.get(
            'size_id'
        )

        quantity = request.POST.get(
            'quantity',
            '1'
        )

        # =========================================
        # Quantity validation
        # =========================================

        try:

            quantity = int(
                quantity
            )

        except (
                TypeError,
                ValueError
        ):

            quantity = 0

        if quantity < 1:
            messages.error(
                request,
                'Invalid quantity.'
            )

            return redirect(
                product.get_absolute_url()
            )

        # =========================================
        # Color validation
        # =========================================

        if product.color.exists():

            if not color_id:
                messages.error(
                    request,
                    'Please select a color.'
                )

                return redirect(
                    product.get_absolute_url()
                )

            if not product.color.filter(
                    id=color_id
            ).exists():
                messages.error(
                    request,
                    'Selected color is not available for this product.'
                )

                return redirect(
                    product.get_absolute_url()
                )

        else:

            color_id = None

        # =========================================
        # Size validation
        # =========================================

        if product.size.exists():

            if not size_id:
                messages.error(
                    request,
                    'Please select a size.'
                )

                return redirect(
                    product.get_absolute_url()
                )

            if not product.size.filter(
                    id=size_id
            ).exists():
                messages.error(
                    request,
                    'Selected size is not available for this product.'
                )

                return redirect(
                    product.get_absolute_url()
                )

        else:

            size_id = None

        # =========================================
        # Convert IDs to integer
        # =========================================

        if color_id:
            color_id = int(
                color_id
            )

        if size_id:
            size_id = int(
                size_id
            )

        # =========================================
        # Add product to cart
        # =========================================

        add_to_cart(
            request=request,
            product=product,
            quantity=quantity,
            color_id=color_id,
            size_id=size_id
        )

        messages.success(
            request,
            'Product added to cart successfully.'
        )

        # مهم:
        # کاربر به Cart نمی‌رود
        # در همان صفحه محصول می‌ماند.

        return redirect(
            product.get_absolute_url()
        )


class CartDetailView(View):

    def get(
            self,
            request,
            *args,
            **kwargs
    ):
        cart_items = get_cart_items(
            request
        )

        subtotal = sum(
            item['total_price']
            for item in cart_items
        )

        # فعلاً هزینه ارسال ثابت است.
        # بعداً می‌توانیم سیستم Shipping حرفه‌ای بسازیم.

        shipping = 10 if cart_items else 0

        total = (
                subtotal
                + shipping
        )

        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
        }

        return render(
            request,
            'cart_app/cart_detail.html',
            context
        )


class CartUpdateView(View):

    def post(
            self,
            request,
            *args,
            **kwargs
    ):

        cart_key = request.POST.get(
            'cart_key'
        )

        quantity = request.POST.get(
            'quantity'
        )

        if not cart_key:
            messages.error(
                request,
                'Invalid cart item.'
            )

            return redirect(
                'cart_app:cart_detail'
            )

        try:

            quantity = int(
                quantity
            )

        except (
                TypeError,
                ValueError
        ):

            quantity = 0

        if quantity < 1:
            messages.error(
                request,
                'Quantity must be at least 1.'
            )

            return redirect(
                'cart_app:cart_detail'
            )

        update_cart_item(
            request=request,
            cart_key=cart_key,
            quantity=quantity
        )

        messages.success(
            request,
            'Cart updated successfully.'
        )

        return redirect(
            'cart_app:cart_detail'
        )


class CartRemoveView(View):

    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        cart_key = request.POST.get(
            'cart_key'
        )

        if not cart_key:
            messages.error(
                request,
                'Invalid cart item.'
            )

            return redirect(
                'cart_app:cart_detail'
            )

        remove_from_cart(
            request=request,
            cart_key=cart_key
        )

        messages.success(
            request,
            'Product removed from cart.'
        )

        return redirect(
            'cart_app:cart_detail'
        )
