from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import os
import hashlib

@csrf_exempt
@api_view(['POST'])
def generate_integrity_hash(request):
    
    order_data = request.data.get('order', [])
    print("order_data: ", order_data)
    
    # Obtener los datos de la orden del request
    order_id = order_data.get('order_id')
    amount = order_data.get('amount')
    currency = order_data.get('currency')
    secret_key = os.getenv('SECRET_KEY') 

    # Generar el hash de integridad
    concatenated_string = f"{order_id}{amount}{currency}{secret_key}"
    sha256_hash = hashlib.sha256(concatenated_string.encode()).hexdigest()
    
    # Devolver el hash de integridad como JSON
    return JsonResponse({'hash': sha256_hash})
