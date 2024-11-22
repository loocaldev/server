from rest_framework import serializers
from .models import Order, OrderItem, Discount
from products.serializer import ProductVariationSerializer
from loocal.serializers import AddressSerializer
from django.utils import timezone

class OrderItemSerializer(serializers.ModelSerializer):
    product_variation = ProductVariationSerializer(required=False, allow_null=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'product_variation', 'quantity', 'unit_price', 'subtotal', 'tax']  # Agregamos `unit_price` y `subtotal`

class OrderSerializer(serializers.ModelSerializer):
    address = AddressSerializer()  # Serializamos la dirección
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'email', 'phone', 'custom_order_id', 'subtotal', 'address', 'delivery_date', 'delivery_time', 'payment_status', 'shipping_status', 'items', 'created_at']
        
class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['code', 'discount_value', 'discount_type', 'min_order_value', 'start_date', 'end_date', 'max_uses_per_user', 'max_uses_total', 'times_used', 'status']

class OrderSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    items = OrderItemSerializer(many=True)
    discount = DiscountSerializer(required=False, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'firstname', 'lastname', 'company_name', 'document_type', 'document_number',
            'email', 'phone', 'custom_order_id', 'subtotal', 'discount', 'discount_value',
            'total', 'address', 'delivery_date', 'delivery_time', 'payment_status',
            'shipping_status', 'items', 'created_at'
        ]

    # Validación de código de descuento en la creación o actualización
    def validate_discount(self, discount_code):
        try:
            discount = Discount.objects.get(code=discount_code, status='active')
            if discount.end_date < timezone.now().date():
                raise serializers.ValidationError("El descuento ha expirado.")
            return discount
        except Discount.DoesNotExist:
            raise serializers.ValidationError("Código de descuento no válido o inactivo.")