# views.py
from rest_framework import viewsets
from .serializer import (
    ProductSerializer, CategorySerializer, AttributeSerializer, ProductVariationSerializer
)
from .models import Product, Category, Attribute, ProductVariation

class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

class CategoryView(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

class AttributeView(viewsets.ModelViewSet):
    serializer_class = AttributeSerializer
    queryset = Attribute.objects.all()

class ProductVariationView(viewsets.ModelViewSet):
    serializer_class = ProductVariationSerializer
    queryset = ProductVariation.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtro adicional para mostrar solo variaciones en promoción si `is_on_promotion` está en los parámetros
        is_on_promotion = self.request.query_params.get('is_on_promotion', None)
        if is_on_promotion is not None:
            queryset = queryset.filter(is_on_promotion=is_on_promotion == 'true')
        return queryset
