# models/cart.py

from django.db import models
from .customer import Customer
from .product import Product

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)

    def total_price(self):
        return self.product.price * self.quantity