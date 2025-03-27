"""WhatsApp message handler implementation."""

import logging
from typing import Dict, Any, Optional, List

from django.db.models import Q

from care.facility.models import Facility, FacilityUser
from care.users.models import User
from care.emr.models import Patient
from care.emr.models.medication_request import MedicationRequest
from care.emr.resources.medication.request.spec import MedicationRequestStatus

from care_im.messaging.client import WhatsAppClient
from care_im.messaging.template_sender import WhatsAppSender
from care_im.templates.message_templates import MessageTemplates

logger = logging.getLogger(__name__)


class WhatsAppMessageHandler:
    """
    Handler for WhatsApp messages.
    
    Processes incoming messages, identifies users, and dispatches appropriate responses.
    """
    
    def __init__(self, from_number: str):
        """
        Initialize the message handler.
        
        Args:
            from_number: The sender's phone number
        """
        self.from_number = from_number
        self.user = None
        self.patient = None
        self._identify_user()
        self.templates = MessageTemplates()
        self.whatsapp_client = WhatsAppClient()
        self.whatsapp_template_sender = WhatsAppSender()

    def _identify_user(self):
        """Identify if the sender is a patient or staff member based on phone number."""
        try:
            logger.info(f"Identifying user with phone number: {self.from_number}")

            # Normalize phone number
            normalized_number = self._normalize_phone_number(self.from_number)
            logger.info(f"Looking up user/patient with normalized number: {normalized_number}")

            # Try to find a patient record
            self._find_patient(normalized_number)
            
            # If no patient found, try to find a staff user
            if not self.patient:
                self._find_staff_user(normalized_number)
                
            logger.info(f"Identified user: {self.user}, patient: {self.patient}")
        except Exception as e:
            logger.error(f"Error in user identification: {str(e)}")
            self.user = None
            self.patient = None
            
    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize phone number format.
        
        Args:
            phone_number: Raw phone number
            
        Returns:
            Normalized phone number with country code
        """
        normalized_number = phone_number.strip().replace(" ", "")
        
        if not normalized_number.startswith('+'):
            if (normalized_number.startswith('91') and len(normalized_number) >= 12):
                normalized_number = f"+{normalized_number}"
            elif len(normalized_number) == 10:
                normalized_number = f"+91{normalized_number}"
            else:
                normalized_number = f"+{normalized_number}"
                
        return normalized_number
        
    def _find_patient(self, normalized_number: str) -> None:
        """
        Find a patient by phone number.
        
        Args:
            normalized_number: Normalized phone number
        """
        try:
            # First try primary phone number
            self.patient = Patient.objects.filter(
                phone_number=normalized_number
            ).order_by('-modified_date').first()
            
            if self.patient:
                logger.info(f"Found patient: {self.patient}")
                return
                
            # If no patient found, try emergency contact
            self.patient = Patient.objects.filter(
                emergency_phone_number=normalized_number
            ).first()
            
            if self.patient:
                logger.info(f"Found patient via emergency contact: {self.patient}")
        except Exception as e:
            logger.error(f"Error finding patient: {str(e)}")
            
    def _find_staff_user(self, normalized_number: str) -> None:
        """
        Find a staff user by phone number.
        
        Args:
            normalized_number: Normalized phone number
        """
        try:
            self.user = User.objects.filter(phone_number=normalized_number).first()
            
            if self.user:
                logger.info(f"Found staff user: {self.user}")
                return
                
            self.user = User.objects.filter(alt_phone_number=normalized_number).first()
            
            if self.user:
                logger.info(f"Found staff user via alternate number: {self.user}")
        except Exception as e:
            logger.error(f"Error finding staff user: {str(e)}")
            
    def process_message(self, message_text: str) -> str:
        """
        Process incoming message and return appropriate response.
        
        Args:
            message_text: The message content from the user
            
        Returns:
            Response message or status
        """
        message_text = message_text.lower().strip()

        if not (self.user or self.patient):
            return self._handle_unregistered_user()

        if message_text == 'help':
            return self._send_help_message()

        # Route message to appropriate handler based on user type
        if self.patient or (self.user and not self.user.is_staff):
            return self._handle_patient_request(message_text)
        else:
            return self._handle_staff_request(message_text)
            
    def _send_help_message(self) -> str:
        """
        Send the appropriate help message based on user type.
        
        Returns:
            Status message
        """
        if self.patient:
            return self.whatsapp_template_sender.send_template(
                to_number=self.from_number,
                template_name="care_help_patient"
            )
        else:
            return self.whatsapp_template_sender.send_template(
                to_number=self.from_number,
                template_name="care_help_staff"
            )

    def _handle_unregistered_user(self) -> str:
        """
        Handle messages from unregistered users.
        
        Returns:
            Information message for unregistered users
        """
        return self.templates.unregistered_user_message()

    def _handle_patient_request(self, message_text: str) -> str:
        """
        Handle requests from patients.
        
        Args:
            message_text: The message from the patient
            
        Returns:
            Response status
        """
        if 'records' in message_text:
            return self._get_patient_records()
        elif 'medications' in message_text:
            logger.info(f"Getting medications for patient: {self.patient}")
            return self._get_current_medications()
        elif 'procedures' in message_text:
            return self._get_procedures()
        elif 'token' in message_text:
            return self._get_token_booking()
        else:
            return self.templates.help_message(is_patient=True)

    def _handle_staff_request(self, message_text: str) -> str:
        """
        Handle requests from hospital staff.
        
        Args:
            message_text: The message from the staff member
            
        Returns:
            Response status
        """
        if 'schedule' in message_text:
            return self._get_staff_schedule()
        elif message_text.startswith('/s '):
            try:
                facility_number = message_text.split()[1]
                return self._get_staff_schedule(facility_id=facility_number)
            except IndexError:
                return "Invalid command. Use '/s <facility_number>'"
        elif message_text.startswith('/a '):
            try:
                facility_number = message_text.split()[1]
                return self._get_asset_status(facility_id=facility_number)
            except IndexError:
                return "Invalid command. Use '/a <facility_number>'"
        elif message_text.startswith('/r '):
            try:
                facility_number = message_text.split()[1]
                return self._get_resource_status(facility_id=facility_number)
            except IndexError:
                return "Invalid command. Use '/r <facility_number>'"
        elif 'asset' in message_text:
            return self._get_asset_status()
        elif 'resource' in message_text:
            return self._get_resource_status()
        else:
            return self.templates.help_message(is_patient=False)

    # The following methods will be implemented in separate handler modules
    # to keep this file at a manageable size

    def _get_patient_records(self) -> str:
        """Get patient records. Will be implemented in PatientHandler."""
        from care_im.messaging.handlers.patient import PatientHandler
        handler = PatientHandler(self.from_number, self.patient, self.user)
        return handler.get_patient_records(self.whatsapp_template_sender)

    def _get_current_medications(self) -> str:
        """Get active medications for the patient. Will be implemented in MedicationHandler."""
        from care_im.messaging.handlers.medication import MedicationHandler
        handler = MedicationHandler(self.from_number, self.patient, self.user)
        return handler.get_medications(self.whatsapp_template_sender)

    def _get_procedures(self) -> str:
        """Get procedures for the patient. Will be implemented in ProceduresHandler."""
        from care_im.messaging.handlers.procedures import ProceduresHandler
        handler = ProceduresHandler(self.from_number, self.patient, self.user)
        return handler.get_procedures(self.whatsapp_template_sender)

    def _get_token_booking(self) -> str:
        """Get token booking details. Will be implemented in TokenHandler."""
        from care_im.messaging.handlers.token import TokenHandler
        handler = TokenHandler(self.from_number, self.patient, self.user)
        return handler.get_token_booking(self.whatsapp_template_sender)

    def _get_staff_schedule(self, facility_id=None) -> str:
        """Get staff schedule. Will be implemented in StaffHandler."""
        from care_im.messaging.handlers.staff import StaffHandler
        handler = StaffHandler(self.from_number, self.patient, self.user)
        return handler.get_staff_schedule(self.whatsapp_client, facility_id)

    def _get_asset_status(self, facility_id=None) -> str:
        """Get asset status. Will be implemented in FacilityHandler."""
        from care_im.messaging.handlers.facility import FacilityHandler
        handler = FacilityHandler(self.from_number, self.patient, self.user)
        return handler.get_asset_status(facility_id)

    def _get_resource_status(self, facility_id=None) -> str:
        """Get resource status. Will be implemented in ResourceHandler."""
        from care_im.messaging.handlers.resource import ResourceHandler
        handler = ResourceHandler(self.from_number, self.patient, self.user)
        return handler.get_resource_status(self.whatsapp_client, facility_id)

    def send_whatsapp_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp."""
        formatted_number = to_number.replace('+', '')
        if not formatted_number.startswith('91'):
            formatted_number = '91' + formatted_number
        return self.whatsapp_client.send_message(formatted_number, message)

    def send_whatsapp_text(self, to_number: str, message: str) -> Dict[str, Any]:
        """Process a message and send the response via WhatsApp."""
        response = self.process_message(message)
        formatted_number = to_number.replace('+', '')
        if not formatted_number.startswith('91'):
            formatted_number = '91' + formatted_number
        return self.whatsapp_client.send_message(formatted_number, response)