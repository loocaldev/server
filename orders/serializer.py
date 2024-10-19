# orders/serializer.py
from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product, ProductVariation
from products.serializer import ProductVariationSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_variation = ProductVariationSerializer(required=False, allow_null=True)  # Permitir variación opcional

    class Meta:
        model = OrderItem
        fields = ['product', 'product_variation', 'quantity', 'unit_price', 'subtotal', 'tax']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Incluir los items de la orden

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'email', 'phone', 'custom_order_id', 'subtotal', 'created_at', 'updated_at', 'payment_status', 'shipping_status', 'items']
