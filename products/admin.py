# admin.py
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
    fields = [
        'sku', 'price', 'final_price', 'stock', 'unit_type', 'unit_quantity',
        'is_on_promotion', 'discount_type', 'discount_value'
    ]
    readonly_fields = ['final_price']

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariationInline]

class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'price', 'final_price', 'is_on_promotion', 'discount_type', 'discount_value', 'stock')
    list_filter = ('is_on_promotion', 'discount_type')
    readonly_fields = ['final_price']
    fields = [
        'product', 'sku', 'price', 'stock', 'image', 'attribute_options', 'unit_type', 
        'unit_quantity', 'contenido_peso', 'is_on_promotion', 'discount_type', 'discount_value', 'final_price'
    ]

admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(ProductVariation, ProductVariationAdmin)
