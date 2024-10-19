# serializers.py
from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='product_count', read_only=True)  # Contar productos asociados

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)  # Incluir categorías en el serializador de productos

    class Meta:
        model = Product
        fields = '__all__'
