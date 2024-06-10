# views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from .serializers import UserSerializer, UserProfileSerializer, AddressSerializer
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import UserProfile, Address
import datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    
    if not user.check_password(request.data['password']):
        return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
    
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
