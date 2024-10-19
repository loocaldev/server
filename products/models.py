from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    description = models.TextField(blank=True)
    unit = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=4)
    categories = models.CharField(max_length=255, blank=True)  # Campo de categorías
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_categories_list(self):
        return [cat.strip() for cat in self.categories.split(',') if cat.strip()]

    
    