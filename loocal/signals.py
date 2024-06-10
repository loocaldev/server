# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.mail import send_mail

@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    print("User logged in signal received!")
    # Envía un correo electrónico al usuario
    send_mail(
        'Inicio de sesión exitoso',
        '¡Hola! Has iniciado sesión en nuestro sistema.',
        'camilo@loocal.co',  # Remitente
        [user.email],  # Destinatario
        fail_silently=False,
    )