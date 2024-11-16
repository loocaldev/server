# models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils.timezone import now

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    document_type = models.CharField(max_length=10, blank=True, null=True)  # Asegúrate de que esté aquí
    document_number = models.CharField(max_length=20, blank=True, null=True)  # Asegúrate de que esté aquí
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Asegúrate de que esté aquí
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_created_at = models.DateTimeField(blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    def is_otp_valid(self):
        if self.otp_created_at:
            return now() < self.otp_created_at + timedelta(minutes=10)
        return False

    def __str__(self):
        return self.user.username

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', null=True, blank=True)  # Hacemos la relación opcional
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state}, {self.country}'