from django.urls import path

from . import views

app_name = 'cart_app'

urlpatterns = [

    path(
        'add/<int:product_id>/',
        views.CartAddView.as_view(),
        name='cart_add'
    ),

    path(
        'detail/',
        views.CartDetailView.as_view(),
        name='cart_detail'
    ),

    path(
        'update/',
        views.CartUpdateView.as_view(),
        name='cart_update'
    ),

    path(
        'remove/',
        views.CartRemoveView.as_view(),
        name='cart_remove'
    ),

]
