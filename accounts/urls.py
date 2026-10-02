from django.urls import path
from . import views
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/<int:order_id>/',views.order_detail,name='order_detail'
),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),
]