# views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from django.contrib.auth import authenticate, login as django_login
from rest_framework.response import Response
from .serializers import UserSerializer, UserProfileSerializer, AddressSerializer
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import UserProfile, Address
import datetime
from .services import send_email_otp, send_sms_otp, generate_otp
from . import signals
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import check_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.urls import reverse
from datetime import timedelta
from django.utils.timezone import now
from rest_framework_simplejwt.tokens import RefreshToken
import os
from twilio.rest import Client
from django.views.decorators.csrf import csrf_exempt

# Función para generar tokens
def get_tokens_for_user(user):
    print("Generating tokens for user:", user)
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@csrf_exempt  # Solo mientras depuras, remueve esto una vez que funcione.
@api_view(['POST'])
def login(request):
    print("Request data received:", request.data)

    username = request.data.get('username')
    password = request.data.get('password')
    print("Username:", username, "Password:", password)

    user = authenticate(username=username, password=password)
    if user:
        print("User authenticated:", user)
        tokens = get_tokens_for_user(user)
        serializer = UserSerializer(instance=user)
        return Response({
            "tokens": tokens,
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    else:
        print("Authentication failed")
        return Response({"error": "Credenciales inválidas."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register(request):
    email = request.data.get('username')
    password = request.data.get('password')

    user = User.objects.filter(email=email).first()

    if not user:
        return Response({"error": "Primero verifica tu correo electrónico."}, status=status.HTTP_400_BAD_REQUEST)

    user_profile = user.userprofile
    if not user_profile.is_email_verified:
        return Response({"error": "El correo electrónico no ha sido verificado."}, status=status.HTTP_400_BAD_REQUEST)

    # Configurar contraseña y activar usuario
    user.set_password(password)
    user.is_active = True
    user_profile.is_temporary = False  # Ya no es temporal
    user_profile.save()
    user.save()

    tokens = get_tokens_for_user(user)
    return Response({
        "tokens": tokens,
        "message": "Registro completado exitosamente."
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user

    # Asegurarse de que el perfil existe
    if not hasattr(user, 'userprofile'):
        UserProfile.objects.create(user=user)  # Crear un perfil si no existe

    serializer = UserSerializer(instance=user)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_address(request):
    user = request.user
    address_serializer = AddressSerializer(data=request.data)
    
    if address_serializer.is_valid():
        address_serializer.save(user=user)
        return Response(address_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_addresses(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    serializer = AddressSerializer(instance=addresses, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Sesión cerrada con éxito."}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_user(request):
    user = request.user

    # Actualizar campos de User
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    new_email = request.data.get('email')
    if new_email:
        user.email = new_email
        user.username = new_email  # Usamos el email como username

    # Actualizar la contraseña si se envía
    new_password = request.data.get('password')
    if new_password:
        user.set_password(new_password)

    # Guardar cambios en el modelo User
    user.save()

    # Procesar datos de UserProfile
    profile_data = request.data.get('profile', {})
    if profile_data:
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.document_type = profile_data.get('document_type', profile.document_type)
        profile.document_number = profile_data.get('document_number', profile.document_number)
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)

        # Si se envía una imagen de perfil
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        # Guardar cambios en UserProfile
        profile.save()

    return Response({"message": "Perfil actualizado exitosamente"}, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_address(request, pk):
    user = request.user
    address = get_object_or_404(Address, pk=pk, user=user)
    is_default = request.data.get("is_default", False)

    if is_default:
        # Si se marca esta dirección como principal, desmarcar otras del usuario
        Address.objects.filter(user=user, is_default=True).update(is_default=False)

    serializer = AddressSerializer(instance=address, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")

    if not check_password(current_password, user.password):
        return Response({"error": "Contraseña actual incorrecta"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Contraseña actualizada exitosamente"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    user = User.objects.filter(email=email).first()

    if not user:
        return Response({"error": "Correo electrónico no registrado."}, status=status.HTTP_400_BAD_REQUEST)

    user_profile = user.userprofile

    # Verificar si ya existe un token y está dentro del tiempo de validez
    if user_profile.reset_token and user_profile.reset_token_created_at + timedelta(hours=1) > now():
        token = user_profile.reset_token  # Reutilizar el token existente
    else:
        # Generar un nuevo token
        token = get_random_string(32)
        user_profile.reset_token = token
        user_profile.reset_token_created_at = now()
        user_profile.save()

    # Crear URL para restablecer contraseña en el frontend
    reset_url = f"https://loocal.co/reset-password?token={token}"

    # Enviar correo
    send_mail(
        'Recuperación de contraseña',
        f'Usa el siguiente enlace para restablecer tu contraseña: {reset_url}',
        'no-reply@loocal.co',
        [email],
        fail_silently=False,
    )
    return Response({"message": "Se ha reenviado el correo con las instrucciones para restablecer tu contraseña."})

@api_view(['POST'])
def reset_password(request):
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    user_profile = UserProfile.objects.filter(reset_token=token).first()

    if not user_profile:
        return Response({"error": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)

    # Verificar la expiración del token
    if user_profile.reset_token_created_at + timedelta(hours=1) < now():
        return Response({"error": "El token ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

    # Cambiar la contraseña del usuario
    user = user_profile.user
    user.set_password(new_password)
    user.save()

    # Limpiar el token después de usarlo
    user_profile.reset_token = None
    user_profile.save()

    return Response({"message": "Contraseña restablecida exitosamente."})

@api_view(['POST'])
def send_verification_code(request):
    phone_number = request.data.get('phone_number')
    if not phone_number:
        return Response({"error": "Número de teléfono requerido."}, status=status.HTTP_400_BAD_REQUEST)

    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    try:
        verification = client.verify.services(os.getenv('TWILIO_VERIFY_SERVICE_SID')) \
            .verifications \
            .create(to=phone_number, channel='sms')
        return Response({"message": "Código enviado exitosamente."})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def verify_code(request):
    phone_number = request.data.get('phone_number')
    code = request.data.get('code')

    if not phone_number or not code:
        return Response({"error": "Número de teléfono y código son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    try:
        verification_check = client.verify.services(os.getenv('TWILIO_VERIFY_SERVICE_SID')) \
            .verification_checks \
            .create(to=phone_number, code=code)

        if verification_check.status == "approved":
            return Response({"message": "Verificación exitosa."})
        else:
            return Response({"error": "Código inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_email_verification_code(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Correo electrónico requerido."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()

    if not user:
        # Crear un usuario temporal si no existe
        user = User.objects.create(username=email, email=email, is_active=False)
        UserProfile.objects.create(user=user, is_temporary=True)

    user_profile = user.userprofile
    otp_code = generate_otp()
    user_profile.otp_code = otp_code
    user_profile.otp_created_at = now()
    user_profile.save()

    send_email_otp(email, otp_code)
    return Response({"message": "Código enviado exitosamente."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def verify_email_otp(request):
    email = request.data.get('email')
    otp_code = request.data.get('otp_code')

    if not email or not otp_code:
        return Response({"error": "Correo y código son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({"error": "Correo electrónico no registrado."}, status=status.HTTP_400_BAD_REQUEST)

    user_profile = user.userprofile
    if user_profile.otp_code == otp_code and user_profile.is_otp_valid():
        user_profile.is_email_verified = True
        user_profile.otp_code = None
        user_profile.is_temporary = False  # Convertir en un usuario completo
        user_profile.save()

        # Activar el usuario si estaba inactivo
        if not user.is_active:
            user.is_active = True
            user.save()

        return Response({"message": "Correo verificado exitosamente."}, status=status.HTTP_200_OK)

    return Response({"error": "Código inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_user(request):
    email = request.data.get('email')

    if not email:
        return Response({"error": "El correo es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()

    if user:
        user_profile = user.userprofile
        return Response({
            "is_registered": True,
            "is_temporary": user_profile.is_temporary,  # Usuario temporal
        }, status=status.HTTP_200_OK)

    # Usuario no existe
    return Response({"is_registered": False}, status=status.HTTP_200_OK)