from django.db import models


# Create your models here.
class Dreamreal(models.Model):
    website = models.CharField(max_length=50)
    mail = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    phonenumber = models.IntegerField()
    #online = models.ForeignKey('Online', default=1, on_delete=models.CASCADE, db_constraint=False)

    class Meta:
        db_table = "dreamreal"
        
# class Online(models.Model):
#     domain = models.CharField(max_length=30)

#     class Meta:
#         db_table = "online"
        
class Login(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    
    class Meta:
        db_table = "login"