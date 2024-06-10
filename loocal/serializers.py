# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state', 'postal_code', 'country', 'is_default']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    addresses = AddressSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile', 'addresses']
