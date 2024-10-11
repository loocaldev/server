# utils.py

import requests
from django.conf import settings

def update_auth0_user(user):
    url = f'https://{settings.AUTH0_DOMAIN}/api/v2/users/{user.username}'  # Cambiar a user_id si es necesario
    headers = {
        'Authorization': f'Bearer {settings.API_TOKEN}',  # API_TOKEN debe ser generado con un permiso de management API
        'Content-Type': 'application/json'
    }
    data = {
        'email': user.email,
        'given_name': user.first_name,
        'family_name': user.last_name,
    }
    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print("User updated successfully in Auth0")
    else:
        print(f"Failed to update user in Auth0: {response.status_code}")
