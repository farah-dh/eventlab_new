from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, to_email, subject, body, from_email=None):
    """Send a single email notification."""
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info("Email sent to %s: %s", to_email, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        raise self.retry(exc=exc)


@shared_task
def send_bulk_email(recipient_list, subject, body):
    """Send bulk emails."""
    from django.core.mail import send_mass_mail
    messages = [(subject, body, settings.DEFAULT_FROM_EMAIL, [email]) for email in recipient_list]
    send_mass_mail(messages, fail_silently=True)


@shared_task
def send_password_reset_email(user_id, token):
    """Send password reset email."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}&email={user.email}"
        body = f"Click the link to reset your password: {reset_url}\n\nThis link expires in 2 hours."
        send_email_notification.delay(user.email, "Password Reset Request", body)
    except User.DoesNotExist:
        logger.warning("Password reset requested for non-existent user: %s", user_id)


@shared_task
def send_order_confirmation(order_id):
    """Send order confirmation to user."""
    from apps.orders.models import Order
    try:
        order = Order.objects.select_related("user", "event").get(pk=order_id)
        if order.user:
            body = (
                f"Hi {order.user.full_name},\n\n"
                f"Your order for '{order.event.title}' has been confirmed.\n"
                f"Order ID: #{order.pk}\n"
                f"Quantity: {order.quantity}\n"
                f"Total: {order.total_price}\n\n"
                "Thank you for your purchase!"
            )
            send_email_notification.delay(order.user.email, "Order Confirmation", body)
    except Order.DoesNotExist:
        logger.warning("Order confirmation for non-existent order: %s", order_id)
