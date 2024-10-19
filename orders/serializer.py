from rest_framework import serializers
from .models import Order, OrderItem
from products.serializer import ProductVariationSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_variation = ProductVariationSerializer(required=False, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_variation', 'quantity', 'unit_price', 'subtotal', 'tax']  # Agregamos `unit_price` y `subtotal`

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'email', 'phone', 'custom_order_id', 'subtotal', 'created_at', 'updated_at', 'payment_status', 'shipping_status', 'items']
