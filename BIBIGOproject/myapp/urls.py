# -*- coding: utf-8 -*-

from django.urls import path,re_path
from . import views


urlpatterns =[
    path('LoginPage', views.login_view, name='Login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('cache', views.my_view, name='cache'),
    path('send_email', views.send_email, name='send_email'),
    path('home/', views.home, name='home'),
    path('subpage/', views.subpage, name='subpage'),
    path('search/', views.search, name='search'),
    path('product/<int:product_id>/', views.product, name='product'),
    re_path(r'^dreamreal/', views.dreamreal, name='dreamreal'),
    path('home/', views.home, name='home'),
    path('subpage/', views.subpage, name='subpage'),
    path('search/', views.search, name='search'),
    path('product/<int:product_id>/', views.product, name='product'),
    ]