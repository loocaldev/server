# urls.py
from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductView)
router.register(r'categories', views.CategoryView)
router.register(r'attributes', views.AttributeView)
router.register(r'variations', views.ProductVariationView)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
