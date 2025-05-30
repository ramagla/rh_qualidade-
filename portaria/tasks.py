# rh_qualidade/portaria/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def enviar_email_recado(subject, message, recipient, html_message):
    send_mail(
        subject=subject,
        message=message,
        from_email="no-reply@brasmol.com.br",
        recipient_list=[recipient],
        fail_silently=True,
        html_message=html_message,
    )
