# products/models.py
from django.db import models
from django.core.validators import MinValueValidator

# Categoría de productos
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.count()

class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    description = models.TextField(blank=True)
    unit = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=4)  # Precio fijo si no es variable
    categories = models.ManyToManyField('Category', related_name='products')
    is_variable = models.BooleanField(default=False)  # Define si el producto tiene variaciones
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


# Atributos dinámicos, como "estado de maduración"
class Attribute(models.Model):
    name = models.CharField(max_length=100)  # Ejemplo: "Estado de maduración"

    def __str__(self):
        return self.name

# Opciones de los atributos, como "verde", "maduro"
class AttributeOption(models.Model):
    attribute = models.ForeignKey(Attribute, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Ejemplo: "Verde"

    def __str__(self):
        return f"{self.attribute.name} - {self.name}"

# Variaciones de productos (cada variación puede tener diferentes combinaciones de atributos)
class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name='variations', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # Relación ManyToMany para combinar diferentes opciones de atributos
    attribute_options = models.ManyToManyField(AttributeOption, related_name='variations')

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    def get_attribute_summary(self):
        return ", ".join([str(option) for option in self.attribute_options.all()])
