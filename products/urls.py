# urls.py
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from products import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductView)
router.register(r'categories', views.CategoryView)  # Nueva ruta para categorías

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("docs/", include_docs_urls(title="Products API"))
]
