from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from orders import views

router = routers.DefaultRouter()
router.register(r'orders',views.OrderView)

urlpatterns = [
    path("api/v1/",include(router.urls)),
    path("docs/", include_docs_urls(title="Orders API"))
]