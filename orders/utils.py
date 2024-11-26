from decimal import Decimal
from .models import Discount, UserDiscount
from django.utils import timezone

AVAILABLE_CITIES = ["BOGOTÁ ZONA NORTE", "CHÍA", "CAJICÁ", "SOPÓ"]

TRANSPORT_COST_BY_CITY = {
    "BOGOTÁ ZONA NORTE": 10000,
    "CHÍA": 2000,
    "CAJICÁ": 6000,
    "SOPÓ": 8000,
}

DEFAULT_TRANSPORT_COST = 18000

def calculate_transport_cost(city):
    if not isinstance(city, str):
        # Si city no es una cadena, devuelve el costo de transporte por defecto
        return DEFAULT_TRANSPORT_COST
    normalized_city = city.strip().upper()
    return TRANSPORT_COST_BY_CITY.get(normalized_city, DEFAULT_TRANSPORT_COST)

def calculate_discount(subtotal, discount):
    """
    Calcula el valor del descuento basado en el subtotal y el tipo de descuento.
    """
    if discount.discount_type == 'percentage':
        return Decimal(subtotal) * (discount.discount_value / Decimal('100'))
    elif discount.discount_type == 'absolute':
        return min(Decimal(discount.discount_value), Decimal(subtotal))  # Evitar descuento mayor al subtotal
    return Decimal('0.0')

def validate_discount_code(discount_code, request, subtotal):
        try:
            discount = Discount.objects.get(code=discount_code, status="active")
            if discount.end_date < timezone.now().date():
                raise ValueError("El descuento ha expirado.")
            if discount.max_uses_total and discount.times_used >= discount.max_uses_total:
                raise ValueError("El descuento alcanzó su límite de usos.")
            if discount.max_uses_per_user:
                user = request.user
                user_discount, _ = UserDiscount.objects.get_or_create(
                    discount=discount,
                    email=user.email if user.is_authenticated else request.data.get("email"),
                )
                if user_discount.times_used >= discount.max_uses_per_user:
                    raise ValueError("El descuento alcanzó su límite de usos para este usuario.")
            return discount
        except Discount.DoesNotExist:
            raise ValueError("El código de descuento no es válido.")