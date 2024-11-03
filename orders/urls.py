from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from orders import views

# No incluyas el prefijo `orders` aquí
router = routers.DefaultRouter()
router.register(r'', views.OrderView)  # Sin prefijo

urlpatterns = [
    path('api/orders/customid/<str:custom_order_id>/', views.OrderByCustomOrderIdAPIView.as_view(), name='order-by-custom-order-id'),
    path('api/orders/', include(router.urls)),  # Ajustar la URL principal
    path("docs/", include_docs_urls(title="Orders API"))
]
