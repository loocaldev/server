from django.db import models

# Create your models here.

class Payment(models.Model):
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    token = models.CharField(max_length=255)
    description = models.TextField()
    installments = models.IntegerField()
    payment_method_id = models.CharField(max_length=100)
    payer_email = models.EmailField()
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"Payment {self.id} - {self.status}"
