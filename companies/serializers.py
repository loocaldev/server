from rest_framework import serializers
from .models import Company, CompanyMembership

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'nit', 'email', 'phone', 'created_by', 'created_at', 'updated_at']

class CompanyMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMembership
        fields = ['id', 'user', 'company', 'role', 'invited_by', 'joined_at', 'invitation_accepted']
