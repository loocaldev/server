# views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
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

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

# Verificar el JWT proporcionado por Auth0
def decode_auth0_token(token):
    rsa_key = get_rsa_key(token)
    if rsa_key:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=['RS256'],
            audience=settings.API_IDENTIFIER,
            issuer=f"https://{settings.AUTH0_DOMAIN}/"
        )
        return payload
    raise ValueError('No se pudo obtener la clave RSA de Auth0')

# Obtener o crear el usuario basado en la autenticación de Auth0
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    token = request.headers.get('Authorization', '').split()[1]
    
    try:
        payload = decode_auth0_token(token)
    except jwt.ExpiredSignatureError:
        return Response({'error': 'Token ha expirado'}, status=400)
    except jwt.JWTClaimsError:
        return Response({'error': 'Token inválido'}, status=400)

    # Sincronizar el usuario en Django usando la información de Auth0
    user, created = User.objects.get_or_create(
        username=payload['sub'],  # Auth0 sub
        defaults={'email': payload.get('email', '')}
    )

    # Actualizar la información del usuario si es necesario
    user.email = payload.get('email', user.email)
    user.save()

    # Crear o actualizar el perfil del usuario
    profile_data = {'profile_picture': payload.get('picture', None)}
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults=profile_data)
    
    if payload.get('picture'):
        profile.profile_picture = payload.get('picture')
        profile.save()

    # Retornar los datos del usuario en Django
    user_serializer = UserSerializer(instance=user)
    return Response(user_serializer.data)

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
def update_user(request):
    user = request.user  # Obtener el objeto User asociado al usuario actual

    # Recopilar los datos que deseas actualizar desde la solicitud
    new_email = request.data.get('email')
    new_password = request.data.get('password')
    new_first_name = request.data.get('first_name')
    new_last_name = request.data.get('last_name')

    # Actualizar los campos necesarios del objeto User
    if new_email:
        user.email = new_email
        user.username = new_email
    if new_password:
        user.set_password(new_password)
    if new_first_name:
        user.first_name = new_first_name
    if new_last_name:
        user.last_name = new_last_name

    # Guardar los cambios en la base de datos
    user.save()

    return Response("User updated successfully", status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
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
