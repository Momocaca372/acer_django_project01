# myapp/management/commands/sync_firebase.py
from django.core.management.base import BaseCommand
from BIBIGOproject.firebase_config import firebase
from myapp.models import Store, Category, Product, DataEntry
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
                if store_data:  # 過濾 null
                    Store.objects.update_or_create(
                        id=str(idx),
                        defaults={'name': store_data['name']}
                    )

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

        # 同步 Product 和 Product Detail
        products = db.child("product").get().val()
        product_details = db.child("product_detail").get().val()
        if products and product_details:
            for idx, (prod_data, detail_data) in enumerate(zip(products, product_details)):
                if prod_data and detail_data:
                    category = Category.objects.get(id=prod_data['category_id'])
                    store = Store.objects.get(id=prod_data['store_id'])
                    price_str = str(detail_data['price']).replace(',', '')
                    price = Decimal(price_str)
                    Product.objects.update_or_create(
                        id=str(idx),
                        defaults={
                            'category': category,
                            'store': store,
                            'img_url': detail_data['img_url'],
                            'name': detail_data['name'],
                            'price': price,
                            'product_url': detail_data['product_url']
                        }
                    )

        # 同步 DataEntry（假設陣列位於 "data" 路徑）
        data_array = db.child("data").get().val()
        if data_array:
            # 確認索引 0 是 null
            if data_array[0] is not None:
                self.stdout.write(self.style.WARNING('Index 0 is not null, proceeding anyway'))

            # 取得當前最大索引
            last_entry = DataEntry.objects.order_by('-index').first()
            last_index = last_entry.index if last_entry else -1

            # 分批處理
            batch_size = 1000
            total_length = len(data_array)
            new_or_updated_entries = []

            for i in range(max(0, last_index + 1), total_length):
                value = data_array[i]
                new_or_updated_entries.append(DataEntry(index=i, value=value))

                if len(new_or_updated_entries) >= batch_size:
                    with transaction.atomic():
                        DataEntry.objects.bulk_create(new_or_updated_entries, ignore_conflicts=False)
                        for entry in new_or_updated_entries:
                            DataEntry.objects.filter(index=entry.index).update(value=entry.value)
                    self.stdout.write(self.style.SUCCESS(f'Synced {i + 1}/{total_length} DataEntry entries'))
                    new_or_updated_entries = []

            # 處理剩餘資料
            if new_or_updated_entries:
                with transaction.atomic():
                    DataEntry.objects.bulk_create(new_or_updated_entries, ignore_conflicts=False)
                    for entry in new_or_updated_entries:
                        DataEntry.objects.filter(index=entry.index).update(value=entry.value)
                self.stdout.write(self.style.SUCCESS(f'Synced {total_length}/{total_length} DataEntry entries'))

        self.stdout.write(self.style.SUCCESS('成功同步 Firebase 資料到 Django 資料庫'))