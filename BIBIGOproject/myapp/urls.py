from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('subpage/', views.subpage, name='subpage'),
    path('search/', views.search, name='search'),
    path('care/', views.care, name='care'),
    path('product/<int:product_id>/', views.product, name='product'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forget_password/', views.forget_password_view, name='forget_password'),
    path('register/', views.register_view, name='register'),
    
    
]