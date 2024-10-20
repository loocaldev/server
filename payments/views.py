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
    
    # Obtener el secreto de integridad desde variables de entorno
    secret_key = os.getenv('WOMPI_INTEGRITY_SECRET')  # Configura esto en tu entorno

    # Generar la cadena concatenada como exige Wompi
    concatenated_string = f"{order_id}{amount}{currency}{secret_key}"
    
    # Generar el hash SHA256 de la cadena concatenada
    sha256_hash = hashlib.sha256(concatenated_string.encode()).hexdigest()
    
    # Devolver el hash de integridad como JSON
    return JsonResponse({'hash': sha256_hash})
