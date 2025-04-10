from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),  # Shows product list
    path('cart/', views.cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),  
    path('payment-success/', views.payment_success, name='payment_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),  
    path("register/", views.register, name="register"),

]



