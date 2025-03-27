"""Signal handlers for sending WhatsApp messages."""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from celery import shared_task

from care.facility.models.patient import PatientMobileOTP
from care.emr.models import QuestionnaireResponse, EncounterOrganization, Patient, TokenBooking

from care_im.messaging.template_sender import WhatsAppSender
from care_im.messaging.handler import WhatsAppMessageHandler

logger = logging.getLogger(__name__)


# Separate Celery tasks for each message type
@shared_task
def send_otp_message_task(phone_number: str, otp: str):
    """Send OTP message via WhatsApp."""
    try:
        logger.info(f"Sending OTP message to {phone_number}")
        WhatsAppSender().send_template(
            to_number=phone_number,
            template_name="care_otp",
            params={
                "body": [
                    {"type": "text", "text": f"{otp}"}
                ],
                "button": [
                    {"type": "text", "text": f"{otp}", "sub_type": "url", "index": 0}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Failed to send OTP: {str(e)}")


@shared_task
def send_questionnaire_response_task(phone_number: str):
    """Send questionnaire response (medications) via WhatsApp."""
    lock_id = f"questionnaire_response:{phone_number}"

    # Set lock with expiry of 10 seconds to prevent duplicate messages
    if cache.add(lock_id, "locked", timeout=10):
        try:
            logger.info(f"Sending questionnaire response to {phone_number}")
            whatsapp_client = WhatsAppMessageHandler(phone_number)
            whatsapp_client.process_message(message_text="medications")
        except Exception as e:
            logger.error(f"Failed to send questionnaire response: {str(e)}")
        finally:
            cache.delete(lock_id)  # Remove lock after execution
    else:
        logger.info(f"Skipping duplicate questionnaire response request for {phone_number}")


@shared_task
def send_procedures_task(phone_number: str):
    """Send procedures information via WhatsApp."""
    try:
        logger.info(f"Sending procedures information to {phone_number}")
        whatsapp_client = WhatsAppMessageHandler(phone_number)
        whatsapp_client.process_message(message_text="procedures")
    except Exception as e:
        logger.error(f"Failed to send procedures message: {str(e)}")


@shared_task
def send_patient_registration_task(phone_number: str, name: str):
    """Send patient registration confirmation via WhatsApp."""
    try:
        logger.info(f"Sending registration confirmation to {phone_number}")
        whatsapp_sender = WhatsAppSender()
        whatsapp_sender.send_template(
            phone_number,
            "care_greeting",
            params={
                "body": [
                    {"type": "text", "text": name},
                    {"type": "text", "text": "Your registration is successful."},
                    {"type": "text", "text": "Please ensure your details are correct."}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Failed to send patient registration message: {str(e)}")


@shared_task
def send_token_booking_task(phone_number: str):
    """Send token booking information via WhatsApp."""
    try:
        logger.info(f"Sending token booking information to {phone_number}")
        whatsapp_client = WhatsAppMessageHandler(phone_number)
        whatsapp_client.process_message(message_text="token")
    except Exception as e:
        logger.error(f"Failed to send token booking message: {str(e)}")


# Signal handlers with dispatch_uid to prevent duplicate registration
@receiver(post_save, sender=PatientMobileOTP, dispatch_uid="patient_otp_signal")
def handle_otp_message(sender, instance, created, **_):
    """Handle OTP generation and send OTP message."""
    if created:
        logger.info(f"OTP created for {instance.phone_number}, scheduling message")
        send_otp_message_task.delay(instance.phone_number, instance.otp)


@receiver(post_save, sender=QuestionnaireResponse, dispatch_uid="questionnaire_response_signal")
def handle_questionnaire_response(sender, instance, created, **_):
    """Handle questionnaire response creation and send medication information."""
    if created:
        logger.info(f"Questionnaire response created for patient {instance.patient.id}")
        send_questionnaire_response_task.delay(instance.patient.phone_number)


@receiver(post_save, sender=Patient, dispatch_uid="patient_registration_signal")
def handle_patient_registration(sender, instance, created, **_):
    """Handle patient registration and send welcome message."""
    if created and instance.phone_number:
        logger.info(f"Patient {instance.id} registered with phone {instance.phone_number}")
        send_patient_registration_task.delay(instance.phone_number, instance.name)


@receiver(post_save, sender=EncounterOrganization, dispatch_uid="encounter_organization_signal")
def handle_encounter_organization(sender, instance, created, **_):
    """Handle encounter organization creation and send procedures information."""
    if created and hasattr(instance.encounter, 'patient') and instance.encounter.patient.phone_number:
        logger.info(f"Encounter organization created for patient {instance.encounter.patient.id}")
        send_procedures_task.delay(instance.encounter.patient.phone_number)


@receiver(post_save, sender=TokenBooking, dispatch_uid="token_booking_signal")
def handle_token_booking(sender, instance: TokenBooking, created: bool, **_):
    """Handle token booking creation and send booking confirmation."""
    if created and instance.patient.phone_number:
        logger.info(f"Token booking created for patient {instance.patient.id}")
        send_token_booking_task.delay(instance.patient.phone_number)
