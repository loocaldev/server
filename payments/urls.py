from django.urls import path
from . import views

urlpatterns = [
    path('tokenize_card/', views.create_payment_token, name='tokenize_card'),
    path('create_transaction/', views.create_wompi_transaction, name='create_transaction'),
]
