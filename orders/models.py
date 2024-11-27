# orders/models.py
from django.db import models
from django.conf import settings
from products.models import Product, ProductVariation
from loocal.models import Address
from companies.models import Company
from decimal import Decimal
from django.utils.timezone import now


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
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente de Pago'),
        ('in_progress', 'En Progreso'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ]

    SHIPPING_STATUS_CHOICES = [
        ('pending_preparation', 'Pendiente de Preparación'),
        ('preparing', 'Preparando para Envío'),
        ('ready_to_ship', 'Listo para Despacho'),
        ('in_transit', 'En Camino'),
        ('delivered', 'Entregado'),
        ('returned', 'Devuelto'),
    ]

    GENERAL_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_preparation', 'En Preparación'),
        ('in_transit', 'En Tránsito'),
        ('delivered_paid', 'Entregada (Pagada)'),
        ('delivered_pending_payment', 'Entregada (Pendiente de Pago)'),
        ('canceled', 'Cancelada'),
        ('returned', 'Devuelta'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online'),
        ('in_person', 'In-person'),
    ]

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
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='online',
        verbose_name="Método de Pago",
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending'
    )
    shipping_status = models.CharField(
        max_length=20, choices=SHIPPING_STATUS_CHOICES, default='pending_preparation'
    )
    order_status = models.CharField(max_length=30, choices=GENERAL_STATUS_CHOICES, default='pending')
    updated_at = models.DateTimeField(auto_now=True)
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
    
    def save(self, *args, **kwargs):
        # Determina si se está actualizando el estado general
        update_status = kwargs.pop('update_status', True)

        if self.pk:  # Solo realiza las verificaciones si el objeto ya existe
            old_order = Order.objects.get(pk=self.pk)

            # Registro de cambios en `payment_status`
            if old_order.payment_status != self.payment_status:
                OrderStatusChangeLog.objects.create(
                    order=self,
                    previous_status=old_order.payment_status,
                    new_status=self.payment_status,
                    field_changed='payment_status'
                )

            # Registro de cambios en `shipping_status`
            if old_order.shipping_status != self.shipping_status:
                OrderStatusChangeLog.objects.create(
                    order=self,
                    previous_status=old_order.shipping_status,
                    new_status=self.shipping_status,
                    field_changed='shipping_status'
                )

        # Evita un ciclo infinito al actualizar el estado general
        if update_status:
            self.update_general_status(save_instance=False)

        super().save(*args, **kwargs)

    
    def update_general_status(self, save_instance=True):
        """
        Actualiza el estado general de la orden según los estados de pago y despacho.
        """
        if self.payment_status == 'refunded' or self.payment_status == 'failed':
            self.general_status = 'canceled'
        elif self.payment_status == 'paid' and self.shipping_status == 'delivered':
            self.general_status = 'delivered_paid'
        elif self.payment_status == 'pending' and self.shipping_status == 'delivered':
            self.general_status = 'delivered_pending_payment'
        elif self.payment_status == 'paid' and self.shipping_status == 'in_transit':
            self.general_status = 'in_transit'
        elif self.payment_status == 'pending' and self.shipping_status in ['pending_preparation', 'in_transit']:
            self.general_status = 'in_preparation'
        elif self.shipping_status == 'returned':
            self.general_status = 'returned'
        else:
            self.general_status = 'pending'

        # Guarda solo si se especifica explícitamente
        if save_instance:
            self.save(update_status=False)
    
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


class OrderStatusChangeLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    previous_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    field_changed = models.CharField(max_length=20)  # 'payment_status', 'shipping_status', or 'general_status'
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.field_changed} changed from {self.previous_status} to {self.new_status} on {self.timestamp}"