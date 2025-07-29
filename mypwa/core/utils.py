# core/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode

def send_verification_email(user, request=None):
    """
    Sends an email verification link to the user.
    """
    if not user.verification_token:
        user.generate_verification_token()

    if request:
        verification_url = request.build_absolute_uri(
            f"{reverse('verify_email')}?{urlencode({'token': user.verification_token})}"
        )
    else:
        verification_url = f"/verify_email/?token={user.verification_token}"

    subject = 'Verify Your Email Address'
    message = f'Hi {user.username},\n\nPlease click the link below to verify your email address:\n\n{verification_url}\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        print(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Failed to send verification email to {user.email}: {e}")
        return False

def send_password_reset_email(user, request=None):
    """
    Sends a password reset link to the user.
    """
    if not user.reset_token or not user.is_reset_token_valid():
         user.generate_reset_token()

    if request:
        reset_url = request.build_absolute_uri(
            f"{reverse('reset_password')}?{urlencode({'token': user.reset_token})}"
        )
    else:
        reset_url = f"/reset_password/?token={user.reset_token}"

    subject = 'Password Reset Request'
    message = f'Hi {user.username},\n\nYou requested a password reset. Click the link below to reset your password:\n\n{reset_url}\n\nThis link will expire in 1 hour.\n\nIf you did not request this, please ignore this email.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        print(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {user.email}: {e}")
        return False