# orders/models.py
from django.db import models
from products.models import Product, ProductVariation
from loocal.models import Address 


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('absolute', 'Absoluto'),  # Descuento en valor monetario
        ('percentage', 'Porcentaje'),  # Descuento en porcentaje
    ]

    code = models.CharField(max_length=20, unique=True)
    discount_value = models.DecimalField(max_digits=6, decimal_places=2)  # Valor del descuento
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='absolute')  # Tipo de descuento
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    max_uses_per_user = models.PositiveIntegerField(null=True, blank=True)
    max_uses_total = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10,
        choices=[('active', 'Vigente'), ('expired', 'Expirado'), ('redeemed', 'Redimido'), ('suspended', 'Suspendido')],
        default='active'
    )

    def __str__(self):
        return f"{self.code} - {self.discount_type} - {self.discount_value}"

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
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='orders')
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Valor de descuento aplicado
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total final después de aplicar descuento

    # Campos para la fecha y hora de entrega
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.custom_order_id} - {self.firstname} {self.lastname} (${self.subtotal})"
    
    def calculate_total(self):
        if self.discount:
            if self.discount.discount_type == 'percentage':
                self.discount_value = (self.subtotal * self.discount.discount_value / 100).quantize(self.subtotal)
            else:
                self.discount_value = self.discount.discount_value

            # Asegurarnos de que el total no sea menor a 0
            self.total = max(self.subtotal - self.discount_value, 0)
        else:
            self.total = self.subtotal

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order.custom_order_id} - {self.product.name} ({self.quantity} units)"