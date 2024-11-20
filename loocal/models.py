# models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils.timezone import now
import uuid
from django.utils.text import slugify

def get_profile_picture_upload_path(instance, filename):
    unique_id = uuid.uuid4().hex[:8]
    file_extension = filename.split('.')[-1]
    filename = f"{slugify(instance.user.username)}-{unique_id}.{file_extension}"
    return f"profile_pictures/{filename}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=get_profile_picture_upload_path, blank=True, null=True)
    document_type = models.CharField(max_length=10, blank=True, null=True)  # Asegúrate de que esté aquí
    document_number = models.CharField(max_length=20, blank=True, null=True)  # Asegúrate de que esté aquí
    birthdate = models.DateField(blank=True, null=True) 
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Asegúrate de que esté aquí
    phone_code = models.CharField(max_length=5, blank=True, null=True)  # Indicativo
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_created_at = models.DateTimeField(blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_temporary = models.BooleanField(default=False)  # Usuario temporal
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
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state}, {self.country}'