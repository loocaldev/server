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
    path('api/orders/', include('orders.urls')), 
    path('api/payments/', include('payments.urls')),
    path('api/login/', views.login, name='login'),  # Login
    path('api/register/', views.register, name='register'),  # Registro
    path('api/profile/', views.profile, name='profile'),  # Perfil
    path('api/logout/', views.logout, name='logout'),  # Logout
    path('api/update_user/', views.update_user, name='update_user'),
    path('api/add_address/', views.add_address, name='add_address'),
    path('api/get_addresses/', views.get_addresses, name='get_addresses'),
    path('api/delete_address/<int:pk>/', views.delete_address, name='delete_address'),
    path('api/update_address/<int:pk>/', views.update_address, name='update_address'),
    path('api/change_password/', views.change_password, name='change_password'),
    path('api/forgot_password/', views.forgot_password, name='forgot_password'),
    path('api/reset_password/', views.reset_password, name='reset_password'),
    path('api/send_verification_code/', views.send_verification_code, name='send_verification_code'),
    path('api/verify_code/', views.verify_code, name='verify_code'),
    path('api/send_email_verification_code/', views.send_email_verification_code, name='send_email_verification_code'),
    path('api/verify_email_otp/', views.verify_email_otp, name='verify_email_otp'),
    path('api/check_user/', views.check_user, name='check_user'),
    path('api/companies/', include('companies.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)