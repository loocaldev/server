from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    description = models.TextField(blank=True)
    is_variable = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='products')
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name

class UnitType(models.Model):
    name = models.CharField(max_length=50)  # Ejemplo: "Peso", "Unidad", "Volumen"

    def __str__(self):
        return self.name

class Attribute(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class AttributeOption(models.Model):
    attribute = models.ForeignKey(Attribute, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.attribute.name} - {self.name}"

class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name='variations', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='variation_images/', null=True, blank=True)
    attribute_options = models.ManyToManyField(AttributeOption, related_name='variations')
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE, null=True)
    unit_quantity = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    contenido_peso = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Campos para la promoción
    is_on_promotion = models.BooleanField(default=False)
    discount_type = models.CharField(max_length=10, choices=[('percentage', 'Percentage'), ('value', 'Value')], null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        options = ", ".join([str(option) for option in self.attribute_options.all()])
        return f"{self.product.name} - {options} - SKU: {self.sku} - {self.unit_quantity} {self.unit_type.name}"

    @property
    def final_price(self):
        """Calcula el precio final aplicando el descuento si está en promoción."""
        if self.is_on_promotion and self.discount_value:
            if self.discount_type == 'percentage':
                discount = (self.discount_value / 100) * self.price
            elif self.discount_type == 'value':
                discount = self.discount_value
            else:
                discount = 0
            return max(self.price - discount, 0)  # Asegura que el precio no sea negativo
        return self.price

    def save(self, *args, **kwargs):
        # Crea o asigna la categoría de promoción si está en promoción
        promotion_category, created = Category.objects.get_or_create(name="Promoción")
        if self.is_on_promotion:
            self.product.categories.add(promotion_category)
        else:
            self.product.categories.remove(promotion_category)
        super().save(*args, **kwargs)
