# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state', 'postal_code', 'country', 'is_default']

class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['profile_picture']

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url  # Devolver la URL completa de la imagen
        return None

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    addresses = AddressSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile', 'addresses']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        addresses_data = validated_data.pop('addresses', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        profile = instance.profile
        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        for address_data in addresses_data:
            address_id = address_data.pop('id', None)
            if address_id:
                address = Address.objects.get(id=address_id, user=instance)
                for attr, value in address_data.items():
                    setattr(address, attr, value)
                address.save()
            else:
                Address.objects.create(user=instance, **address_data)

        return instance
