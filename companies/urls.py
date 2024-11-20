from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_company, name='create_company'),
    path('<uuid:company_id>/invite/', views.invite_member, name='invite_member'),
    path('<uuid:company_id>/accept-invitation/', views.accept_invitation, name='accept_invitation'),
]
