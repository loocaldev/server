from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Q
from .models import Order, OrderItem, Discount, UserDiscount, OrderStatusChangeLog
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
from datetime import timedelta
from reportlab.platypus import Table
from django.utils.timezone import now
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from payments.models import Payment
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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
            payment_status=data.get("payment_status", "pending"),
            shipping_status=data.get("shipping_status", "pending_preparation"),
            payment_method=data.get("payment_method", "online"),
            discount=discount,
            discount_value=discount_value,
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
        
        Payment.objects.create(
            transaction_amount=order.total,
            token=order.custom_order_id,  # Usa el custom_order_id como referencia
            description=f"Pago para la orden {order.custom_order_id}",
            installments=1,  # Ajustar según la lógica de tu app
            payment_method_id=data.get("payment_method", "online"),  # Puede ser 'online' o similar
            payer_email=order.email,
            status="pending",  # Estado inicial del pago
        )
        
        # Verifica si la orden cumple las condiciones para procesarse
        logger.debug(f"Verificando si la orden {order.custom_order_id} puede procesarse.")
        if can_process_order(order):
            logger.info(f"La orden {order.custom_order_id} cumple las condiciones para procesarse.")
            process_order_documents_and_emails(order)
        else:
            logger.warning(f"La orden {order.custom_order_id} no cumple las condiciones para procesarse.")
            
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
        
        # Verifica si la orden cumple las condiciones para procesarse
        if can_process_order(order):
            process_order_documents_and_emails(order)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


def process_order_documents_and_emails(order):
    """
    Genera documentos (orden y factura) y los envía por correo cuando la orden está lista.
    """
    try:
        # Generar documentos PDF
        order_pdf = generate_pdf(order, doc_type="Orden")
        invoice_pdf = generate_pdf(order, doc_type="Factura")

        # Subir documentos a S3
        order_url = upload_to_s3(order_pdf, os.getenv("AWS_STORAGE_BUCKET_NAME"), f"orders/order_{order.custom_order_id}.pdf")
        invoice_url = upload_to_s3(invoice_pdf, os.getenv("AWS_STORAGE_BUCKET_NAME"), f"invoices/invoice_{order.custom_order_id}.pdf")

        # Enviar correos
        send_email_with_attachments(
            order,
            [
                (f"order_{order.custom_order_id}.pdf", order_pdf, "application/pdf"),
                (f"invoice_{order.custom_order_id}.pdf", invoice_pdf, "application/pdf"),
            ]
        )
        print(f"Order {order.custom_order_id} documents generated and emails sent.")

    except Exception as e:
        print(f"Error processing order {order.custom_order_id}: {str(e)}")

@api_view(['POST'])
def update_payment_status(request, order_id):
    try:
        order = Order.objects.get(custom_order_id=order_id)
        new_status = request.data.get('payment_status')
        
        if new_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            return Response({"error": "Estado de pago inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Registrar cambio
        OrderStatusChangeLog.objects.create(
            order=order,
            previous_status=order.payment_status,
            new_status=new_status,
            field_changed='payment_status',
        )

        # Actualizar estado
        order.payment_status = new_status
        order.update_general_status()  # Actualiza el estado general
        order.save()

        return Response({"message": "Estado de pago actualizado."}, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({"error": "Orden no encontrada."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def update_shipping_status(request, order_id):
    try:
        order = Order.objects.get(custom_order_id=order_id)
        new_status = request.data.get('shipping_status')
        if new_status not in dict(Order.SHIPPING_STATUS_CHOICES):
            return Response({"error": "Estado de despacho inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Registrar el cambio
        OrderStatusChangeLog.objects.create(
            order=order,
            previous_status=order.shipping_status,
            new_status=new_status,
            field_changed='shipping_status',
        )

        # Actualizar el estado
        order.shipping_status = new_status
        order.update_general_status()  # Actualizar el estado general automáticamente
        return Response({"message": "Estado de despacho actualizado correctamente."}, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({"error": "Orden no encontrada."}, status=status.HTTP_404_NOT_FOUND)

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


def can_process_order(order):
    """
    Verifica si la orden cumple las condiciones para ser procesada.
    La orden debe no ser temporal y estar en estado 'in_preparation'.
    """
    return not order.is_temporary and order.order_status == 'in_preparation'

def generate_pdf(order, doc_type="Orden"):
    """
    Genera un PDF profesional de la orden o factura.
    Args:
        order (Order): Objeto de la orden.
        doc_type (str): Tipo de documento (Orden o Factura).
    Returns:
        bytes: Contenido del PDF en memoria.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    elements = []

    # Agregar logo
    logo_path = "https://loocalapp.s3.us-east-1.amazonaws.com/logoloocal.png"
    try:
        logo = Image(logo_path, width=100, height=50)
        elements.append(logo)
    except Exception:
        elements.append(Paragraph("Loocal", styles['Title']))  # Fallback si el logo falla

    # Encabezado
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"{doc_type} #{order.custom_order_id}", styles['Title']))
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(f"Estado: {order.payment_status.capitalize()}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Información del cliente
    elements.append(Paragraph("Información del Cliente", styles['Heading2']))
    elements.append(Paragraph(f"Nombre: {order.firstname} {order.lastname}", styles['Normal']))
    elements.append(Paragraph(f"Email: {order.email} | Teléfono: {order.phone}", styles['Normal']))
    elements.append(Paragraph(f"Documento: {order.document_type} {order.document_number}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Información de entrega
    elements.append(Paragraph("Información de Entrega", styles['Heading2']))
    elements.append(Paragraph(f"Fecha: {order.delivery_date} | Hora: {order.delivery_time}", styles['Normal']))
    elements.append(Paragraph(f"Dirección: {order.address.street}, {order.address.city}, {order.address.state}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Tabla de productos
    elements.append(Paragraph("Detalle de Productos", styles['Heading2']))
    data = [["Cant.", "Descripción", "Precio Unitario", "Subtotal"]]
    for item in order.items.all():
        data.append([
            item.quantity,
            item.product.name,
            f"${round(item.unit_price):,.0f}",  # Redondear precio unitario
            f"${round(item.subtotal):,.0f}"    # Redondear subtotal
        ])
    table = Table(data, colWidths=[50, 200, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Calcular valores redondeados para totales
    subtotal = round(order.subtotal)  # Redondear subtotal
    transport_cost = round(order.transport_cost)  # Redondear transporte
    discount_value = round(order.discount_value)  # Redondear descuento
    total = round(order.total)  # Redondear total

    # Tabla de totales
    totals_data = [
        ["Subtotal de productos", f"${subtotal:,.0f}"],
        ["Costo de transporte", f"${transport_cost:,.0f}"],
    ]
    if order.discount_value > 0:
        totals_data.append(["Descuento aplicado", f"-${discount_value:,.0f}"])
    totals_data.append(["Total final", f"${total:,.0f}"])
    totals_table = Table(totals_data, colWidths=[250, 100])
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(Paragraph("Totales", styles['Heading2']))
    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # Términos y condiciones
    elements.append(Paragraph("Términos y Condiciones", styles['Heading2']))
    elements.append(Paragraph("Gracias por su compra. Por favor conserve este recibo como comprobante.", styles['Normal']))
    elements.append(Paragraph("Si necesita ayuda, comuníquese al WhatsApp +57 3197363596.", styles['Normal']))
    elements.append(Paragraph("Gracias por comprar en Loocal.co", styles['Normal']))

    # Generar el PDF
    doc.build(elements)
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
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=file_content)
    return f"https://{bucket_name}.s3.amazonaws.com/{file_key}"

def send_email_with_attachments(order, attachments):
    """
    Envía dos correos electrónicos separados con documentos adjuntos:
    - Uno al cliente con el resumen de la orden.
    - Otro al administrador con copia del pedido.
    
    Args:
        order (Order): Objeto de la orden.
        attachments (list): Lista de tuplas (filename, content, mime_type).
    """
    # Filtrar adjuntos para el cliente (solo resumen)
    customer_attachments = [
        (filename, content, mime_type)
        for filename, content, mime_type in attachments
        if "order" in filename  # Solo incluir el resumen de la orden
    ]
    # Correo al cliente
    customer_email = EmailMessage(
        subject=f"Tu pedido en Loocal #{order.custom_order_id}",
        body=f"Hola {order.firstname}, gracias por comprar en Loocal. Adjunto encontrarás el resumen de tu orden.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    for filename, content, mime_type in customer_attachments:
        customer_email.attach(filename, content, mime_type)
    customer_email.send()

    # Correo al administrador
    admin_email = EmailMessage(
        subject=f"Nuevo Pedido #{order.custom_order_id} - Copia Administrativa",
        body=f"Adjunto se encuentra una copia del pedido #{order.custom_order_id} realizada por el cliente {order.firstname} {order.lastname}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["camilo@loocal.co"],
    )
    for filename, content, mime_type in attachments:
        admin_email.attach(filename, content, mime_type)
    admin_email.send()
    
def generate_daily_report_pdf(start_time, end_time):
    """
    Genera un PDF con el reporte diario de órdenes.
    Args:
        start_time (datetime): Inicio del período de reporte.
        end_time (datetime): Fin del período de reporte.
    Returns:
        bytes: Contenido del PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    elements = []

    # Agregar encabezado
    elements.append(Paragraph("Reporte Diario de Órdenes", styles['Title']))
    elements.append(Paragraph(f"Período: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Consultar órdenes en el período
    orders = Order.objects.filter(created_at__gte=start_time, created_at__lt=end_time)
    if not orders.exists():
        elements.append(Paragraph("No se encontraron órdenes en el período.", styles['Normal']))
    else:
        # Crear tabla de datos
        data = [["ID Orden", "Fecha/Hora Entrega", "Ciudad", "Estado", "Total"]]
        for order in orders:
            data.append([
                order.custom_order_id,
                f"{order.delivery_date} {order.delivery_time}",
                order.address.city,
                order.payment_status.capitalize(),
                f"${round(order.total):,.0f}"
            ])

        table = Table(data, colWidths=[100, 150, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)

    # Términos
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Reporte generado automáticamente por Loocal.co", styles['Normal']))

    # Generar el PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
def send_daily_report_email(report_content, start_time, end_time):
    """
    Envía el reporte diario por correo.
    Args:
        report_content (bytes): Contenido del PDF del reporte.
        start_time (datetime): Inicio del período.
        end_time (datetime): Fin del período.
    """
    email = EmailMessage(
        subject="Reporte Diario de Órdenes",
        body=f"Adjunto encontrarás el reporte diario de órdenes del período {start_time.strftime('%Y-%m-%d %H:%M')} a {end_time.strftime('%Y-%m-%d %H:%M')}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["camilo@loocal.co"],
    )
    filename = f"reporte_diario_{start_time.strftime('%Y%m%d%H%M')}_a_{end_time.strftime('%Y%m%d%H%M')}.pdf"
    email.attach(filename, report_content, "application/pdf")
    email.send()
def save_report_to_s3(report_content, start_time, end_time):
    """
    Guarda el reporte diario en la carpeta reportes de S3.
    Args:
        report_content (bytes): Contenido del PDF.
        start_time (datetime): Inicio del período.
        end_time (datetime): Fin del período.
    Returns:
        str: URL del archivo guardado.
    """
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
    filename = f"reportes/reporte_diario_{start_time.strftime('%Y%m%d%H%M')}_a_{end_time.strftime('%Y%m%d%H%M')}.pdf"
    return upload_to_s3(report_content, bucket_name, filename)

def generate_and_send_daily_report():
    """
    Genera y envía el reporte diario de órdenes.
    """
    # Definir el intervalo de tiempo (últimas 24 horas hasta las 5:00 pm del día actual)
    timezone = pytz.timezone("America/Bogota")
    end_time = timezone.localize(now().replace(hour=17, minute=0, second=0, microsecond=0))
    start_time = end_time - timedelta(days=1)

    # Generar reporte en PDF
    report_content = generate_daily_report_pdf(start_time, end_time)

    # Guardar en S3
    save_report_to_s3(report_content, start_time, end_time)

    # Enviar por correo
    send_daily_report_email(report_content, start_time, end_time)

# Programar la ejecución diaria
scheduler = BackgroundScheduler()
scheduler.add_job(generate_and_send_daily_report, 'cron', hour=17, minute=0, timezone="America/Bogota")
scheduler.start()

@api_view(['POST'])
def generate_report_endpoint(request):
    """
    Endpoint para generar y enviar el reporte diario de órdenes.
    """
    try:
        # Configurar zona horaria
        timezone = pytz.timezone("America/Bogota")

        # Asegúrate de que now() sea naive antes de asignar una zona horaria
        naive_now = datetime.now().replace(tzinfo=None)

        # Calcular el intervalo de tiempo: desde las 5 pm de ayer hasta las 5 pm de hoy
        end_time = timezone.localize(naive_now.replace(hour=17, minute=0, second=0, microsecond=0))
        start_time = end_time - timedelta(days=1)

        # Generar contenido del reporte en PDF
        report_content = generate_daily_report_pdf(start_time, end_time)

        # Guardar el reporte en S3
        save_report_to_s3(report_content, start_time, end_time)

        # Enviar el reporte por correo
        send_daily_report_email(report_content, start_time, end_time)

        return Response({"message": "Reporte generado, guardado y enviado con éxito."}, status=200)

    except Exception as e:
        return Response({"error": f"Error al generar el reporte: {str(e)}"}, status=500)