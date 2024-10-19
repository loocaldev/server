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

    class Meta:
        model = ProductVariation
        fields = ['id', 'sku', 'price', 'stock', 'image', 'attribute_options']  # Incluimos la imagen de la variación

class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)  # Mostrar las variaciones con sus atributos

    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'description', 'unit', 'categories', 'is_variable', 'variations', 'created_at', 'updated_at']

    def to_representation(self, instance):
        # Si el producto no es variable, incluir el precio
        representation = super().to_representation(instance)
        if not instance.is_variable:
            representation['price'] = instance.price
        return representation
