from django.db import models
from django.contrib.auth.models import User

class Store(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    img_url = models.URLField(max_length=500)  
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_url = models.URLField(max_length=500)  
    value = models.CharField(max_length=100, null=True, blank=True)  

    def __str__(self):
        return self.name

class FollowedProduct(models.Model):
    user_id = models.CharField(max_length=128)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'product')