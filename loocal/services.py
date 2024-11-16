# services.py
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
import random

def send_email_otp(email, otp_code):
    subject = 'Tu código de verificación'
    message = f'Tu código de verificación es {otp_code}. Este código expirará en 10 minutos.'
    from_email = 'noreply@loocal.co'
    send_mail(subject, message, from_email, [email], fail_silently=False)

def send_sms_otp(phone_number, otp_code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=f'Tu código de verificación es {otp_code}. Este código expirará en 10 minutos.',
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    
def generate_otp():
    # Genera un código OTP de 4 dígitos
    return f"{random.randint(1000, 9999)}"

def send_email_otp(email, otp_code):
    subject = 'Tu código de verificación'
    message = f'Tu código de verificación es {otp_code}. Este código expirará en 10 minutos.'
    from_email = 'noreply@loocal.co'
    send_mail(subject, message, from_email, [email], fail_silently=False)
