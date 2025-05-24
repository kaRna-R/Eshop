from django.contrib import admin
from .models.product import Product
from.models.Category import Category
from .models.customer import Customer

class ProductAdmin(admin.ModelAdmin):
    list_display=['name','price','category']

class CategoryAdmin(admin.ModelAdmin):
    list_display=['name',]

class CustomerAdmin(admin.ModelAdmin):
    list_display=['first_name',]

# Register your models here.
admin.site.register(Product,ProductAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Customer,CustomerAdmin)
