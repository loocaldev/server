# Serializer.py
from rest_framework import serializers
from .models import Order, OrderItem
from products.models import ProductVariation
from products.serializer import ProductVariationSerializer

class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = ['id', 'name', 'price']

class OrderItemSerializer(serializers.ModelSerializer):
    product_variation = ProductVariationSerializer()

    class Meta:
        model = OrderItem
        fields = ['product_variation', 'quantity', 'unit_price', 'subtotal', 'tax']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Incluir los items de la orden

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'email', 'phone', 'custom_order_id', 'subtotal', 'created_at', 'updated_at', 'payment_status', 'shipping_status', 'items']