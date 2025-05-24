from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'), # Correct usage
    path('payment-success/', views.PaymentSuccessView.as_view(), name='payment_success'),  # Correct usage
    path('payment-cancelled/', views.PaymentCancelledView.as_view(), name='payment_cancelled'),  # Correct usage
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'), 
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'), # Assuming you have this function
]