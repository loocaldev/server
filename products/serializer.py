# serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Product, Category, Attribute, AttributeOption, ProductVariation, UnitTypeAggregation

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

class AttributeOptionSerializer(serializers.ModelSerializer):
    attribute = serializers.StringRelatedField()  # Incluimos el nombre del atributo

    class Meta:
        model = AttributeOption
        fields = ['id', 'name', 'attribute']  # Aseguramos que se incluye el atributo

class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'options']

class ProductVariationSerializer(serializers.ModelSerializer):
    attribute_data = serializers.SerializerMethodField()
    unit_type = serializers.SerializerMethodField()
    unit_quantity = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariation
        fields = [
            'id', 'sku', 'price', 'final_price', 'stock', 'image',
            'attribute_data', 'is_on_promotion', 'discount_type', 'discount_value',
            'unit_type', 'unit_quantity'
        ]

    def get_unit_type(self, obj):
        # Devuelve unit_type de la variación o el del producto si no está en la variación
        return obj.unit_type.name if obj.unit_type else obj.product.unit_type.name

    def get_unit_quantity(self, obj):
        # Devuelve unit_quantity de la variación o el del producto si no está en la variación
        return obj.unit_quantity if obj.unit_quantity else obj.product.unit_quantity

    def get_attribute_data(self, obj):
        # Agrupa las opciones de atributos por cada atributo.
        attribute_dict = {}
        for option in obj.attribute_options.all():
            attribute_name = option.attribute.name
            if attribute_name not in attribute_dict:
                attribute_dict[attribute_name] = []
            attribute_dict[attribute_name].append({
                "id": option.id,
                "name": option.name,
            })
        return attribute_dict
    
class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    unit_type = serializers.StringRelatedField()
    unit_quantity = serializers.DecimalField(max_digits=6, decimal_places=2)
    converted_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'image', 'description', 'price', 'categories',
            'is_variable', 'variations', 'created_at', 'updated_at',
            'unit_type', 'unit_quantity', 'converted_quantity'
        ]

    def get_converted_quantity(self, instance):
        requested_unit = self.context.get('requested_unit')
        if requested_unit:
            try:
                return instance.get_converted_quantity(to_unit_name=requested_unit)
            except ValidationError as e:
                return str(e)
        return instance.unit_quantity

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Sobreescribir el precio si el producto no es variable
        if not instance.is_variable:
            representation['price'] = instance.price

        return representation