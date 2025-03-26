from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from BIBIGOproject.firebase_config import pyrebase_auth  # 從你的配置導入
from firebase_admin import auth as firebase_admin_auth  # 直接從 firebase_admin 導入 auth
from myapp.models import Product, FollowedProduct
from django.db.models import Q, Count
import re
import random
import logging
import sqlite3
from django.core.mail import send_mail
from myapp.utils.bigdata_final import most_similar_filter , create_Word2Vec ,recommand_list_generator
from django.conf import settings
from functools import wraps
from pathlib import Path
import joblib
from gensim.models import Word2Vec

logger = logging.getLogger(__name__)

STORE_BASE_URLS = {
    "1": "https://online.carrefour.com.tw",
    "2": "https://www.costco.com.tw",
    "3": "https://www.poyabuy.com.tw",
    "4": "https://www.savesafe.com.tw/Products/"
}

# 設定路徑
path = Path(__file__).resolve().parent.parent

# 預載入資料
df_product = joblib.load(path / "static/df_product.pkl")
vectorizer = Word2Vec.load(str(path / "static/Word2Vec.pkl"))

def preload_bigdata(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):

        request.df_product = df_product
        request.vectorizer = vectorizer
        return func(request, *args, **kwargs)
    return wrapper

# 統一圖片處理邏輯
def process_image_url(img_url, store_id, store_base_url):
    if img_url and img_url.startswith('http'):
        return img_url
    elif img_url:
        if store_id in ['1', '2']:
            return store_base_url + img_url
        return img_url
    return '/static/default_image.png'  # 預設圖片


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

def subpage(request):
    uid = request.session.get('firebase_uid')
    category_value = request.GET.get('category', '')

    if category_value:
        hot_products = Product.objects.filter(value=category_value).order_by('?')[:20]
    else:
        hot_products = Product.objects.order_by('?')[:20]

    for product in hot_products:
        store_id = str(product.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            product.image_url = product.img_url if product.img_url and product.img_url.startswith('http') else store_url + (product.img_url or '')
        else:
            product.image_url = product.img_url or ''
        product.product_url = product.product_url if product.product_url and product.product_url.startswith('http') else store_url + (product.product_url or '')
        product.price_int = int(float(product.price)) if product.price is not None else 0
        product.is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    categories = Product.objects.values('value').distinct().order_by('value')
    categories = [{'value': cat['value'], 'name': cat['value']} for cat in categories if cat['value'] is not None]

    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    for tag in hot_tags:
        store_id = str(tag.store.id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            tag.image_url = tag.img_url if tag.img_url and tag.img_url.startswith('http') else store_url + (tag.img_url or '')
        else:
            tag.image_url = tag.img_url or ''
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    return render(request, 'subpage.html', {
        'hot_products': hot_products,
        'categories': categories,
        'hot_tags': hot_tags,
        'uid': uid,
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
        store_id = str(product.store_id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:
            image_url = product.img_url
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

# 搜尋視圖
def search(request):
    query = request.GET.get('q', '')
    uid = request.session.get('firebase_uid')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(price__icontains=query)
        )[:20]
    else:
        products = Product.objects.none()

    # 處理 products 的 image_url 和其他屬性
    for product in products:
        store_id = str(product.store_id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            product.image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:
            product.image_url = product.img_url
        product.product_url = product.product_url if product.product_url.startswith('http') else store_url + product.product_url
        product.price_int = int(product.price)
        product.is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    # 處理 hot_tags
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    # 為 hot_tags 添加 image_url
    for tag in hot_tags:
        store_id = str(tag.store_id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            tag.image_url = tag.img_url if tag.img_url.startswith('http') else store_url + tag.img_url
        else:
            tag.image_url = tag.img_url

    categories = Product.objects.values('value').distinct().order_by('value')
    categories = [{'value': cat['value'], 'name': cat['value']} for cat in categories]

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
    # 動態生成分類列表，直接從 Product.value 獲取
    categories = Product.objects.values('value').distinct().order_by('value')
    categories = [(cat['value'], cat['value'], f"Class_img/{cat['value']}.jpg") for cat in categories]

    # 處理 hot_tags
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    # 為 hot_tags 添加 image_url
    for tag in hot_tags:
        store_id = str(tag.store_id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            tag.image_url = tag.img_url if tag.img_url.startswith('http') else store_url + tag.img_url
        else:
            tag.image_url = tag.img_url

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
        product = get_object_or_404(Product, id=int(product_id))
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
@preload_bigdata
def product(request, product_id):
    product = get_object_or_404(Product, id=int(product_id))
    uid = request.session.get('firebase_uid')
    store_id = str(product.store.id)
    store_base_url = STORE_BASE_URLS.get(store_id, "")
    

    # 處理當前商品的圖片和連結
    product.image_url = process_image_url(product.img_url, store_id, store_base_url)
    product.product_url = product.product_url if product.product_url and product.product_url.startswith('http') else store_base_url + (product.product_url or '')
    product.price_int = int(float(product.price)) if product.price is not None else 0
    is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    # 初始相關商品（前 5 個，排除當前商品）
    similar_products_df = most_similar_filter(product.name, top_n=40)
    related_products = []
    for _, row in similar_products_df.iterrows():
        related_id = int(row['id'])
        if related_id == product.id:
            continue
        try:
            related = Product.objects.get(id=related_id)
            related_store_id = str(related.store.id)
            related_base_url = STORE_BASE_URLS.get(related_store_id, "")
            related.image_url = process_image_url(related.img_url, related_store_id, related_base_url)
            related.price_int = int(float(related.price)) if related.price is not None else 0
            related_products.append(related)
        except Product.DoesNotExist:
            continue
        if len(related_products) >= 5:
            break

    # 推薦商品（前 30 個，排除當前商品和 related_products）
    recommended_products = []
    for _, row in similar_products_df.iterrows():
        recommended_id = int(row['id'])
        if recommended_id == product.id:
            continue
        if recommended_id in [p.id for p in related_products]:
            continue
        try:
            recommended = Product.objects.get(id=recommended_id)
            recommended_store_id = str(recommended.store.id)
            recommended_base_url = STORE_BASE_URLS.get(recommended_store_id, "")
            recommended.image_url = process_image_url(recommended.img_url, recommended_store_id, recommended_base_url)
            recommended.price_int = int(float(recommended.price)) if recommended.price is not None else 0
            recommended_products.append(recommended)
        except Product.DoesNotExist:
            continue
        if len(recommended_products) >= 30:
            break

    # 處理 hot_tags 的 image_url
    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_tags = Product.objects.filter(id__in=product_ids)
    hot_tags = random.sample(list(hot_tags), min(5, len(hot_tags)))

    for tag in hot_tags:
        tag_store_id = str(tag.store.id)
        tag_base_url = STORE_BASE_URLS.get(tag_store_id, "")
        tag.image_url = process_image_url(tag.img_url, tag_store_id, tag_base_url)

    # 商品分類
    categories = Product.objects.values('value').distinct().order_by('value')
    categories = [{'value': cat['value'], 'name': cat['value']} for cat in categories if cat['value'] is not None]

    return render(request, 'product.html', {
        'product': product,
        'is_followed': is_followed,
        'related_products': related_products,
        'recommended_products': recommended_products,
        'hot_tags': hot_tags,
        'categories': categories
    })
    
@preload_bigdata
def load_more_related_products(request):
    product_id = request.GET.get('product_id')
    offset = int(request.GET.get('offset', 5))
    product = get_object_or_404(Product, id=int(product_id))


    similar_products_df = most_similar_filter(product.name, top_n=offset + 5)
    related_products = []
    for index, row in similar_products_df.iterrows():
        related_id = int(row['id'])
        if related_id == product.id:
            continue
        try:
            related = Product.objects.get(id=related_id)
            related_store_id = str(related.store.id)
            related_base_url = STORE_BASE_URLS.get(related_store_id, "")
            related.image_url = process_image_url(related.img_url, related_store_id, related_base_url)
            related.price_int = int(float(related.price)) if related.price is not None else 0
            related_products.append({
                'id': related.id,
                'name': related.name,
                'image_url': related.image_url,
                'price': related.price_int
            })
        except Product.DoesNotExist:
            continue

    related_products = related_products[offset-5:offset] if len(related_products) > offset else related_products[offset-5:]
    return JsonResponse({'related_products': related_products})

# 關注清單視圖
@preload_bigdata
def care(request):
    uid = request.session.get('firebase_uid')
    user_email = request.session.get('user_email')

    # 篩選參數
    store_filter = request.GET.get('store', '')
    category_filter = request.GET.get('category', '')

    # 處理關注商品
    if user_email and uid:
        followed_products = FollowedProduct.objects.filter(user_id=uid).order_by('-followed_at')
        
        # 應用篩選
        if store_filter:
            followed_products = followed_products.filter(product__store__id=store_filter)
        if category_filter:
            followed_products = followed_products.filter(product__value=category_filter)

        for followed in followed_products:
            store_id = str(followed.product.store.id)
            store_base_url = STORE_BASE_URLS.get(store_id, "")
            followed.product.image_url = process_image_url(followed.product.img_url, store_id, store_base_url)
            followed.product.product_url = followed.product.product_url if followed.product.product_url and followed.product.product_url.startswith('http') else store_base_url + (followed.product.product_url or '')
            followed.product.price_int = int(float(followed.product.price)) if followed.product.price is not None else 0
    else:
        followed_products = []

    # 基於用戶關注歷史的推薦（使用 myapp_recommand_list）
    recommended_products = []
    if uid:
        # 從 myapp_recommand_list 中獲取用戶的推薦商品
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT product_id FROM myapp_recommand_list WHERE user_id = ? LIMIT 30", (uid,))
        recommended_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        # 根據推薦的 product_id 查詢商品詳情
        for prod_id in recommended_ids:
            try:
                recommended = Product.objects.get(id=prod_id)
                recommended_store_id = str(recommended.store.id)
                recommended_base_url = STORE_BASE_URLS.get(recommended_store_id, "")
                recommended.image_url = process_image_url(recommended.img_url, recommended_store_id, recommended_base_url)
                recommended.price_int = int(float(recommended.price)) if recommended.price is not None else 0
                recommended_products.append(recommended)
            except Product.DoesNotExist:
                continue

    # 如果用戶未登入或無推薦商品，隨機選擇一些熱門商品
    if not recommended_products:
        popular_products = Product.objects.annotate(follow_count=Count('followedproduct')).order_by('-follow_count')[:30]
        for prod in popular_products:
            store_id = str(prod.store.id)
            store_base_url = STORE_BASE_URLS.get(store_id, "")
            prod.image_url = process_image_url(prod.img_url, store_id, store_base_url)
            prod.price_int = int(float(prod.price)) if prod.price is not None else 0
            recommended_products.append(prod)

    # 分類選項
    categories = Product.objects.values('value').distinct().order_by('value')
    categories = [{'value': cat['value'], 'name': cat['value']} for cat in categories if cat['value'] is not None]

    # 商店選項
    stores = [
        {'id': '1', 'name': '家樂福'},
        {'id': '2', 'name': 'Costco'},
        {'id': '3', 'name': '寶雅'},
        {'id': '4', 'name': '大買家'},
    ]

    return render(request, 'care.html', {
        'followed_products': followed_products,
        'recommended_products': recommended_products,  # 新增推薦商品
        'categories': categories,
        'stores': stores,
        'selected_store': store_filter,
        'selected_category': category_filter,
    })

def hot(request):
    uid = request.session.get('firebase_uid')

    popular_products = FollowedProduct.objects.values('product').annotate(
        follow_count=Count('id')
    ).order_by('-follow_count')[:10]
    product_ids = [item['product'] for item in popular_products]
    hot_products = Product.objects.filter(id__in=product_ids)
    
    for product in hot_products:
        store_id = str(product.store_id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            product.image_url = product.img_url if product.img_url.startswith('http') else store_url + product.img_url
        else:
            product.image_url = product.img_url
        product.price_int = int(product.price)
        product.is_followed = FollowedProduct.objects.filter(user_id=uid, product=product).exists() if uid else False

    # 處理 hot_tags 的 image_url
    hot_tags = random.sample(list(hot_products), min(5, len(hot_products)))
    for tag in hot_tags:
        store_id = str(tag.store_id)
        store_url = STORE_BASE_URLS.get(store_id, "")
        if store_id in ["1", "2"]:
            tag.image_url = tag.img_url if tag.img_url.startswith('http') else store_url + tag.img_url
        else:
            tag.image_url = tag.img_url

    categories = Product.objects.values('value').distinct().order_by('value')
    categories = [{'value': cat['value'], 'name': cat['value']} for cat in categories]

    return render(request, 'hot.html', {
        'hot_products': hot_products,
        'hot_tags': hot_tags,
        'categories': categories
    })

@csrf_exempt
def contact_view(request):
    if request.method == 'POST':
        if not request.session.get('user_email'):
            return JsonResponse({'success': False, 'error': '請先登入'})

        user_email = request.session['user_email']  # 發件人
        message = request.POST.get('message')
        recipient_list = settings.CUSTOMER_SERVICE_EMAILS  # 從 settings 讀取

        try:
            send_mail(
                subject='來自用戶的客服問題',
                message=f'用戶 {user_email} 提交的問題：\n\n{message}',
                from_email=user_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '無效的請求'})

def create_vec_view(request):
    try:
        create_Word2Vec()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False})