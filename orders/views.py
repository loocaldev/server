# Views.py

from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .models import Order
from products.models import ProductVariation
from .serializer import OrderSerializer
from products.serializer import ProductVariationSerializer

class OrderView(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Override the default create method to handle product variations in the order.
        """
        data = request.data
        
        # Verificar si se están enviando variaciones de productos
        product_variations_data = data.pop('product_variations', [])
        product_variations = []

        # Validar y obtener las variaciones de productos seleccionadas
        for variation_data in product_variations_data:
            try:
                variation = ProductVariation.objects.get(id=variation_data['id'])
                product_variations.append(variation)
            except ProductVariation.DoesNotExist:
                return Response(
                    {"error": f"Product variation with ID {variation_data['id']} not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Crear la orden
        order = Order.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone=data['phone'],
            custom_order_id=data['custom_order_id'],
            subtotal=data['subtotal'],
            payment_status=data.get('payment_status', 'pending')
        )

        # Agregar las variaciones de productos a la orden
        order.product_variations.set(product_variations)
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# View para obtener ordenes por custom_order_id (opcional)
class OrderByCustomOrderIdAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        custom_order_id = self.kwargs['custom_order_id']
        return Order.objects.filter(custom_order_id=custom_order_id)
