# serializers.py
from rest_framework import serializers
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
    converted_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'image', 'description', 'price', 'categories', 'is_variable',
            'variations','converted_quantity', 'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Calcular la cantidad convertida, si la unidad se especifica en el contexto
        requested_unit = self.context.get('requested_unit')
        if requested_unit:
            representation['converted_quantity'] = instance.get_converted_quantity(to_unit_name=requested_unit)
        else:
            # Si no hay una unidad solicitada, muestra la cantidad en su unidad base
            representation['converted_quantity'] = instance.unit_quantity

        # Si el producto no es variable, incluir el precio en la representación
        if not instance.is_variable:
            representation['price'] = instance.price

        return representation
