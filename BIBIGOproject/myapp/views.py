from django.shortcuts import render, redirect, get_object_or_404
from BIBIGOproject.firebase_config import firebase
from django.contrib import messages
from myapp.models import Product
# import pyrebase
import firebase_admin
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from firebase_admin import auth
import re
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from BIBIGOproject.firebase_config import pyrebase_auth
import logging
logger = logging.getLogger(__name__)
# # Create your views here.

def home(request):
    return render(request, 'base.html')

def subpage(request):
    STORE_BASE_URLS = {
        "1": "https://online.carrefour.com.tw",
        "2": "https://www.costco.com.tw"
    }

    hot_products = Product.objects.all()[:10]  # 限制前 10 筆
    for product in hot_products:
        product.image_url = product.img_url if product.img_url.startswith('http') else STORE_BASE_URLS[product.store.id] + product.img_url
        product.product_url = product.product_url if product.product_url.startswith('http') else STORE_BASE_URLS[product.store.id] + product.product_url

    return render(request, 'subpage.html', {'hot_products': hot_products})

def search(request):
    STORE_BASE_URLS = {
        "1": "https://online.carrefour.com.tw",
        "2": "https://www.costco.com.tw"
    }

    query = request.GET.get('q', '').strip()
    search_products = []

    if query:
        products = Product.objects.filter(name__icontains=query)[:10]
        for product in products:
            product.image_url = product.img_url if product.img_url.startswith('http') else STORE_BASE_URLS[product.store.id] + product.img_url
            product.product_url = product.product_url if product.product_url.startswith('http') else STORE_BASE_URLS[product.store.id] + product.product_url
            search_products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'image_url': product.image_url,
                'product_url': product.product_url
            })

    return render(request, 'search.html', {
        'query': query,
        'products': search_products
    })

def login_view(request):
    if 'user_email' in request.session:  # 保留 Firebase 會話檢查
        return redirect('subpage')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_page = request.POST.get('next', '/myapp/subpage/')
        try:
            user = pyrebase_auth.sign_in_with_email_and_password(email, password)
            request.session['user_email'] = user['email']
            request.session['firebase_uid'] = user['localId']
            return redirect(next_page)
        except Exception as e:
            messages.error(request, '登入失敗：請檢查您的電子郵件或密碼')
            return render(request, 'login.html', {'next': next_page})
    
    next_page = request.GET.get('next', request.META.get('HTTP_REFERER', '/myapp/subpage/'))
    return render(request, 'login.html', {'next': next_page})


def register_view(request):
    if request.method == 'POST':
        display_name = request.POST.get('displayName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 自訂 email 格式驗證
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, '電子郵件格式無效，請輸入正確的電子郵件地址')
            return render(request, 'register.html')

        # 密碼一致性檢查
        if password != confirm_password:
            messages.error(request, '密碼與確認密碼不一致')
            return render(request, 'register.html')

        try:
            user = pyrebase_auth.create_user_with_email_and_password(email, password)
            auth.update_user(user['localId'], display_name=display_name)
            request.session['user_email'] = user['email']
            request.session['firebase_uid'] = user['localId']
            request.session['display_name'] = display_name
            messages.success(request, '註冊成功！')
            return render(request, 'register.html')
        except Exception as e:
            error_msg = str(e).lower()
            if "email_exists" in error_msg:  # 修正為精確匹配
                messages.error(request, '此電子郵件已被註冊，請使用其他電子郵件或登入。')
            elif "weak_password" in error_msg or "6" in error_msg:
                messages.error(request, '密碼長度不足，請輸入至少 6 個字符的密碼。')
            else:
                messages.error(request, f'註冊失敗，請稍後再試。錯誤詳情：{str(e)}')
            return render(request, 'register.html')

    return render(request, 'register.html')

def logout_view(request):
    if 'user_email' in request.session:
        del request.session['user_email']
        del request.session['firebase_uid']
        if 'display_name' in request.session:
            del request.session['display_name']
    # 保留當前頁面
    return redirect(request.META.get('HTTP_REFERER', 'subpage'))

def forget_password_view(request):
    if 'user_email' in request.session:
        return redirect('subpage')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        # 自訂 email 格式驗證
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, '電子郵件格式錯誤')
            return render(request, 'forget_password.html')

        # 使用 Firebase Admin SDK 檢查信箱是否註冊
        try:
            auth.get_user_by_email(email)  # 若不存在會拋出異常
            # 已註冊，發送重設密碼郵件
            pyrebase_auth.send_password_reset_email(email)
            messages.success(request, '重設密碼郵件已發送，請檢查您的電子郵件收件箱。')
            return redirect('login')
        except auth.UserNotFoundError:
            # 未註冊信箱
            messages.error(request, '此電子郵件未註冊')
            return render(request, 'forget_password.html')
        except Exception as e:
            # 其他錯誤
            messages.error(request, f'發生錯誤，請稍後再試。錯誤詳情：{str(e)}')
            return render(request, 'forget_password.html')

    return render(request, 'forget_password.html')

def product(request, product_id):
    STORE_BASE_URLS = {
        "1": "https://online.carrefour.com.tw",
        "2": "https://www.costco.com.tw"
    }

    # 獲取單一商品
    product = get_object_or_404(Product, id=product_id)
    
    # 處理圖片和商品連結的 URL
    product.image_url = product.img_url if product.img_url.startswith('http') else STORE_BASE_URLS[product.store.id] + product.img_url
    product.product_url = product.product_url if product.product_url.startswith('http') else STORE_BASE_URLS[product.store.id] + product.product_url

    # 相關商品（根據類別推薦）
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    # 為相關商品處理 URL
    for related in related_products:
        related.image_url = related.img_url if related.img_url.startswith('http') else STORE_BASE_URLS[related.store.id] + related.img_url
        related.product_url = related.product_url if related.product_url.startswith('http') else STORE_BASE_URLS[related.store.id] + related.product_url

    return render(request, 'product.html', {
        'product': product,
        'related_products': related_products
    })

def care(request):
    return render(request, 'care.html')
