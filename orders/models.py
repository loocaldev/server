from django.db import models

# Create your models here.

class Order(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    products = models.ManyToManyField('products.Product')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Otros campos relevantes para tu modelo de orden

    def __str__(self):
        return f'Order {self.pk}'