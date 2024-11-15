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
from . import signals
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.hashers import check_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.urls import reverse
from datetime import timedelta
from django.utils.timezone import now

@api_view(['POST'])
def login(request):
    user = authenticate(username=request.data['username'], password=request.data['password'])
    
    if not user.check_password(request.data['password']):
        return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
    
    django_login(request, user)
    
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(instance=user)
    
    print("Login: Session cookie age:", request.session.get_expiry_age())
    print("Login: Token expiration:", token.created + datetime.timedelta(hours=1))
    
    return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def register(request):
    user_serializer = UserSerializer(data=request.data)
    
    if user_serializer.is_valid():
        user = user_serializer.save()
        user.email = request.data['username']
        user.set_password(request.data['password'])
        user.save()

        profile_data = request.data.get('profile', {})
        UserProfile.objects.create(user=user, **profile_data)
        
        addresses_data = request.data.get('addresses', [])
        for address_data in addresses_data:
            Address.objects.create(user=user, **address_data)
        
        token = Token.objects.create(user=user)
        return Response({'token': token.key, "user": user_serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user

    # Asegurarse de que el perfil existe
    if not hasattr(user, 'userprofile'):
        UserProfile.objects.create(user=user)  # Crear un perfil si no existe

    serializer = UserSerializer(instance=user)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_address(request):
    user = request.user
    address_serializer = AddressSerializer(data=request.data)
    
    if address_serializer.is_valid():
        address_serializer.save(user=user)
        return Response(address_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_addresses(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    serializer = AddressSerializer(instance=addresses, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    token = Token.objects.get(user=request.user)
    token.delete()
    return Response("Logout successful", status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
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

    # Generar token único
    token = get_random_string(32)
    user_profile = user.userprofile
    user_profile.reset_token = token
    user_profile.reset_token_created_at = now()  # Actualizar la fecha de creación del token
    user_profile.save()

    # Crear URL para restablecer contraseña en el frontend
    reset_url = f"https://loocal.co/reset-password?token={token}"

    # Enviar correo
    send_mail(
        'Recuperación de contraseña',
        f'Usa el siguiente enlace para restablecer tu contraseña: {reset_url}',
        'camilo@loocal.co',
        [email],
        fail_silently=False,
    )
    return Response({"message": "Se ha enviado un correo con las instrucciones para restablecer tu contraseña."})

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