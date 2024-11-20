from django.db import models
from django.contrib.auth.models import User
import uuid

class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True)  # Número de Identificación Tributaria
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_companies")
    members = models.ManyToManyField(
        User, 
        through="CompanyMembership", 
        related_name="companies",
        through_fields=('company', 'user')  # Especificamos los campos en la tabla intermedia
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CompanyMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ], default='member')
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="invitations")
    joined_at = models.DateTimeField(auto_now_add=True)
    invitation_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'company')
