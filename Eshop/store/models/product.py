from django.db import models
from .Category import Category

class Product(models.Model):
    name=models.CharField(max_length=255)
    description=models.TextField()
    price=models.DecimalField(max_digits=10, decimal_places=2)
    image=models.ImageField(upload_to='product_images/')
    category=models.ForeignKey(Category, on_delete=models.CASCADE,default=1)
 

    def __str__(self):
        return self.name
    @staticmethod
    def get_all_products():
        return Product.objects.all()
    
    @staticmethod
    def get_all_products_by_categoryid(category_id):
        if category_id:
            return Product.objects.filter(category_id=category_id)
        else:
            return Product.get_all_products()