from django.urls import path
from . import views
from .views import product_details
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about-us/', views.about_us),
    path('blog/', views.blog),
    path('blog-details/', views.blog_details),

    path('checkout/', views.checkout, name='checkout'),
    path('contact-us/', views.contact_us),
    path('product/<int:id>/<slug:slug>/', views.product_details, name='product_details'),

    path('shop/', views.shop),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("add-wishlist/<int:id>/", views.add_to_wishlist, name="add_wishlist"),

    path('login/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('signup/', views.signup, name='signup'),
    path('quick-view/<int:id>/', views.quick_view, name='quick_view'),

    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:id>/', views.remove_from_cart, name='remove_from_cart'),

    path('update-quantity/', views.update_quantity, name='update_quantity'),
    path('payment/', views.payment, name='payment'),

    path('account/', views.account_dashboard, name='account_dashboard'),
    # path('my-orders/', views.my_orders, name='my_orders'),
    # path("order-success/", views.order_success, name="order_success"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("invoice/<str:order_id>/", views.invoice, name="invoice"),
    path("download-invoice/<str:order_id>/", views.download_invoice, name="download_invoice"),
    path('category/<str:category>/', views.category_products, name='category_products'),

    path('edit-profile/', views.edit_profile, name='edit_profile'),
]
