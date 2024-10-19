from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

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
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)  # Imagen general para productos fijos
    description = models.TextField(blank=True)
    unit = models.TextField(blank=True)  # Unidad predeterminada si no es variable
    price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)  # Precio predeterminado para productos no variables
    categories = models.ManyToManyField('Category', related_name='products')
    is_variable = models.BooleanField(default=False)  # Define si el producto es variable
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def has_variations(self):
        return self.variations.exists()
    
    def clean(self):
        # Los productos variables no deben tener un precio general
        if self.is_variable and self.price is not None:
            raise ValidationError("Los productos variables no deben tener un precio general.")

class Attribute(models.Model):
    name = models.CharField(max_length=100)  # Ejemplo: "Maduración", "Presentación"

    def __str__(self):
        return self.name

class AttributeOption(models.Model):
    attribute = models.ForeignKey(Attribute, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Ejemplo: "Maduro", "Verde", "Por paquete", "Por peso"

    def __str__(self):
        return f"{self.attribute.name} - {self.name}"

class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name='variations', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Cada variación tiene su precio específico
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])  # Stock de la variación
    image = models.ImageField(upload_to='variation_images/', null=True, blank=True)  # Imagen específica de la variación
    attribute_options = models.ManyToManyField(AttributeOption, related_name='variations')  # Combinación de atributos

    def __str__(self):
        options = ", ".join([str(option) for option in self.attribute_options.all()])
        return f"{self.product.name} - {options} - SKU: {self.sku}"

    def get_attribute_summary(self):
        return ", ".join([str(option) for option in self.attribute_options.all()])
