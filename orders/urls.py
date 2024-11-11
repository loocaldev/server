from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from orders import views

router = routers.DefaultRouter()
router.register(r'order', views.OrderView, basename='order')

urlpatterns = [
    path('apply-discount/', views.apply_discount, name='apply-discount'),
    path('customid/<str:custom_order_id>/', views.OrderByCustomOrderIdAPIView.as_view(), name='order-by-custom-order-id'),
    path('', include(router.urls)),  # Las rutas de OrderView ahora estarán bajo 'order/'
    path("docs/", include_docs_urls(title="Orders API")),
]
