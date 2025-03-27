from django.urls import path
from . import views

urlpatterns = [
    # path('home/', views.home, name='home'),
    path('subpage/', views.subpage, name='subpage'),
    path('search/', views.search, name='search'),
    path('product/<str:product_id>/', views.product, name='product'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forget_password/', views.forget_password_view, name='forget_password'),
    path('register/', views.register_view, name='register'),
    path('cat/', views.cat_view, name='cat'),
    path('care/', views.care, name='care'),
    path('follow_product/', views.follow_product, name='follow_product'),
    path('hot/', views.hot, name='hot'),
    path('load-more-products/', views.load_more_products, name='load_more_products'),
    path('load_more_related_products/', views.load_more_related_products, name='load_more_related_products'),
    path('contact_view/', views.contact_view, name='contact_view'),
    path('createvec/', views.create_vec_view, name='create_vec_view'),
]