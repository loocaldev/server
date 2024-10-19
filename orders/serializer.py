# Serializer.py
from rest_framework import serializers
from .models import Order
from products.models import ProductVariation

class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = ['id', 'name', 'price']

class OrderSerializer(serializers.ModelSerializer):
    product_variations = ProductVariationSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'
