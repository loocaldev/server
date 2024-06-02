from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from payments import views

from django.urls import path
from . import views

urlpatterns = [
    path('generate_integrity_hash/', views.generate_integrity_hash, name='generate_integrity_hash'),
]