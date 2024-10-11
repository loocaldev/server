from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserSerializer
from .models import UserProfile
import jwt
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import requests

# Obtener el conjunto de claves de Auth0 (JWKS)
def get_jwks():
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    return jwks

# Extraer la clave RSA adecuada para verificar el token JWT
def get_rsa_key(token):
    jwks = get_jwks()  # Obtener claves
    unverified_header = jwt.get_unverified_header(token)  # Decodificar el encabezado sin verificar el token

    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:  # Coincidir por 'kid'
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    return rsa_key

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

# Sincronizar el usuario de Auth0 con el modelo de Django
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

    # Crear o actualizar el usuario en Django basado en la información de Auth0
    user, created = User.objects.get_or_create(
        username=payload['sub'],  # Auth0 "sub" es el identificador único
        defaults={'email': payload.get('email', '')}
    )

    user.email = payload.get('email', user.email)
    user.save()

    # Crear o actualizar el perfil del usuario
    profile_data = {'profile_picture': payload.get('picture', None)}
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults=profile_data)

    if payload.get('picture'):
        profile.profile_picture = payload.get('picture')
        profile.save()

    # Retornar los datos del usuario
    user_serializer = UserSerializer(instance=user)
    return Response(user_serializer.data)
