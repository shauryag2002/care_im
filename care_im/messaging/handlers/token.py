"""Handler for token booking related requests."""

import logging
from typing import Dict, Any, Optional

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.template_sender import WhatsAppSender

logger = logging.getLogger(__name__)


class TokenHandler(BaseHandler):
    """Handler for token booking related functionality."""
    
    def get_token_booking(self, template_sender: WhatsAppSender) -> str:
        """
        Get token booking details for the patient.
        
        Args:
            template_sender: WhatsApp template sender instance
            
        Returns:
            Status message indicating whether the token booking was sent
        """
        try:
            if not self.patient:
                return "No patient record found. Please register to get your token booking details."

            # Retrieve token booking information
            token_booking_info = self._retrieve_token_booking_info()

            if not token_booking_info:
                template_sender.send_template(
                    to_number=self.from_number,
                    template_name="care_token",
                    params={
                        "body": [
                            {"type": "text", "text": "🚫 No token booking details found."}
                        ]
                    }
                )
                return "No token booking details available at this time."
                
            # Format and send the token booking information
            formatted_message = self._format_token_booking_message(token_booking_info)
            
            template_sender.send_template(
                to_number=self.from_number,
                template_name="care_token",
                params={
                    "body": [
                        {"type": "text", "text": formatted_message}
                    ]
                }
            )
            
            return "Token booking information sent successfully"
            
        except Exception as e:
            return self._handle_error(e, "retrieving token booking details")
    
    def _retrieve_token_booking_info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve token booking information for the patient.
        
        Returns:
            Dictionary containing token booking information or None if not found
        """
        try:
            from care.emr.models import TokenBooking

            # Get the latest token booking for the patient
            token_booking = TokenBooking.objects.filter(
                patient=self.patient
            ).order_by('-created_date').first()

            if not token_booking:
                return None
                
            return {
                'slot_id': token_booking.token_slot.id,
                'slot_date': token_booking.token_slot.start_datetime.strftime('%d %B, %Y'),
                'slot_time': token_booking.token_slot.end_datetime.strftime('%I:%M %p'),
                'booked_on': token_booking.booked_on.strftime('%d %B, %Y %I:%M %p'),
                'status': token_booking.status,
                'reason': token_booking.reason_for_visit or 'Not specified'
            }
            
        except Exception as e:
            logger.error(f"Error retrieving token booking info: {str(e)}")
            return None
            
    def _format_token_booking_message(self, booking_info: Dict[str, Any]) -> str:
        """
        Format token booking information into a readable message.
        
        Args:
            booking_info: Dictionary containing token booking information
            
        Returns:
            Formatted message string
        """
        return (
            f"📅 Appointment on {booking_info.get('slot_date')} "
            f"at {booking_info.get('slot_time')} | "
            f"Status: {booking_info.get('status')} | "
            f"Booked on: {booking_info.get('booked_on')} | "
            f"Reason: {booking_info.get('reason')}"
        )