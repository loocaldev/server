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
from .utils import calculate_discount,calculate_transport_cost,validate_discount_code, AVAILABLE_CITIES
from django.http import JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from django.core.mail import EmailMessage
import boto3
import os
from django.conf import settings


User = get_user_model()

def get_or_create_address(user, address_data):
        """
        Recupera una dirección existente o la crea si no existe.
        
        Args:
            user (User): El usuario autenticado (o None si no está autenticado).
            address_data (dict): Los datos de la dirección enviados en el request.
        
        Returns:
            Address: La instancia de dirección.
        
        Raises:
            ValueError: Si faltan datos obligatorios en la dirección.
        """
        if not address_data:
            raise ValueError("La dirección es obligatoria.")

        street = address_data.get("street")
        city = address_data.get("city")
        state = address_data.get("state")
        postal_code = address_data.get("postal_code")
        country = address_data.get("country")

        if not all([street, city, state, postal_code, country]):
            raise ValueError("Faltan datos obligatorios en la dirección.")

        # Verificar si la dirección ya existe
        address = Address.objects.filter(
            Q(user=user) & Q(street=street) & Q(city=city) &
            Q(state=state) & Q(postal_code=postal_code) & Q(country=country)
        ).first()

        # Si no existe, crearla
        if not address:
            address = Address.objects.create(
                user=user,
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            )

        return address


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
        firstname = None
        lastname = None
        company_name = None
        email = ""
        phone = ""
        document_type = ""
        document_number = ""

        if company_id:
            # Pedidos realizados por una empresa
            company = get_object_or_404(Company, id=company_id)
            company_name = company.name
            email = company.email
            phone = company.phone_number
        else:
            # Pedidos realizados por una persona
            firstname = customer_data.get("firstname")
            lastname = customer_data.get("lastname")
            email = customer_data.get("email")
            phone = customer_data.get("phone")
            document_type = customer_data.get("document_type")
            document_number = customer_data.get("document_number")

        # Validar que los datos obligatorios estén presentes
        if not (firstname and lastname) and not company_name:
            return Response(
                {"error": "Debe proporcionar el nombre y apellido o el nombre de la empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not email or not phone or not document_type or not document_number:
            return Response(
                {"error": "Faltan datos obligatorios: email, teléfono o documento."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        address_data = data.get("address")
        # Validar dirección
        try:
            address = get_or_create_address(
                user=request.user if request.user.is_authenticated else None,
                address_data=address_data
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        city = address.city.strip().upper()

        # Validar que la ciudad esté en la lista de ciudades disponibles
        if city not in AVAILABLE_CITIES:
            return Response(
                {"error": f"La ciudad '{address.city}' no está disponible para entregas."},
                status=status.HTTP_400_BAD_REQUEST,
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
            try:
                discount = validate_discount_code(discount_code, request, data.get("subtotal"))
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Calcular costo de transporte
        transport_cost = calculate_transport_cost(address.city)

        # Crear la orden
        order = Order.objects.create(
            custom_order_id=data.get(
                "custom_order_id", f"ORD{int(timezone.now().timestamp())}"
            ),
            firstname=firstname,
            lastname=lastname,
            company_name=company_name,
            email=email,
            phone=phone,
            document_type=document_type,
            document_number=document_number,
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
        
        # Generar documentos PDF
        order_pdf = generate_pdf(order, f"order_{order.custom_order_id}.pdf", doc_type="Orden")
        invoice_pdf = generate_pdf(order, f"invoice_{order.custom_order_id}.pdf", doc_type="Factura")

        # Subir documentos a S3
        try:
            order_url = upload_to_s3(order_pdf, os.getenv("AWS_STORAGE_BUCKET_NAME"), f"orders/order_{order.custom_order_id}.pdf")
            invoice_url = upload_to_s3(invoice_pdf, os.getenv("AWS_STORAGE_BUCKET_NAME"), f"invoices/invoice_{order.custom_order_id}.pdf")
        except Exception as e:
            return Response({"error": f"Error al subir documentos a S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Enviar correos
        try:
            send_email_with_attachments(
                order,
                [
                    (f"order_{order.custom_order_id}.pdf", order_pdf, "application/pdf"),
                    (f"invoice_{order.custom_order_id}.pdf", invoice_pdf, "application/pdf"),
                ]
            )
        except Exception as e:
            return Response({"error": f"Error al enviar correo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    subtotal = Decimal(request.data.get("subtotal", 0))

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

        # Inicializar valores de descuento
        discount_value = Decimal("0.0")
        transport_discount = Decimal("0.0")
        applies_to_transport = discount.applicable_to_transport

        # Cálculo del descuento
        if applies_to_transport:
            # Si aplica al transporte, usar un valor estimado del transporte
            transport_cost = calculate_transport_cost(request.data.get("city", ""))
            transport_discount = min(
                Decimal(discount.discount_value)
                if discount.discount_type == "absolute"
                else transport_cost * (Decimal(discount.discount_value) / 100),
                transport_cost,  # Máximo el costo del transporte
            )
        else:
            # Si aplica al subtotal, calcular descuento sobre el subtotal
            discount_value = (
                Decimal(subtotal) * (Decimal(discount.discount_value) / 100)
                if discount.discount_type == "percentage"
                else min(Decimal(discount.discount_value), subtotal)
            )

        return Response(
            {
                "valid": True,
                "discount_value": float(discount_value),
                "applies_to_transport": applies_to_transport,
                "transport_discount": float(transport_discount),
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

def transport_cost_view(request):
    """
    Endpoint para obtener el costo de transporte basado en la ciudad.
    """
    city = request.GET.get("city")  # Obtén la ciudad de los parámetros de la URL
    if not city:
        return JsonResponse({"error": "City parameter is missing."}, status=400)

    cost = calculate_transport_cost(city)  # Calcula el costo usando la lógica centralizada
    return JsonResponse({"cost": cost})

def generate_pdf(order, filename, doc_type="Orden"):
    """
    Genera un archivo PDF de la orden o factura.
    Args:
        order (Order): Objeto de la orden.
        filename (str): Nombre del archivo.
        doc_type (str): Tipo de documento ("Orden" o "Factura").
    Returns:
        bytes: Archivo PDF en memoria.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{doc_type} de Pedido - {order.custom_order_id}")

    # Información del cliente
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Cliente: {order.firstname} {order.lastname}")
    c.drawString(50, height - 120, f"Correo: {order.email}")
    c.drawString(50, height - 140, f"Teléfono: {order.phone}")

    # Detalle de productos
    c.drawString(50, height - 180, "Productos:")
    y = height - 200
    for item in order.items.all():
        c.drawString(50, y, f"{item.product.name} - {item.quantity} x ${item.unit_price}")
        y -= 20

    # Totales
    c.drawString(50, y - 20, f"Subtotal: ${order.subtotal}")
    c.drawString(50, y - 40, f"Envío: ${order.transport_cost}")
    c.drawString(50, y - 60, f"Total: ${order.total}")

    # Guardar el PDF
    c.save()
    buffer.seek(0)

    return buffer.getvalue()

def upload_to_s3(file_content, bucket_name, file_key):
    """
    Sube un archivo a Amazon S3.
    Args:
        file_content (bytes): Contenido del archivo.
        bucket_name (str): Nombre del bucket de S3.
        file_key (str): Key del archivo en S3.
    Returns:
        str: URL del archivo subido.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_S3_REGION_NAME'),
    )
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=file_content, ACL='public-read')
    return f"https://{bucket_name}.s3.amazonaws.com/{file_key}"

def send_email_with_attachments(order, attachments):
    """
    Envía un correo electrónico con documentos adjuntos.
    Args:
        order (Order): Objeto de la orden.
        attachments (list): Lista de tuplas (filename, content, mime_type).
    """
    email = EmailMessage(
        subject=f"Documentos de Pedido #{order.custom_order_id}",
        body=f"Hola {order.firstname}, adjuntamos los documentos de tu pedido.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
        cc=["camilo@loocal.co"],
    )
    for filename, content, mime_type in attachments:
        email.attach(filename, content, mime_type)
    email.send()