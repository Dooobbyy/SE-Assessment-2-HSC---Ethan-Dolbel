# core/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode
import logging
import secrets
from django.utils import timezone

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
    
def send_settings_change_verification_email(user, new_email, request=None):
    """
    Sends an email verification link to the user's OLD email address
    to confirm an email address change.
    This function generates a specific token for email change confirmation.
    """
    token = secrets.token_urlsafe(32)
    expiry_minutes = 60 # Token valid for 1 hour

    user.email_change_token = token
    
    user.email_change_token_expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
    user.email_change_new_email = new_email
    # Use update_fields to only update these specific fields
    user.save(update_fields=['email_change_token', 'email_change_token_expires_at', 'email_change_new_email'])
    
    if request:
        # Build the confirmation URL
        confirmation_url = request.build_absolute_uri(
            f"{reverse('confirm_email_change')}?{urlencode({'token': token})}"
        )
    else:
        confirmation_url = f"/confirm-email-change/?token={token}" # Fallback

    subject = 'Confirm Email Address Change'
    message = (
        f'Hi {user.username},\n\n'
        f'You have requested to change your account email address from {user.email} to {new_email}.\n\n'
        f'To confirm this change, please click the link below:\n\n'
        f'{confirmation_url}\n\n'
        f'This link will expire in 1 hour.\n\n'
        f'If you did not request this change, please ignore this email or contact support.\n\n'
        f'Thank you!'
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    # Send to the OLD email address for verification
    recipient_list = [user.email] 

    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"Email change confirmation sent to {user.email} for user {user.username}.")
        return True
    except Exception as e:
        error_msg = f"Failed to send email change confirmation to {user.email}: {e}"
        logger.error(error_msg)
        print(error_msg) # For development
        return False

# Add this new utility function to confirm the email change
def confirm_email_change_token(user, token):
    """
    Checks if the provided token is valid for the user's pending email change.
    """
    from django.utils import timezone
    # Check if the user has a pending email change with a token
    if not user.email_change_token or not user.email_change_token_expires_at or not user.email_change_new_email:
        return False
    
    # Check if the token matches
    if user.email_change_token != token:
        return False
        
    # Check if the token is expired
    if timezone.now() > user.email_change_token_expires_at:
        user.email_change_token = None
        user.email_change_token_expires_at = None
        user.email_change_new_email = None
        user.save(update_fields=['email_change_token', 'email_change_token_expires_at', 'email_change_new_email'])
        return False
    
    # Token is valid
    return True
