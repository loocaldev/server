from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Nombre único de la categoría
    description = models.TextField(blank=True)  # Descripción opcional de la categoría

    def __str__(self):
        return self.name

    # Método para contar los productos asociados a la categoría
    @property
    def product_count(self):
        return self.products.count()  # 'products' es el nombre del campo ManyToMany en Product
    
class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    description = models.TextField(blank=True)
    unit = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=4)
    categories = models.ManyToManyField('Category', related_name='products')  # Relación ManyToMany con Category
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name
    