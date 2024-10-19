from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_categories(self, obj):
        return obj.get_categories_list()  # Devuelve las categorías como una lista