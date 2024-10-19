from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .models import Order, OrderItem
from products.models import Product, ProductVariation
from .serializer import OrderSerializer

class OrderView(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        product_items_data = data.pop('items', [])  # Obtener los productos y sus cantidades
        order_subtotal = 0  # Inicializar subtotal de la orden

        # Crear la orden sin los datos del cliente (se agregarán luego en el checkout)
        order = Order.objects.create(
            custom_order_id=data['custom_order_id'],
            payment_status=data.get('payment_status', 'pending'),
            shipping_status=data.get('shipping_status', 'pending'),
            subtotal=0  # Inicializamos con 0, se actualizará después
        )

        # Procesar los items de la orden
        for item_data in product_items_data:
            product_variation_id = item_data.get('product_variation_id')
            quantity = item_data['quantity']

            if product_variation_id:
                # Si es un producto variable, obtenemos la variación
                product_variation = ProductVariation.objects.get(id=product_variation_id)
                unit_price = product_variation.price
                product = product_variation.product  # Obtener el producto base de la variación
            else:
                # Si no tiene variación, es un producto fijo
                product_id = item_data.get('product_id')
                product = Product.objects.get(id=product_id)
                unit_price = product.price

            # Calcular el subtotal del item
            item_subtotal = unit_price * quantity
            order_subtotal += item_subtotal  # Sumar al subtotal total de la orden

            # Crear el OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                product_variation=product_variation if product_variation_id else None,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=item_subtotal
            )

        # Actualizar el subtotal de la orden
        order.subtotal = order_subtotal
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):
        # Actualización parcial para agregar los datos del cliente
        order = self.get_object()
        data = request.data

        order.firstname = data.get('firstname', order.firstname)
        order.lastname = data.get('lastname', order.lastname)
        order.email = data.get('email', order.email)
        order.phone = data.get('phone', order.phone)

        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OrderByCustomOrderIdAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        custom_order_id = self.kwargs['custom_order_id']
        return Order.objects.filter(custom_order_id=custom_order_id)
