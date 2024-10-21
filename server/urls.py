"""
URL configuration for loocal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# urls.py 

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/products/',include('products.urls')),
    path('api/orders/',include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    re_path('api/login', views.login),
    re_path('api/register', views.register),
    re_path('api/profile', views.profile),
    re_path('api/logout', views.logout),
    path('api/add_address/', views.add_address, name='add_address'),
    path('api/get_addresses/', views.get_addresses, name='get_addresses'),
    path('api/update_user/', views.update_user, name='update_user'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)