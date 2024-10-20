from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import os
import hashlib

@csrf_exempt
@api_view(['POST'])
def generate_integrity_hash(request):
    # Obtener los datos de la orden desde el request
    order_data = request.data.get('order', {})
    order_id = order_data.get('order_id')
    amount = order_data.get('amount')
    currency = order_data.get('currency', 'COP')
    
    # Llave de integridad (puede venir de tus variables de entorno)
    secret_key = "test_integrity_r7mbaEF8A7XF8ex9T5O0Ul0tAhCdhUDM"  # O usar os.getenv('WOMPI_INTEGRITY_SECRET')
    
    # Concatenar los valores en el orden correcto
    concatenated_string = f"{order_id}{amount}{currency}{secret_key}"
    
    # Generar el hash SHA-256
    sha256_hash = hashlib.sha256(concatenated_string.encode()).hexdigest()
    
    # Devolver el hash de integridad como JSON
    return JsonResponse({'hash': sha256_hash})
