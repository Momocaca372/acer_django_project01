from django.db import models

# Create your models here.


class Store(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # 索引作為 ID
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Category(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # 索引作為 ID
    name = models.CharField(max_length=100)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # 索引作為 ID
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    img_url = models.URLField(max_length=500)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_url = models.URLField(max_length=500)

    def __str__(self):
        return self.name
    
class DataEntry(models.Model):
    index = models.IntegerField(unique=True)  # 陣列中的索引
    value = models.IntegerField(null=True, blank=True)  # 允許 null 值
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Index {self.index}: {self.value}"

    class Meta:
        ordering = ['index']  # 按索引排序