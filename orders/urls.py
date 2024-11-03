from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from orders import views

# Configura el router sin prefijo adicional
router = routers.DefaultRouter()
router.register(r'', views.OrderView, basename='order')

urlpatterns = [
    path('customid/<str:custom_order_id>/', views.OrderByCustomOrderIdAPIView.as_view(), name='order-by-custom-order-id'),
    path('', include(router.urls)),  # Incluye el router sin prefijo adicional
    path("docs/", include_docs_urls(title="Orders API")),
]
