from django.db import models

class Customer(models.Model):
    first_name = models.CharField(max_length=50)  
    last_name = models.CharField(max_length=50)  
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    password = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"