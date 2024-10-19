# products/admin.py
from django.contrib import admin
from .models import Product, Category, Attribute, AttributeOption, ProductVariation

class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1

class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeOptionInline]

class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariationInline]

admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(ProductVariation)
