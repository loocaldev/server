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


User = get_user_model()

class OrderView(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    lookup_field = 'custom_order_id'

    def get_object(self):
        """
        Sobrescribe el método get_object para buscar la orden por custom_order_id
        """
        custom_order_id = self.kwargs.get('custom_order_id')
        try:
            return Order.objects.get(custom_order_id=custom_order_id)
        except Order.DoesNotExist:
            raise NotFound(detail="Order not found")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        discount_code = data.get('discount_code')
        discount = None
        discount_value = 0

        # Aplicar y validar descuento si se proporciona el código
        if discount_code:
            try:
                discount = Discount.objects.select_for_update().get(code=discount_code, status='active')
                if discount.end_date < timezone.now().date():
                    return Response({"error": "El descuento ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

                if discount.max_uses_total and discount.times_used >= discount.max_uses_total:
                    return Response({"error": "Este descuento ha alcanzado su límite de usos total."}, status=status.HTTP_400_BAD_REQUEST)

                user = request.user if request.user.is_authenticated else None
                email = user.email if user else data.get('email')
                if discount.max_uses_per_user:
                    user_discount, created = UserDiscount.objects.get_or_create(
                        discount=discount,
                        email=email,
                        defaults={'user': user, 'times_used': 0}
                    )
                    if user_discount.times_used >= discount.max_uses_per_user:
                        return Response({"error": "Este descuento ha alcanzado su límite de usos para este usuario."}, status=status.HTTP_400_BAD_REQUEST)
                    user_discount.times_used += 1
                    user_discount.save(update_fields=['times_used'])

                discount.times_used += 1
                discount.save(update_fields=['times_used'])

                discount_value = data['subtotal'] * (discount.discount_value / 100) if discount.discount_type == 'percentage' else discount.discount_value

            except Discount.DoesNotExist:
                return Response({"error": "Código de descuento no válido o inactivo."}, status=status.HTTP_400_BAD_REQUEST)

        # Procesamiento de dirección
        address_data = data.get('address')
        address = None
        if address_data:
            street = address_data.get('street')
            city = address_data.get('city')
            state = address_data.get('state')
            postal_code = address_data.get('postal_code')
            country = address_data.get('country')

            if not all([street, city, state, postal_code, country]):
                return Response({"error": "Datos de dirección incompletos."}, status=status.HTTP_400_BAD_REQUEST)

            user = request.user if request.user.is_authenticated else None

            # Verificar si la dirección ya existe para el usuario
            address = Address.objects.filter(
                Q(user=user) & 
                Q(street=street) & 
                Q(city=city) & 
                Q(state=state) & 
                Q(postal_code=postal_code) & 
                Q(country=country)
            ).first()

            # Si no existe, crearla
            if not address:
                address = Address.objects.create(
                    user=user,
                    street=street,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    country=country
                )

        else:
            return Response({"error": "Falta la información de dirección."}, status=status.HTTP_400_BAD_REQUEST)

        # Validación de fecha y hora de entrega
        try:
            delivery_date = datetime.strptime(data.get('delivery_date'), "%Y-%m-%d").date()
            delivery_time = datetime.strptime(data.get('delivery_time'), "%H:%M").time()
        except (ValueError, TypeError):
            return Response({"error": "Formato de fecha u hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Crear la orden
        order = Order.objects.create(
            custom_order_id=data.get('custom_order_id', f"ORD{int(timezone.now().timestamp())}"),
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone=data['phone'],
            address=address,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            payment_status=data.get('payment_status', 'pending'),
            shipping_status=data.get('shipping_status', 'pending'),
            subtotal=0,  # Inicializamos con 0, se actualizará después
            discount=discount,
            discount_value=discount_value
        )

        # Procesar los artículos de la orden
        product_items_data = data.get('items', [])
        order_subtotal = 0
        for item_data in product_items_data:
            product_variation_id = item_data.get('product_variation_id')
            product_id = item_data.get('product_id')
            quantity = item_data['quantity']
            unit_price = None
            product_variation = None

            try:
                if product_variation_id:
                    product_variation = ProductVariation.objects.get(id=product_variation_id)
                    unit_price = product_variation.price
                    product = product_variation.product
                else:
                    product = Product.objects.get(id=product_id)
                    unit_price = product.price

                if unit_price is None:
                    return Response({"error": "El precio del producto o de la variación no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

                item_subtotal = unit_price * quantity
                order_subtotal += item_subtotal

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_variation=product_variation if product_variation_id else None,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=item_subtotal
                )
            except (Product.DoesNotExist, ProductVariation.DoesNotExist):
                return Response({"error": "Producto o variación no válido."}, status=status.HTTP_400_BAD_REQUEST)

        order.subtotal = order_subtotal
        order.calculate_total()
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        data = request.data

        # Actualizar datos del cliente y dirección
        order.firstname = data.get('firstname', order.firstname)
        order.lastname = data.get('lastname', order.lastname)
        order.email = data.get('email', order.email)
        order.phone = data.get('phone', order.phone)

        address_id = data.get('address_id')
        if address_id:
            try:
                order.address = Address.objects.get(id=address_id)
            except Address.DoesNotExist:
                return Response({"error": "La dirección no es válida."}, status=status.HTTP_400_BAD_REQUEST)

        # Validación de fecha y hora de entrega
        if data.get('delivery_date'):
            try:
                order.delivery_date = datetime.strptime(data['delivery_date'], "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Formato de fecha inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if data.get('delivery_time'):
            try:
                order.delivery_time = datetime.strptime(data['delivery_time'], "%H:%M").time()
            except ValueError:
                return Response({"error": "Formato de hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Actualización de estado de pago
        order.payment_status = data.get('payment_status', order.payment_status)
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def apply_discount(request):
    code = request.data.get("code")
    subtotal = request.data.get("subtotal")

    if not code:
        return Response({"error": "No se ha proporcionado un código de descuento"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        discount = Discount.objects.get(code=code, status='active')

        # Verificar vigencia del descuento
        if discount.end_date < timezone.now().date():
            return Response({"error": "El descuento ha expirado"}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar límite de usos totales
        if discount.max_uses_total and discount.times_used >= discount.max_uses_total:
            return Response({"error": "Este descuento ha alcanzado su límite de usos totales"}, status=status.HTTP_400_BAD_REQUEST)

        # Validar límite de uso por usuario
        email = request.user.email if request.user.is_authenticated else request.data.get('email')
        if discount.max_uses_per_user:
            user_discount, _ = UserDiscount.objects.get_or_create(discount=discount, email=email)
            if user_discount.times_used >= discount.max_uses_per_user:
                return Response({"error": "Este descuento ha alcanzado su límite de usos para este usuario"}, status=status.HTTP_400_BAD_REQUEST)

        # Calcular el valor del descuento
        discount_value = discount.discount_value
        if discount.discount_type == 'percentage':
            discount_value = Decimal(subtotal) * (Decimal(discount_value) / Decimal('100'))
        else:
            discount_value = Decimal(discount_value)

        # Asegurarse de que ambos valores estén en Decimal
        final_price = Decimal(subtotal) - discount_value

        # Retornar información del descuento
        return Response({
            "valid": True,
            "discount_value": float(discount_value),  # Convertimos a float si es necesario para el JSON
            "final_price": float(final_price),         # Convertimos a float para JSON
            "message": "Código de descuento aplicado correctamente"
        }, status=status.HTTP_200_OK)

    except Discount.DoesNotExist:
        return Response({"error": "Código de descuento no válido"}, status=status.HTTP_400_BAD_REQUEST)

class OrderByCustomOrderIdAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        custom_order_id = self.kwargs['custom_order_id']
        return Order.objects.filter(custom_order_id=custom_order_id)
