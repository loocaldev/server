import json
import requests
from jose import jwt, JWTError
from django.conf import settings

AUTH0_DOMAIN = settings.AUTH0_DOMAIN
API_IDENTIFIER = settings.API_IDENTIFIER
JWKS_URL = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'

def get_jwks():
    response = requests.get(JWKS_URL)
    return response.json()

def verify_jwt(token):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=API_IDENTIFIER,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
    except JWTError:
        raise Exception("Token inválido")
    return payload
