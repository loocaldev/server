from django.urls import path
from . import views

urlpatterns = [
    # Crear una empresa
    path('create/', views.create_company, name='create_company'),
    # Invitar a un miembro
    path('<uuid:company_id>/invite/', views.invite_member, name='invite_member'),
    # Aceptar una invitación con autenticación (usuarios registrados)
    path('<uuid:company_id>/accept-invitation/', views.accept_invitation, name='accept_invitation'),
    # Aceptar una invitación y completar registro (usuarios no registrados)
    path('<uuid:company_id>/accept-invitation/<str:token>/', views.accept_invitation_register, name='accept_invitation_register'),
]
