from rest_framework import serializers
from .models import Order, OrderItem
from products.serializer import ProductVariationSerializer
from loocal.serializers import AddressSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_variation = ProductVariationSerializer(required=False, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_variation', 'quantity', 'unit_price', 'subtotal', 'tax']  # Agregamos `unit_price` y `subtotal`

class OrderSerializer(serializers.ModelSerializer):
    address = AddressSerializer()  # Serializamos la dirección
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'email', 'phone', 'custom_order_id', 'subtotal', 'address', 'delivery_date', 'delivery_time', 'payment_status', 'shipping_status', 'items']