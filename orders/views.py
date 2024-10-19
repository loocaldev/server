# orders/views.py
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

        # Crear la orden
        order = Order.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone=data['phone'],
            custom_order_id=data['custom_order_id'],
            payment_status=data.get('payment_status', 'pending'),
            shipping_status=data.get('shipping_status', 'pending')
        )

        # Procesar los items de la orden (fijos y variables)
        for item_data in product_items_data:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            product_variation_id = item_data.get('product_variation_id', None)

            # Obtener el producto
            product = Product.objects.get(id=product_id)

            # Obtener la variación (si existe)
            product_variation = None
            if product_variation_id:
                product_variation = ProductVariation.objects.get(id=product_variation_id)
                unit_price = product_variation.price
            else:
                unit_price = product.price

            # Calcular el subtotal de este producto (precio * cantidad)
            item_subtotal = unit_price * quantity
            order_subtotal += item_subtotal

            # Crear el OrderItem (variación opcional)
            OrderItem.objects.create(
                order=order,
                product=product,
                product_variation=product_variation,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=item_subtotal,
                tax=0  # Asume que no hay impuestos; si los hay, puedes calcular aquí.
            )

        # Actualizar el subtotal de la orden
        order.subtotal = order_subtotal
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderByCustomOrderIdAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        custom_order_id = self.kwargs['custom_order_id']
        return Order.objects.filter(custom_order_id=custom_order_id)
