# admin.py
from django.contrib import admin
from .models import Product, Category, Attribute, AttributeOption, ProductVariation, UnitType, UnitTypeAggregation
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Inline para opciones de atributos en el administrador de atributos
class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1

class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeOptionInline]

# Inline para variaciones de producto en el administrador de productos
class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1
    fields = [
        'sku', 'price', 'final_price', 'stock', 'unit_type', 'unit_quantity',
        'is_on_promotion', 'discount_type', 'discount_value'
    ]
    readonly_fields = ['final_price']

# Recursos para importación/exportación de productos
class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = (
            'name', 'description', 'price', 'is_variable', 'unit_type__name', 
            'unit_quantity', 'categories__name', 'is_on_promotion', 
            'discount_type', 'discount_value', 'image'
        )

class ProductVariationResource(resources.ModelResource):
    product_name = resources.Field(attribute='product__name', column_name='product_name')

    class Meta:
        model = ProductVariation
        fields = (
            'product_name', 'sku', 'price', 'stock', 'unit_type__name', 
            'unit_quantity', 'is_on_promotion', 'discount_type', 'discount_value', 
            'image', 'attribute_options__name'
        )

# Configuración del administrador de productos
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    inlines = [ProductVariationInline]

# Configuración del administrador de variaciones de productos
@admin.register(ProductVariation)
class ProductVariationAdmin(ImportExportModelAdmin):
    resource_class = ProductVariationResource
    list_display = ('sku', 'product', 'price', 'final_price', 'is_on_promotion', 'discount_type', 'discount_value', 'stock')
    list_filter = ('is_on_promotion', 'discount_type')
    readonly_fields = ['final_price']
    fields = [
        'product', 'sku', 'price', 'stock', 'image', 'attribute_options', 'unit_type', 
        'unit_quantity', 'contenido_peso', 'is_on_promotion', 'discount_type', 'discount_value', 'final_price'
    ]

# Otros registros
admin.site.register(Category)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(UnitType)
admin.site.register(UnitTypeAggregation)
