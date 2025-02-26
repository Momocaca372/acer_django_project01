from django.db import models


class Store(models.Model):
    id = models.AutoField(primary_key=True)  # 自動遞增的主鍵
    name = models.CharField(max_length=255)  # 商店名稱，不允許為空

    def __str__(self):
        return self.name  # 在 Django Admin 或 shell 顯示商店名稱


class Category(models.Model):
    id = models.AutoField(primary_key=True)  # 自動遞增的主鍵
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # 關聯到 `store` 表
    name = models.CharField(max_length=255)  # 分類名稱，不允許為空

    def __str__(self):
        return self.name  # 在 Django Admin 或 shell 顯示分類名稱


class Product(models.Model):
    id = models.AutoField(primary_key=True)  # 自動遞增的主鍵
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # 關聯 store 表
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # 關聯 category 表

    def __str__(self):
        return f"Product {self.id}"  # 讓 Django Admin 介面顯示 Product ID


class ProductDetail(models.Model):
    id = models.AutoField(primary_key=True)  # 自動遞增的主鍵
    product = models.ForeignKey(  # 外鍵關聯到 `product` 表的 `id`
        Product,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)  # 商品名稱
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 商品價格
    image_url = models.TextField(blank=True, null=True)  # 圖片網址，可為空
    product_url = models.TextField(blank=True, null=True)  # 產品頁面網址，可為空

    def __str__(self):
        return self.name  # 在 Django Admin 或 shell 顯示商品名稱

        
class Login(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    
    class Meta:
        db_table = "login"