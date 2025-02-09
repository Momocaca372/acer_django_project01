# -*- coding: utf-8 -*-

from django.urls import path,re_path
from . import views


urlpatterns =[
    path('LoginPage', views.login_view, name='Login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('cache', views.my_view, name='cache'),
    path('send_email', views.send_email, name='send_email'),
    re_path(r'^dreamreal/', views.dreamreal, name='dreamreal'),
    ]