# serializers.py
from rest_framework import serializers
from .models import Product, Category, Attribute, AttributeOption, ProductVariation

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
            'id', 'sku', 'price', 'final_price', 'stock', 'image', 'attribute_options',
            'unit_type', 'unit_quantity', 'is_on_promotion', 'discount_type', 'discount_value'
        ]

class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'image', 'description', 'price', 'categories', 'is_variable',
            'variations', 'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not instance.is_variable:
            representation['price'] = instance.price
        return representation
