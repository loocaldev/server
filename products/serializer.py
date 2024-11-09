# serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Product, Category, Attribute, AttributeOption, ProductVariation, UnitTypeAggregation

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ['id', 'name']

class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'options']

class ProductVariationSerializer(serializers.ModelSerializer):
    attribute_options = AttributeOptionSerializer(many=True, read_only=True)
    unit_type = serializers.StringRelatedField()  # Muestra el nombre del tipo de unidad
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)  # Campo calculado

    class Meta:
        model = ProductVariation
        fields = [
            'id', 'sku', 'price', 'final_price', 'stock', 'image', 'attribute_options', 'is_on_promotion', 'discount_type', 'discount_value'
        ]

class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    unit_type = serializers.StringRelatedField()
    unit_quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    converted_quantity = serializers.SerializerMethodField()  # Definir como SerializerMethodField

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'image', 'description', 'price', 'categories', 'is_variable',
            'variations', 'created_at', 'updated_at', 'unit_type', 'unit_quantity', 'converted_quantity'
        ]

    def get_converted_quantity(self, instance):
        # Obtener la unidad solicitada del contexto
        requested_unit = self.context.get('requested_unit')
        if requested_unit:
            try:
                return instance.get_converted_quantity(to_unit_name=requested_unit)
            except ValidationError as e:
                return str(e)  # Muestra el error si la unidad no es válida
        return instance.unit_quantity  # Valor base si no hay unidad solicitada

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Sobreescribir el precio si el producto no es variable
        if not instance.is_variable:
            representation['price'] = instance.price

        return representation