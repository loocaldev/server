from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import os
import hashlib
from .models import Payment
import json
from orders.models import Order
import logging

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

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(["POST"])
def wompi_webhook(request):
    if request.method == "POST":
        try:
            # Parsear los datos del webhook
            data = json.loads(request.body)
            event = data.get("event", "")
            transaction = data.get("data", {}).get("transaction", {})

            if event == "transaction.updated":
                reference = transaction.get("reference")  # Referencia de la orden/pago
                status = transaction.get("status")       # Estado de la transacción

                # Buscar el Payment asociado
                try:
                    payment = Payment.objects.get(token=reference)

                    # Actualizar estado del Payment
                    status_map = {
                        "APPROVED": "approved",
                        "DECLINED": "rejected",
                        "ERROR": "failed",
                        "FAILED": "failed",
                        "PENDING": "pending",
                    }
                    payment.status = status_map.get(status, "unknown")
                    payment.save()

                    # Buscar la Order asociada y actualizar su payment_status
                    try:
                        order = Order.objects.get(custom_order_id=reference)

                        # Mapear estados de Payment a Order.payment_status
                        order_status_map = {
                            "approved": "paid",
                            "rejected": "failed",
                            "failed": "failed",
                            "pending": "pending",
                        }
                        order.payment_status = order_status_map.get(payment.status, "unknown")
                        order.save()

                        logger.info(
                            f"Order {order.custom_order_id} updated to payment_status: {order.payment_status}"
                        )

                        return JsonResponse(
                            {"message": f"Order and Payment updated successfully: {order.payment_status}"},
                            status=200,
                        )
                    except Order.DoesNotExist:
                        logger.warning(f"Order not found for reference: {reference}")
                        return JsonResponse({"error": "Order not found"}, status=404)

                except Payment.DoesNotExist:
                    logger.warning(f"Payment not found for reference: {reference}")
                    return JsonResponse({"error": "Payment not found"}, status=404)

            return JsonResponse({"message": "Event not handled"}, status=200)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"error": f"Error: {str(e)}"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)