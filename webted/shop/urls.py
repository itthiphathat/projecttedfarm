from django.urls import path 
from . import views  
from .views import confirm_order, order_complete ,privacy_policy, terms_of_use ,line_webhook

urlpatterns = [
    path('', views.product_list, name='product_list'), 
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'), 
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('upload-payment-slip/<int:order_id>/', views.upload_payment_slip, name='upload_payment_slip'),
    path('order-complete/<int:order_id>/', views.order_complete, name='order_complete'),
    path('payment-status/', views.payment_status, name='payment_status'),
    path('admin-orders/', views.admin_order_list, name='admin_order_list'),
    path('admin-orders/confirm/<int:order_id>/', views.admin_confirm_payment, name='admin_confirm_payment'),
    path('admin-orders/reject/<int:order_id>/', views.admin_reject_payment, name='admin_reject_payment'),
    path('set-pickup-date/<int:order_id>/', views.set_pickup_date, name='set_pickup_date'),
    path("confirm-order/", confirm_order, name="confirm_order"),
    path("order-complete/<int:order_id>/", order_complete, name="order_complete"),
    path("order-success/", views.order_success, name="order_success"),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('terms-of-use/', terms_of_use, name='terms_of_use'),
    path('admin-sales-chart/', views.admin_sales_chart, name='admin_sales_chart'),
    path('admin-sales-data/', views.sales_data, name='admin_sales_data'),
    path("line/webhook/", line_webhook, name="line_webhook"),
    path('admin-orders/completed/<int:order_id>/', views.mark_order_completed, name='mark_order_completed'),
]