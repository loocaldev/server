# orders/models.py
from django.db import models
from products.models import Product, ProductVariation

class Order(models.Model):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    custom_order_id = models.CharField(max_length=100, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    shipping_status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('shipped', 'Shipped'), ('delivered', 'Delivered')],
        default='pending'
    )

    def __str__(self):
        return self.custom_order_id

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Permitir productos fijos
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True)  # Variación opcional
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Impuesto opcional

    def __str__(self):
        return f"Order {self.order.custom_order_id} - {self.product.name if not self.product_variation else self.product_variation.product.name}"
