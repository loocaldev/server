from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .models import Order, OrderItem
from rest_framework.exceptions import NotFound
from products.models import Product, ProductVariation
from .serializer import OrderSerializer
from loocal.models import Address  # Importamos el modelo Address
from datetime import datetime


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

    def create(self, request, *args, **kwargs):
        data = request.data
        product_items_data = data.pop('items', [])
        address_id = data.get('address_id', None)  # Address puede ser opcional
        delivery_date = data.get('delivery_date')
        delivery_time = data.get('delivery_time')

        # Si no hay `address_id`, obtenemos los datos de la dirección desde el cuerpo de la solicitud
        if not address_id:
            street = data.get('street')
            city = data.get('city')
            state = data.get('state')
            postal_code = data.get('postal_code')
            country = data.get('country')

            # Validamos la existencia de los campos requeridos para una dirección completa
            if not (street and city and state and postal_code and country):
                return Response({"error": "Datos de dirección incompletos."}, status=status.HTTP_400_BAD_REQUEST)

            # Creamos una dirección temporal para el pedido (sin usuario)
            address = Address.objects.create(
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            )
        else:
            # Si se proporciona `address_id`, usamos una dirección existente
            try:
                address = Address.objects.get(id=address_id)
            except Address.DoesNotExist:
                return Response({"error": "La dirección no es válida."}, status=status.HTTP_400_BAD_REQUEST)

        # Validación de fecha y hora de entrega
        try:
            delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d").date()
            delivery_time = datetime.strptime(delivery_time, "%H:%M").time()
        except (ValueError, TypeError):
            return Response({"error": "Formato de fecha u hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Crear la orden
        order = Order.objects.create(
            custom_order_id=data['custom_order_id'],
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone=data['phone'],
            address=address,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            payment_status=data.get('payment_status', 'pending'),
            shipping_status=data.get('shipping_status', 'pending'),
            subtotal=0  # Inicializamos con 0, se actualizará después
        )

        # Procesar los artículos de la orden
        order_subtotal = 0
        for item_data in product_items_data:
            product_variation_id = item_data.get('product_variation_id')
            product_id = item_data.get('product_id')
            quantity = item_data['quantity']
            unit_price = None

            try:
                # Manejo para productos con variaciones
                if product_variation_id:
                    product_variation = ProductVariation.objects.get(id=product_variation_id)
                    unit_price = product_variation.price
                    product = product_variation.product

                    if unit_price is None:
                        return Response({"error": "El precio de la variación del producto no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

                # Manejo para productos simples
                else:
                    product = Product.objects.get(id=product_id)
                    unit_price = product.price

                    if unit_price is None:
                        return Response({"error": "El precio del producto no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

                # Calcular subtotal de cada item
                item_subtotal = unit_price * quantity
                order_subtotal += item_subtotal

                # Crear el OrderItem
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

        # Actualizar el subtotal de la orden
        order.subtotal = order_subtotal
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
        delivery_date = data.get('delivery_date')
        delivery_time = data.get('delivery_time')

        # Actualización de la dirección si se proporciona un address_id
        if address_id:
            try:
                order.address = Address.objects.get(id=address_id)
            except Address.DoesNotExist:
                return Response({"error": "La dirección no es válida."}, status=status.HTTP_400_BAD_REQUEST)

        # Validación de fecha y hora de entrega
        if delivery_date:
            try:
                order.delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Formato de fecha inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if delivery_time:
            try:
                order.delivery_time = datetime.strptime(delivery_time, "%H:%M").time()
            except ValueError:
                return Response({"error": "Formato de hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Actualización de estado de pago
        order.payment_status = data.get('payment_status', order.payment_status)
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderByCustomOrderIdAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        custom_order_id = self.kwargs['custom_order_id']
        return Order.objects.filter(custom_order_id=custom_order_id)
