# orders/models.py
from django.db import models
from products.models import Product, ProductVariation
from loocal.models import Address 


class Discount(models.Model):
    code = models.CharField(max_length=20, unique=True)  # Código alfanumérico
    discount_value = models.DecimalField(max_digits=6, decimal_places=2)  # Valor del descuento
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Valor mínimo de orden
    start_date = models.DateField()  # Fecha de inicio de validez
    end_date = models.DateField()  # Fecha de fin de validez
    max_uses_per_user = models.PositiveIntegerField(null=True, blank=True)  # Límite de usos por usuario
    max_uses_total = models.PositiveIntegerField(null=True, blank=True)  # Límite total de usos
    times_used = models.PositiveIntegerField(default=0)  # Veces que se ha usado el descuento
    status = models.CharField(
        max_length=10,
        choices=[('active', 'Vigente'), ('expired', 'Expirado'), ('redeemed', 'Redimido'), ('suspended', 'Suspendido')],
        default='active'
    )

    def __str__(self):
        return f"{self.code} - {self.discount_value}"

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
            self.total = self.subtotal - self.discount_value
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