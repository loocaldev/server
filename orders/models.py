# orders/models.py
from django.db import models
from django.conf import settings
from products.models import Product, ProductVariation
from loocal.models import Address
from companies.models import Company
from decimal import Decimal

STATUS_CHOICES = [
    ("pending", "Pendiente"),
    ("approved", "Aprobada"),
    ("rejected", "Rechazada"),
    ("failed", "Fallida"),
]


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("absolute", "Absoluto"),  # Descuento en valor monetario
        ("percentage", "Porcentaje"),  # Descuento en porcentaje
    ]

    code = models.CharField(max_length=20, unique=True)
    discount_value = models.DecimalField(
        max_digits=6, decimal_places=2
    )  # Valor del descuento
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="absolute"
    )  # Tipo de descuento
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    max_uses_per_user = models.PositiveIntegerField(null=True, blank=True)
    max_uses_total = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    applicable_to_transport = models.BooleanField(
        default=False, verbose_name="Aplica al transporte"
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("active", "Vigente"),
            ("expired", "Expirado"),
            ("redeemed", "Redimido"),
            ("suspended", "Suspendido"),
        ],
        default="active",
    )

    def __str__(self):
        return f"{self.code} - {self.discount_type} - {self.discount_value}"


class UserDiscount(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )  # Relaciona el usuario registrado, si aplica
    email = (
        models.EmailField()
    )  # Utiliza el email en caso de que el usuario no esté registrado
    discount = models.ForeignKey(
        Discount, on_delete=models.CASCADE, related_name="user_discounts"
    )
    times_used = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("email", "discount")  # Evita duplicados de usuario/descuento

    def __str__(self):
        return f"{self.email} - {self.discount.code} (Used {self.times_used} times)"


class Order(models.Model):
    firstname = models.CharField(max_length=50, null=True, blank=True)
    lastname = models.CharField(max_length=50, null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)  # Para empresas
    document_type = models.CharField(max_length=10, null=True, blank=True)  # Tipo de documento
    document_number = models.CharField(max_length=20, null=True, blank=True)  # Número de documento
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    custom_order_id = models.CharField(max_length=255, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    payment_status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("in progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    shipping_status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
        ],
        default="pending",
    )
    transport_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, verbose_name="Costo de envio"
    )
    address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_on_transport = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )  # Total final después de aplicar descuento

    # Campos para la fecha y hora de entrega
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time = models.TimeField(null=True, blank=True)
    
    def calculate_total(self):
        self.discount_value = self.discount_value or Decimal("0.0")
        self.transport_cost = self.transport_cost or Decimal("0.0")
        self.discount_on_transport = self.discount_on_transport or Decimal("0.0")
        
        # Validar que los descuentos no superen los valores correspondientes
        self.discount_on_transport = min(self.discount_on_transport, self.transport_cost)
        self.discount_value = min(self.discount_value, self.subtotal)

        if self.discount:
            if self.discount.discount_type == "percentage":
                self.discount_value = Decimal(self.subtotal) * (
                    Decimal(self.discount.discount_value) / Decimal("100")
                )
            else:
                self.discount_value = Decimal(self.discount.discount_value)

            # Total después del descuento
            self.total = max(
                Decimal(self.subtotal)
                + Decimal(self.transport_cost)
                - Decimal(self.discount_value)
                - Decimal(self.discount_on_transport),
                Decimal("0.0"),
            )
        else:
            # Total sin descuento
            self.total = Decimal(self.subtotal) + Decimal(self.transport_cost)

    def __str__(self):
        return f"Order {self.custom_order_id} - {self.firstname or self.company_name} (${self.subtotal})"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variation = models.ForeignKey(
        ProductVariation, on_delete=models.CASCADE, null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order.custom_order_id} - {self.product.name} ({self.quantity} units)"
