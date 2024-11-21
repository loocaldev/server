from decimal import Decimal

TRANSPORT_COST_BY_CITY = {
    "BOGOTA": 8000,
    "CHIA": 5000,
    "CAJICA": 8000,
    "SOPO": 8000,
    "default": 20000,  # Valor predeterminado para casos no mapeados
}

def calculate_transport_cost(city):
    return TRANSPORT_COST_BY_CITY.get(city, TRANSPORT_COST_BY_CITY["Ciudad desconocida"])

def calculate_discount(subtotal, discount):
    """
    Calcula el valor del descuento basado en el subtotal y el tipo de descuento.
    """
    if discount.discount_type == 'percentage':
        return Decimal(subtotal) * (discount.discount_value / Decimal('100'))
    elif discount.discount_type == 'absolute':
        return min(Decimal(discount.discount_value), Decimal(subtotal))  # Evitar descuento mayor al subtotal
    return Decimal('0.0')