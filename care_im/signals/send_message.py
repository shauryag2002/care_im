from django.db.models.signals import post_save
from django.dispatch import receiver
from care.facility.models.patient import PatientMobileOTP
from care.emr.models import QuestionnaireResponse
from care.emr.models import (EncounterOrganization, Patient,TokenBooking)
from care_im.care_im.utils.message_handler import WhatsAppMessageHandler
from care_im.care_im.utils.whatsapp_client import WhatsAppClient
from care_im.care_im.utils.send_message_templates import WhatsAppSender
from django.core.cache import cache
from celery import shared_task

import logging
logger = logging.getLogger(__name__)

# Separate Celery tasks
@shared_task
def send_otp_message_task(phone_number, otp):
    try:
        whatsapp_client = WhatsAppClient()
        whatsapp_client.send_message(
            phone_number,
            f"Kerala Care Login, OTP {otp}. Please do not share this Confidential Login Token with anyone else",
        )
        # WhatsAppSender().send_template(
        #     to_number=phone_number,
        #     template_name="care_otp",
        #     params={
        #         "body": [
        #             {"type": "text", "text": f"{otp}"}
        #         ]
        #     }
        # )
    except Exception as e:
        logger.error(f"Failed to send OTP: {str(e)}")

@shared_task
def send_questionnaire_response_task(phone_number):
    lock_id = f"questionnaire_response:{phone_number}"

    # Set lock with expiry of 10 seconds
    if cache.add(lock_id, "locked", timeout=10):
        try:
            whatsapp_client = WhatsAppMessageHandler(phone_number)
            whatsapp_client.send_whatsapp_message(
                message="medications",
                to_number=phone_number,
            )
            # medications_response=whatsapp_client._get_current_medications()
            # whatsapp_sender = WhatsAppSender()
            # whatsapp_sender.send_template(
            #     phone_number,
            #     "care_medications",
            #     params={
            #         "body": [
            #             {"type": "text", "text": medications_response},
            #         ]
            #     }
            # )
        except Exception as e:
            logger.error(f"Failed to send questionnaire response: {str(e)}")
        finally:
            cache.delete(lock_id)  # Remove lock after execution
    else:
        logger.info(f"Skipping duplicate request for {phone_number}")


@shared_task
def send_procedures_task(phone_number):
    try:
        whatsapp_client = WhatsAppMessageHandler(phone_number)
        whatsapp_client.send_whatsapp_message(
            message="procedures",
            to_number=phone_number,
        )
        # procedure_response=whatsapp_client._get_procedures()
        # whatsapp_sender = WhatsAppSender()
        # whatsapp_sender.send_template(
        #     phone_number,
        #     "care_procedures",
        #     params={
        #         "body": [
        #             {"type": "text", "text": procedure_response},
        #         ]
        #     }
        # )
    except Exception as e:
        logger.error(f"Failed to send procedures message: {str(e)}")

@shared_task
def send_patient_registration_task(phone_number, name):
    try:
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
def send_token_booking_task(phone_number):
    try:
        whatsapp_client = WhatsAppMessageHandler(phone_number)
        whatsapp_client.send_whatsapp_message(
            message="token",
            to_number=phone_number,
        )
        # token_response=whatsapp_client._get_token_booking()
        # whatsapp_sender = WhatsAppSender()
        # whatsapp_sender.send_template(
        #     phone_number,
        #     "care_token",
        #     params={
        #         "body": [
        #             {"type": "text", "text": token_response},
        #         ]
        #     }
        # )
    except Exception as e:
        logger.error(f"Failed to send token booking message: {str(e)}")

# Signal handlers with dispatch_uid
@receiver(post_save, sender=PatientMobileOTP, dispatch_uid="patient_otp_signal")
def handle_otp_message(sender, instance, created, **_):
    if created:
        logger.info(f"Scheduling OTP message for {instance.phone_number}")
        send_otp_message_task.delay(instance.phone_number, instance.otp)

@receiver(post_save, sender=QuestionnaireResponse, dispatch_uid="questionnaire_response_signal")
def handle_questionnaire_response(sender, instance, created, **_):
    if created :
        logger.info(f"Scheduling questionnaire response for {instance.patient.phone_number}")
        send_questionnaire_response_task.delay(instance.patient.phone_number)

@receiver(post_save, sender=Patient, dispatch_uid="patient_registration_signal")
def handle_patient_registration(sender, instance, created, **_):
    if created:
        logger.info(f"Scheduling patient registration message for {instance.phone_number}")
        send_patient_registration_task.delay(instance.phone_number,instance.name)

@receiver(post_save, sender=EncounterOrganization, dispatch_uid="encounter_organization_signal")
def handle_encounter_organization(sender, instance, created, **_):
    if created and hasattr(instance.encounter, 'patient'):
        logger.info(f"Scheduling encounter organization message for {instance.encounter.patient.phone_number}")
        send_procedures_task.delay(instance.encounter.patient.phone_number)

@receiver(post_save, sender=TokenBooking, dispatch_uid="token_booking_signal")
def handle_token_booking(sender, instance: TokenBooking, created: bool, **_):
    if created:
        logger.info(f"Scheduling token booking message for {instance.patient.phone_number}")
        send_token_booking_task.delay(instance.patient.phone_number)
