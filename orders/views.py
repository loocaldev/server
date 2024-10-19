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
            product_variation_id = item_data.get('product_variation_id')
            quantity = item_data['quantity']

        # Verificar si es un producto fijo (sin variaciones)
        if not product_variation_id:
            # Manejar productos fijos (puedes asumir que esto es el ID del producto fijo)
            product_id = item_data.get('product_id')  # o product_variation_id en el caso de productos fijos
            # Aquí, busca el producto fijo y usa el ID
            # Ejemplo (puede variar según el modelo de productos que tengas)
            product = Product.objects.get(id=product_id)
            item_subtotal = product.price * quantity
        else:
            # Manejar productos variables
            product_variation = ProductVariation.objects.get(id=product_variation_id)
            item_subtotal = product_variation.price * quantity

        # Suma el subtotal del item a la orden
        order_subtotal += item_subtotal

        # Crear el OrderItem para ambos tipos de productos
        OrderItem.objects.create(
            order=order,
            product_variation=product if not product_variation_id else product_variation,
            quantity=quantity,
            subtotal=item_subtotal
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
