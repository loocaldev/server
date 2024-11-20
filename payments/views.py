from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import os
import hashlib
from .models import Payment
import json

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
    return JsonResponse({'hash': sha256_hash, 'concatened':concatenated_string})

@csrf_exempt
def wompi_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            event = data.get("event", "")
            transaction = data.get("data", {}).get("transaction", {})

            if event == "transaction.updated":
                reference = transaction.get("reference")  # Referencia de la orden o pago
                status = transaction.get("status")       # Estado de la transacción

                # Buscar el registro del pago asociado a la referencia
                try:
                    payment = Payment.objects.get(token=reference)
                    if status == "APPROVED":
                        payment.status = "approved"
                    elif status == "DECLINED":
                        payment.status = "rejected"
                    elif status in ["ERROR", "FAILED"]:
                        payment.status = "failed"
                    else:
                        payment.status = "pending"
                    payment.save()

                    return JsonResponse({"message": "Payment status updated successfully"}, status=200)
                except Payment.DoesNotExist:
                    return JsonResponse({"error": "Payment not found"}, status=404)

            return JsonResponse({"message": "Event not handled"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)
