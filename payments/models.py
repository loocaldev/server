from django.db import models

class Payment(models.Model):
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    token = models.CharField(max_length=255)  # Token de Wompi
    description = models.TextField()
    installments = models.IntegerField(default=1)
    payment_method_id = models.CharField(max_length=100)  # Tarjeta de crédito, Nequi, etc.
    payer_email = models.EmailField()
    status = models.CharField(max_length=50, default='pending')  # Estado del pago
    transaction_id = models.CharField(max_length=255, blank=True, null=True)  # ID de la transacción de Wompi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"
