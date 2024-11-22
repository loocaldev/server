from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Q
from .models import Order, OrderItem, Discount, UserDiscount
from products.models import Product, ProductVariation
from django.contrib.auth import get_user_model
from loocal.models import Address
from .serializer import OrderSerializer
from datetime import datetime
from decimal import Decimal
from loocal.analytics import track_event
from django.shortcuts import get_object_or_404
from companies.models import Company
from .utils import calculate_discount,calculate_transport_cost,validate_discount_code
from django.http import JsonResponse

User = get_user_model()


class OrderView(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    lookup_field = "custom_order_id"

    def get_object(self):
        """
        Sobrescribe el método get_object para buscar la orden por custom_order_id
        """
        custom_order_id = self.kwargs.get("custom_order_id")
        try:
            return Order.objects.get(custom_order_id=custom_order_id)
        except Order.DoesNotExist:
            raise NotFound(detail="Order not found")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        customer_data = data.get("customer", {})
        discount_code = data.get("discount_code")
        discount = None
        discount_value = 0

        # Procesar empresa si se proporciona
        company_id = data.get("company_id")
        company = None
        firstname = ""
        lastname = ""
        email = ""
        phone = ""

        if company_id:
            # Pedidos realizados por una empresa
            company = get_object_or_404(Company, id=company_id)
            firstname = company.name  # El nombre de la empresa
            email = company.email
            phone = company.phone_number
        else:
            # Pedidos realizados por un cliente
            firstname = customer_data.get("firstname")
            lastname = customer_data.get("lastname")
            email = customer_data.get("email")
            phone = customer_data.get("phone")

        # Validar que los datos requeridos estén presentes
        if not firstname or not email or not phone:
            return Response(
                {"error": "Faltan datos obligatorios: nombre, email o teléfono."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar dirección
        address_data = data.get("address")
        if not address_data:
            return Response(
                {"error": "La dirección es obligatoria."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        street = address_data.get("street")
        city = address_data.get("city")
        state = address_data.get("state")
        postal_code = address_data.get("postal_code")
        country = address_data.get("country")

        if not all([street, city, state, postal_code, country]):
            return Response(
                {"error": "Faltan datos de la dirección."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Recuperar o crear dirección
        user = request.user if request.user.is_authenticated else None
        address = Address.objects.filter(
            Q(user=user)
            & Q(street=street)
            & Q(city=city)
            & Q(state=state)
            & Q(postal_code=postal_code)
            & Q(country=country)
        ).first()

        if not address:
            address = Address.objects.create(
                user=user,
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            )

        # Validar fecha y hora de entrega
        try:
            delivery_date = datetime.strptime(data.get("delivery_date"), "%Y-%m-%d").date()
            delivery_time = datetime.strptime(data.get("delivery_time"), "%H:%M").time()
        except (ValueError, TypeError):
            return Response(
                {"error": "Formato inválido para fecha u hora de entrega."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Procesar descuento si se incluye
        if discount_code:
            discount = validate_discount_code(discount_code, request, data.get("subtotal"))

        # Calcular costo de transporte
        transport_cost = calculate_transport_cost(city)

        # Crear la orden
        order = Order.objects.create(
            custom_order_id=data.get(
                "custom_order_id", f"ORD{int(timezone.now().timestamp())}"
            ),
            firstname=firstname,
            lastname=lastname,  # Puede ser vacío para empresas
            email=email,
            phone=phone,
            company=company,
            address=address,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            transport_cost=transport_cost,
            subtotal=0,  # Se calcula luego
            discount=discount,
            discount_value=discount_value,
            payment_status=data.get("payment_status", "pending"),
            shipping_status=data.get("shipping_status", "pending"),
        )

        # Procesar los productos
        items_data = data.get("items", [])
        if not items_data:
            return Response(
                {"error": "Debe incluir al menos un producto en la orden."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subtotal = 0
        for item in items_data:
            product = get_object_or_404(Product, id=item["product_id"])
            quantity = item.get("quantity", 1)
            unit_price = product.price
            subtotal += unit_price * quantity

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=unit_price * quantity,
            )

        # Actualizar subtotal y total
        order.subtotal = subtotal
        order.calculate_total()
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        data = request.data

        # Actualizar datos del cliente y dirección
        order.firstname = data.get("firstname", order.firstname)
        order.lastname = data.get("lastname", order.lastname)
        order.email = data.get("email", order.email)
        order.phone = data.get("phone", order.phone)

        address_id = data.get("address_id")
        if address_id:
            try:
                order.address = Address.objects.get(id=address_id)
            except Address.DoesNotExist:
                return Response(
                    {"error": "La dirección no es válida."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Validación de fecha y hora de entrega
        if data.get("delivery_date"):
            try:
                order.delivery_date = datetime.strptime(
                    data["delivery_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if data.get("delivery_time"):
            try:
                order.delivery_time = datetime.strptime(
                    data["delivery_time"], "%H:%M"
                ).time()
            except ValueError:
                return Response(
                    {"error": "Formato de hora inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Actualización de estado de pago
        order.payment_status = data.get("payment_status", order.payment_status)
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def apply_discount(request):
    code = request.data.get("code")
    subtotal = request.data.get("subtotal")

    if not code:
        return Response(
            {"error": "No se ha proporcionado un código de descuento"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        discount = Discount.objects.get(code=code, status="active")

        # Verificar vigencia del descuento
        if discount.end_date < timezone.now().date():
            return Response(
                {"error": "El descuento ha expirado"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar límite de usos totales
        if discount.max_uses_total and discount.times_used >= discount.max_uses_total:
            return Response(
                {"error": "Este descuento ha alcanzado su límite de usos totales"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar límite de uso por usuario
        email = (
            request.user.email
            if request.user.is_authenticated
            else request.data.get("email")
        )
        if discount.max_uses_per_user:
            user_discount, _ = UserDiscount.objects.get_or_create(
                discount=discount, email=email
            )
            if user_discount.times_used >= discount.max_uses_per_user:
                return Response(
                    {
                        "error": "Este descuento ha alcanzado su límite de usos para este usuario"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Calcular el valor del descuento
        discount_value = calculate_discount(subtotal, discount)
        applies_to_transport = discount.applicable_to_transport

        return Response(
            {
                "valid": True,
                "discount_value": float(discount_value),
                "applies_to_transport": applies_to_transport,
                "message": "Código de descuento aplicado correctamente",
            },
            status=status.HTTP_200_OK,
        )

    except Discount.DoesNotExist:
        return Response(
            {"error": "Código de descuento no válido"},
            status=status.HTTP_400_BAD_REQUEST,
        )



class OrderByCustomOrderIdAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        custom_order_id = self.kwargs["custom_order_id"]
        return Order.objects.filter(custom_order_id=custom_order_id)


# Simulación de costos de transporte por ciudad
TRANSPORT_COSTS = {
    "BOGOTÁ D.C.": 10000,
    "CHÍA": 2000,
    "CAJICÁ": 6000,
    "SOPÓ": 8000,
}

DEFAULT_COST = 5000 

def transport_cost_view(request):
    city = request.GET.get("city")
    if not city:
        return JsonResponse({"error": "City parameter is missing."}, status=400)
    
    cost = TRANSPORT_COSTS.get(city, DEFAULT_COST)
    return JsonResponse({"cost": cost})