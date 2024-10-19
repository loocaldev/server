# products/views.py
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
