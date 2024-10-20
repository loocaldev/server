from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import os
import hashlib
import requests
from django.conf import settings
from rest_framework.response import Response
from .models import Payment

@api_view(['POST'])
def create_payment_token(request):
    """
    Tokeniza una tarjeta de crédito en Wompi y crea una transacción.
    """
    data = request.data
    card_info = {
        "number": data["number"],
        "exp_month": data["exp_month"],
        "exp_year": data["exp_year"],
        "cvc": data["cvc"],
        "card_holder": data["card_holder"]
    }

    # Enviar la solicitud a Wompi
    url = "https://production.wompi.co/v1/tokens/cards"
    headers = {
        "Authorization": f"Bearer {settings.WOMPI_PRIVATE_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json={"data": card_info}, headers=headers)
    response_data = response.json()

    if response.status_code == 201:
        token = response_data["data"]["id"]  # Token de la tarjeta
        return Response({"token": token})
    else:
        return Response(response_data, status=response.status_code)
    
@api_view(['POST'])
def create_wompi_transaction(request):
    """
    Crea una transacción en Wompi usando el token generado.
    """
    data = request.data
    url = "https://production.wompi.co/v1/transactions"

    headers = {
        "Authorization": f"Bearer {settings.WOMPI_PRIVATE_KEY}",
        "Content-Type": "application/json"
    }

    transaction_data = {
        "amount_in_cents": int(float(data["amount"]) * 100),  # Convertimos a centavos
        "currency": "COP",
        "customer_email": data["email"],
        "payment_method": {
            "type": "CARD",
            "token": data["token"]
        },
        "reference": data["reference"],  # Puedes usar order_id como referencia
        "acceptance_token": data["acceptance_token"],
    }

    response = requests.post(url, json=transaction_data, headers=headers)
    response_data = response.json()

    if response.status_code == 201:
        # Guardar el pago en la base de datos
        payment = Payment.objects.create(
            transaction_amount=data["amount"],
            token=data["token"],
            description=data["description"],
            payment_method_id="CARD",
            payer_email=data["email"],
            transaction_id=response_data["data"]["id"],  # Guardar el ID de la transacción de Wompi
            status=response_data["data"]["status"]
        )
        return Response({"payment": PaymentSerializer(payment).data})
    else:
        return Response(response_data, status=response.status_code)


# @csrf_exempt
# @api_view(['POST'])
# def generate_integrity_hash(request):
    
#     order_data = request.data.get('order', [])
#     print("order_data: ", order_data)
    
#     # Obtener los datos de la orden del request
#     order_id = order_data.get('order_id')
#     amount = order_data.get('amount')
#     currency = order_data.get('currency')
#     secret_key = os.getenv('SECRET_KEY') 

#     # Generar el hash de integridad
#     concatenated_string = f"{order_id}{amount}{currency}{secret_key}"
#     sha256_hash = hashlib.sha256(concatenated_string.encode()).hexdigest()
    
#     # Devolver el hash de integridad como JSON
#     return JsonResponse({'hash': sha256_hash})
