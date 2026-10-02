from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('order_complete/<str:order_number>/',views.order_complete,name='order_complete'),
]