# loocal/auth_backend.py

import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import requests
from django.contrib.auth.models import User

class Auth0JWTAuthentication(BaseAuthentication):
    """
    Autenticación personalizada para manejar los JWT de Auth0.
    """

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '').split()
        
        if not auth or auth[0].lower() != 'bearer':
            return None

        if len(auth) == 1:
            raise AuthenticationFailed('Token no proporcionado')
        elif len(auth) > 2:
            raise AuthenticationFailed('Encabezado de autorización inválido')

        token = auth[1]
        
        try:
            payload = self.decode_auth0_token(token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('El token ha expirado')
        except jwt.JWTClaimsError:
            raise AuthenticationFailed('Token inválido')
        except Exception as e:
            raise AuthenticationFailed(f'Error desconocido al decodificar el token: {str(e)}')
        
        # Aquí asocia el payload con un usuario en tu base de datos
        user, _ = User.objects.get_or_create(
            username=payload['sub'],
            defaults={'email': payload.get('email', ''), 'is_active': True}
        )
        
        return (user, token)

    def decode_auth0_token(self, token):
        rsa_key = self.get_rsa_key(token)
        if not rsa_key:
            raise AuthenticationFailed('No se pudo obtener la clave pública para Auth0')

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=settings.ALGORITHMS,
            audience=settings.API_IDENTIFIER,
            issuer=f"https://{settings.AUTH0_DOMAIN}/"
        )
        return payload

    def get_rsa_key(self, token):
        jwks = self.get_jwks()
        if not jwks:
            raise AuthenticationFailed('No se pudieron obtener las claves JWKS')

        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
                break
        return rsa_key

    def get_jwks(self):
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        try:
            jwks = requests.get(jwks_url).json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener las claves JWKS desde {jwks_url}: {str(e)}")
            return None
        return jwks
