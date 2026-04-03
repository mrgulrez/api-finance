from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

def send_verification_email(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Strip trailing slash from FRONTEND_URL if present, though we handle mostly without.
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    verify_url = f"{frontend_url}/verify-email/{uidb64}/{token}"

    subject = "Verify your Finance Dashboard Account"
    message = f"Hello {user.full_name},\n\nPlease verify your email address by clicking the link below:\n\n{verify_url}\n\nThanks,\nFinance Dashboard Team"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_password_reset_email(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    reset_url = f"{frontend_url}/reset-password/{uidb64}/{token}"

    subject = "Reset your Finance Dashboard Password"
    message = f"Hello {user.full_name},\n\nYou requested a password reset. Click the link below to set a new password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email.\n\nThanks,\nFinance Dashboard Team"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
