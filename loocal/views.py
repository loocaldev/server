from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserSerializer
from .models import UserProfile
from rest_framework.permissions import IsAuthenticated
from loocal.auth_backend import Auth0JWTAuthentication  # Asegúrate de importar tu clase de autenticación personalizada

# Sincronizar el usuario de Auth0 con el modelo de Django
@api_view(['GET'])
@authentication_classes([Auth0JWTAuthentication])  # Usamos la autenticación personalizada
@permission_classes([IsAuthenticated])
def profile(request):
    # Obtener el usuario autenticado desde el token JWT
    user = request.user

    # Si no se encuentra el usuario, devolver un error
    if not user:
        return Response({'error': 'Usuario no autenticado'}, status=401)

    # Crear o actualizar el perfil del usuario
    profile_data = {'profile_picture': request.data.get('picture', None)}
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults=profile_data)

    if request.data.get('picture'):
        profile.profile_picture = request.data.get('picture')
        profile.save()

    # Retornar los datos del usuario
    user_serializer = UserSerializer(instance=user)
    return Response(user_serializer.data)
