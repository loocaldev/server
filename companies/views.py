from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Company, CompanyMembership
from .serializers import CompanySerializer, CompanyMembershipSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from django.contrib.auth import login
from datetime import timedelta
from django.utils.timezone import now


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_company(request):
    data = request.data
    serializer = CompanySerializer(data=data)
    if serializer.is_valid():
        # Agrega el usuario autenticado como `created_by`
        serializer.save(created_by=request.user)
        # Agrega al creador como miembro con rol "owner"
        CompanyMembership.objects.create(user=request.user, company=serializer.instance, role='owner', invitation_accepted=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def invite_member(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if not CompanyMembership.objects.filter(user=request.user, company=company, role='owner').exists():
        return Response({"error": "No tienes permisos para invitar usuarios a esta empresa."}, status=403)

    email = request.data.get('email')
    if not email:
        return Response({"error": "El campo 'email' es requerido."}, status=400)

    # Buscar o crear el usuario
    user, created = User.objects.get_or_create(email=email, defaults={'username': email, 'is_active': False})
    if created:
        user.set_unusable_password()  # Usuario no registrado no puede iniciar sesión aún
        user.save()

    # Buscar membresía existente
    membership = CompanyMembership.objects.filter(user=user, company=company).first()

    if membership:
        if membership.invitation_accepted:
            return Response({"error": "El usuario ya pertenece a la empresa."}, status=400)

        # Actualizar token de invitación si no ha sido aceptada
        membership.invitation_token = get_random_string(32)
        membership.invitation_created_at = now()
        membership.save()
    else:
        # Crear nueva invitación
        membership = CompanyMembership.objects.create(
            user=user,
            company=company,
            role='member',
            invited_by=request.user,
            invitation_token=get_random_string(32),
            invitation_created_at=now()
        )

    # Crear URL de aceptación
    accept_url = f"https://loocal.co/accept-invitation/{company.id}/{membership.invitation_token}/"

    # Enviar correo de invitación
    try:
        send_mail(
            subject=f"Invitación para unirte a {company.name}",
            message=(
                f"Hola,\n\n"
                f"Has sido invitado a unirte a la empresa '{company.name}' en nuestra plataforma Loocal.\n\n"
                f"Por favor, haz clic en el siguiente enlace para aceptar la invitación y completar tu registro:\n\n"
                f"{accept_url}\n\n"
                f"Si no reconoces esta invitación, ignora este correo."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        return Response({"error": f"No se pudo enviar el correo: {str(e)}"}, status=500)

    return Response({"message": "Invitación enviada exitosamente."}, status=200)



@api_view(['POST'])
def accept_invitation_register(request, company_id, token):
    company = get_object_or_404(Company, id=company_id)
    email = request.data.get('email')
    password = request.data.get('password')
    user = User.objects.filter(email=email).first()

    if not user:
        return Response({"error": "La invitación no es válida o el usuario no existe."}, status=400)

    # Validar la invitación
    membership = CompanyMembership.objects.filter(user=user, company=company, invitation_token=token).first()
    if not membership:
        return Response({"error": "La invitación no es válida."}, status=400)

    # Verificar si el token ha expirado (48 horas)
    if now() > membership.invitation_created_at + timedelta(hours=48):
        return Response({"error": "El enlace de invitación ha expirado."}, status=400)

    # Completar el registro
    user.set_password(password)
    user.is_active = True
    user.save()

    # Marcar la invitación como aceptada
    membership.invitation_accepted = True
    membership.invitation_token = None  # Eliminar el token después de usarlo
    membership.save()

    return Response({"message": "Invitación aceptada y registro completado exitosamente."}, status=200)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def accept_invitation(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    membership = get_object_or_404(CompanyMembership, user=request.user, company=company)

    if membership.invitation_accepted:
        return Response({"error": "Ya aceptaste esta invitación."}, status=400)

    membership.invitation_accepted = True
    membership.save()
    return Response({"message": "Invitación aceptada exitosamente."}, status=200)
