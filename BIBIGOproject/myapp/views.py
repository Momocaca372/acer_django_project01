from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from BIBIGOproject.firebase_config import pyrebase_auth  # 從你的配置導入
from firebase_admin import auth as firebase_admin_auth  # 直接從 firebase_admin 導入 auth
from myapp.models import Product, FollowedProduct
from django.db.models import Q,Count
import re
import random
import logging

logger = logging.getLogger(__name__)

VALUE_TO_CATEGORY = {
    85: "食品飲料", 86: "3C科技", 87: "影音家電", 88: "保健美容", 89: "日用母嬰",
    90: "服飾時尚", 91: "家具餐廚", 92: "珠寶黃金", 93: "運動戶外", 94: "辦公文具"
}

STORE_BASE_URLS = {
    "1": "https://online.carrefour.com.tw",
    "2": "https://www.costco.com.tw",
    "3": "https://www.poyabuy.com.tw",
    "4": "https://www.savesafe.com.tw/Products/"
}

# STORE_LOGOS = {
#     "1": "家樂福LOGO.jpg",
#     "2": "COSTCO.png",
#     "3": "寶雅LOGO.jpg",
#     "4": "大買家LOGO.png"
# }

# 通用函數：從 token 獲取 UID
def get_user_from_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.info("No Authorization header found")
        return None
    token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = firebase_admin_auth.verify_id_token(token)
        logger.info(f"Token verified, UID: {decoded_token['uid']}")
        return decoded_token['uid']
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

# 首頁視圖
def home(request):
    return render(request, 'base.html')

from django.shortcuts import render
from django.http import JsonResponse
from myapp.models import Product, FollowedProduct
from django.db.models import Count
import random

# 假設 VALUE_TO_CATEGORY 已獨立定義並導入
# from myapp.some_module import VALUE_TO_CATEGORY


def subpage(request):
    uid = request.session.get('firebase_uid')
    category_value = request.GET.get('category', None)
    if category_value:
        category_value = int(category_value)
        hot_products = Product.objects.filter(value=category_value).order_by('?')[:20]
        category_name = VALUE_TO_CATEGORY.get(category_value, "未知分類")
    else:
        hot_products = Product.objects.all().order_by('?')[:20]
        category_name = "所有商品"

    for product in hot_products:
        store_id = str(product.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        # 圖片 URL 處理
        if store_id in ["1", "2"]:
            product.image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:
            product.image_url = product.img_url
        # 商品 URL 處理
        product.product_url = product.product_url if product.product_url.startswith('http') else store_url + product.product_url
        product.price_int = int(product.price)
        product.is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    categories = [{'value': v, 'name': n} for v, n in VALUE_TO_CATEGORY.items()]

    return render(request, 'subpage.html', {
        'hot_products': hot_products,
        'hot_tags': hot_tags,
        'categories': categories,
        'category_name': category_name
    })

def load_more_products(request):
    uid = request.session.get('firebase_uid')
    offset = int(request.GET.get('offset', 20))
    query = request.GET.get('query', '')

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(price__icontains=query)
        )[offset:offset + 20]
    else:
        products = Product.objects.all().order_by('?')[offset:offset + 20]

    product_list = []
    for product in products:
        store_id = str(product.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        # 圖片 URL 處理
        if store_id in ["1", "2"]:  # 家樂福和 Costco
            image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:  # 寶雅 (3) 和大買家 (4)
            image_url = product.img_url  # 不拼接，直接使用原始圖片 URL
        # 商品 URL 處理
        product_url = product.product_url if product.product_url.startswith('http') else store_url + product.product_url
        is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False
        product_data = {
            'id': product.id,
            'name': product.name,
            'price': int(product.price),
            'image_url': image_url,
            'is_followed': is_followed
        }
        product_list.append(product_data)

    return JsonResponse({'products': product_list})
    return JsonResponse({'products': product_list})

# 搜尋視圖
def search(request):
    query = request.GET.get('q', '')
    uid = request.session.get('firebase_uid')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(price__icontains=query)
        )[:20]  # 初始載入 20 筆
    else:
        products = Product.objects.none()

    for product in products:
        store_id = str(product.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        # 圖片 URL 處理
        if store_id in ["1", "2"]:  # 家樂福和 Costco
            product.image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:  # 寶雅 (3) 和大買家 (4)
            product.image_url = product.img_url  # 不拼接，直接使用原始圖片 URL
        # 商品 URL 處理
        product.product_url = product.product_url if product.product_url.startswith('http') else store_url + product.product_url
        product.price_int = int(product.price)
        product.is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    # 熱門標籤
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    categories = [{'value': v, 'name': n} for v, n in VALUE_TO_CATEGORY.items()]

    return render(request, 'search.html', {
        'products': products,
        'query': query,
        'hot_tags': hot_tags,
        'categories': categories
    })

# 登入視圖
def login_view(request):
    if 'user_email' in request.session:
        logger.info(f"User already logged in: {request.session.get('firebase_uid')}")
        return redirect('subpage')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_page = request.POST.get('next', '/myapp/subpage/')
        try:
            user = pyrebase_auth.sign_in_with_email_and_password(email, password)
            user_info = pyrebase_auth.get_account_info(user['idToken'])
            if not user_info['users'][0]['emailVerified']:
                messages.error(request, '請先驗證您的電子郵件')
                return render(request, 'login.html', {'next': next_page})
            
            request.session['user_email'] = user['email']
            request.session['firebase_uid'] = user['localId']
            logger.info(f"User logged in: {user['localId']}, Email: {user['email']}")
            return render(request, 'login_redirect.html', {'next': next_page, 'id_token': user['idToken']})
        except Exception as e:
            messages.error(request, '登入失敗：請檢查您的電子郵件或密碼')
            logger.error(f"Login failed: {e}")
            return render(request, 'login.html', {'next': next_page})
    
    next_page = request.GET.get('next', request.META.get('HTTP_REFERER', '/myapp/subpage/'))
    return render(request, 'login.html', {'next': next_page})

# 註冊視圖
def register_view(request):
    if 'user_email' in request.session:
        return redirect('subpage')

    if request.method == 'POST':
        display_name = request.POST.get('displayName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([display_name, email, password, confirm_password]):
            messages.error(request, '請填寫所有欄位')
            return render(request, 'register.html')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, '電子郵件格式無效，請輸入正確的電子郵件地址')
            return render(request, 'register.html')

        if password != confirm_password:
            messages.error(request, '密碼與確認密碼不一致')
            return render(request, 'register.html')

        try:
            user = pyrebase_auth.create_user_with_email_and_password(email, password)
            firebase_admin_auth.update_user(user['localId'], display_name=display_name)
            pyrebase_auth.send_email_verification(user['idToken'])
            messages.success(request, '註冊成功！請檢查您的電子郵件以驗證帳號')
            return redirect('login')
        except Exception as e:
            error_msg = str(e).lower()
            if "email_exists" in error_msg:
                messages.error(request, '此電子郵件已被註冊，請使用其他電子郵件或登入。')
            elif "weak_password" in error_msg or "6" in error_msg:
                messages.error(request, '密碼長度不足，請輸入至少 6 個字符的密碼。')
            else:
                messages.error(request, f'註冊失敗，請稍後再試。錯誤詳情：{str(e)}')
            return render(request, 'register.html')

    return render(request, 'register.html')

# 登出視圖
def logout_view(request):
    if 'user_email' in request.session:
        del request.session['user_email']
        del request.session['firebase_uid']
        if 'display_name' in request.session:
            del request.session['display_name']
    return redirect(request.META.get('HTTP_REFERER', 'subpage'))

# 忘記密碼視圖
def forget_password_view(request):
    if 'user_email' in request.session:
        return redirect('subpage')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, '電子郵件格式錯誤')
            return render(request, 'forget_password.html')

        try:
            firebase_admin_auth.get_user_by_email(email)
            pyrebase_auth.send_password_reset_email(email)
            messages.success(request, '重設密碼郵件已發送，請檢查您的電子郵件收件箱。')
            return redirect('login')
        except firebase_admin_auth.UserNotFoundError:
            messages.error(request, '此電子郵件未註冊')
            return render(request, 'forget_password.html')
        except Exception as e:
            messages.error(request, f'發生錯誤，請稍後再試。錯誤詳情：{str(e)}')
            return render(request, 'forget_password.html')

    return render(request, 'forget_password.html')

# 分類視圖
def cat_view(request):
    # 保留原本的分類邏輯
    categories = [(v, n, f"Class_img/{v}.png") for v, n in VALUE_TO_CATEGORY.items()]

    # 添加與其他頁面一致的熱門標籤邏輯
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    return render(request, 'cat.html', {
        'categories': categories,
        'hot_tags': hot_tags,
    })

# 關注商品 API
@csrf_exempt
def follow_product(request):
    if request.method == 'POST':
        uid = get_user_from_token(request) or request.session.get('firebase_uid')
        logger.info(f"Received follow_product request. User ID from token: {get_user_from_token(request)}, Session UID: {request.session.get('firebase_uid')}")
        if not uid:
            logger.warning("No user ID found, authentication required")
            return JsonResponse({'success': False, 'message': '需要登入'}, status=401)

        product_id = request.POST.get('product_id')
        logger.info(f"Product ID: {product_id}")
        product = get_object_or_404(Product, id=product_id)
        
        followed, created = FollowedProduct.objects.get_or_create(user_id=uid, product=product)
        logger.info(f"Followed: {followed}, Created: {created}")
        if not created:
            followed.delete()
            logger.info("Product unfollowed")
            return JsonResponse({'success': True, 'followed': False})
        logger.info("Product followed")
        return JsonResponse({'success': True, 'followed': True})
    logger.warning("Invalid request method")
    return JsonResponse({'success': False, 'message': '無效請求'})

# 商品詳情視圖
def product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    uid = request.session.get('firebase_uid')
    store_id = str(product.store.id)
    store_url = STORE_BASE_URLS.get(store_id, "")
    
    # 圖片 URL 處理
    if store_id in ["1", "2"]:  # 家樂福和 Costco
        product.image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
    else:  # 寶雅 (3) 和大買家 (4)
        product.image_url = product.img_url
    # 商品 URL 處理
    product.product_url = product.product_url if product.product_url.startswith('http') else store_url + product.product_url
    product.price_int = int(product.price)
    is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    # 相關商品（初始 5 個）
    related_products = Product.objects.filter(value=product.value).exclude(id=product.id).order_by('?')[:5]
    for related in related_products:
        related_store_id = str(related.store.id)
        related_store_url = STORE_BASE_URLS.get(related_store_id, "")
        if related_store_id in ["1", "2"]:
            related.image_url = related.img_url if related.img_url.startswith('http') else related_store_url + related.img_url
        else:
            related.image_url = related.img_url
        related.price_int = int(related.price)

    # 熱門標籤
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    categories = [{'value': v, 'name': n} for v, n in VALUE_TO_CATEGORY.items()]

    return render(request, 'product.html', {
        'product': product,
        'is_followed': is_followed,
        'related_products': related_products,
        'hot_tags': hot_tags,
        'categories': categories
    })

def load_more_related_products(request):
    product_id = request.GET.get('product_id')
    offset = int(request.GET.get('offset', 5))
    product = get_object_or_404(Product, id=product_id)
    
    related_products = Product.objects.filter(value=product.value).exclude(id=product.id).order_by('?')[offset:offset + 5]
    product_list = []
    for related in related_products:
        store_id = str(related.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:  # 家樂福和 Costco
            image_url = related.img_url if related.img_url.startswith('http') else store_url + related.img_url
        else:  # 寶雅 (3) 和大買家 (4)
            image_url = related.img_url
        product_data = {
            'id': related.id,
            'name': related.name,
            'price': int(related.price),
            'image_url': image_url
        }
        product_list.append(product_data)

    return JsonResponse({'related_products': product_list})

# 關注清單視圖
def care(request):
    uid = request.session.get('firebase_uid')
    user_email = request.session.get('user_email')

    if user_email and uid:
        followed_products = FollowedProduct.objects.filter(user_id=uid).order_by('-followed_at')  # 按 followed_at 降序排序
        for followed in followed_products:
            store_id = str(followed.product.store.id)
            store_url = STORE_BASE_URLS.get(store_id, "")
            if store_id in ["1", "2"]:  # 家樂福和 Costco
                followed.product.image_url = followed.product.img_url if followed.product.img_url.startswith('http') else store_url + followed.product.img_url
            else:  # 寶雅 (3) 和大買家 (4)
                followed.product.image_url = followed.product.img_url
            followed.product.product_url = followed.product.product_url if followed.product.product_url.startswith('http') else store_url + followed.product.product_url
            followed.product.price = int(followed.product.price)
    else:
        followed_products = []

    categories = [{'value': v, 'name': n} for v, n in VALUE_TO_CATEGORY.items()]

    return render(request, 'care.html', {
        'followed_products': followed_products,
        'categories': categories
    })


def hot(request):
    uid = request.session.get('firebase_uid')

    # 熱門商品（根據關注數排序）
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_products = Product.objects.filter(id__in=product_ids)
    
    for product in hot_products:
        store_id = str(product.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:  # 家樂福和 Costco
            product.image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:  # 寶雅 (3) 和大買家 (4)
            product.image_url = product.img_url
        product.price_int = int(product.price)  # 移除小數點
        product.is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    # 熱門標籤
    hot_tags = random.sample(list(hot_products), min(5, len(hot_products)))
    categories = [{'value': v, 'name': n} for v, n in VALUE_TO_CATEGORY.items()]

    return render(request, 'hot.html', {
        'hot_products': hot_products,
        'hot_tags': hot_tags,
        'categories': categories
    })

def customer_service_home(request):
    return render(request, 'customer_service_home.html')