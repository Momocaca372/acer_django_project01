# myapp/management/commands/sync_firebase.py
from django.core.management.base import BaseCommand
from BIBIGOproject.firebase_config import firebase
from myapp.models import Store, Category, Product  # 移除 DataEntry
from decimal import Decimal
from django.db import transaction

class Command(BaseCommand):
    help = 'Sync Firebase data to Django database'

    def handle(self, *args, **kwargs):
        db = firebase.database()

        # 同步 Store
        stores = db.child("store").get().val()
        if stores:
            for idx, store_data in enumerate(stores):
                if store_data:
                    Store.objects.update_or_create(
                        id=str(idx),
                        defaults={'name': store_data['name']}
                    )
            self.stdout.write(self.style.SUCCESS('Stores synced successfully'))

        # 同步 Category
        categories = db.child("category").get().val()
        if categories:
            for idx, cat_data in enumerate(categories):
                if cat_data:
                    store = Store.objects.get(id=cat_data['store_id'])
                    Category.objects.update_or_create(
                        id=str(idx),
                        defaults={'name': cat_data['name'], 'store': store}
                    )
            self.stdout.write(self.style.SUCCESS('Categories synced successfully'))

        # 同步 Product（包含 product_detail 和 product_relabel）
        products = db.child("product").get().val()
        product_details = db.child("product_detail").get().val()
        product_relabels = db.child("product_relabel").get().val()  # 獲取 product_relabel 資料

        if products and product_details:
            for idx, (prod_data, detail_data) in enumerate(zip(products, product_details)):
                if prod_data and detail_data:
                    category = Category.objects.get(id=prod_data['category_id'])
                    store = Store.objects.get(id=prod_data['store_id'])
                    price_str = str(detail_data['price']).replace(',', '')
                    price = Decimal(price_str)

                    # 從 product_relabel 獲取 value
                    value = None
                    if product_relabels and idx < len(product_relabels) and product_relabels[idx] is not None:
                        value = int(product_relabels[idx])  # 轉為整數

                    Product.objects.update_or_create(
                        id=str(idx),
                        defaults={
                            'category': category,
                            'store': store,
                            'img_url': detail_data['img_url'],
                            'name': detail_data['name'],
                            'price': price,
                            'product_url': detail_data['product_url'],
                            'value': value  # 新增 value 欄位
                        }
                    )
            self.stdout.write(self.style.SUCCESS('Products synced successfully'))

        self.stdout.write(self.style.SUCCESS('成功同步 Firebase 資料到 Django 資料庫'))