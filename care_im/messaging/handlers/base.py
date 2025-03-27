"""Base handler class for WhatsApp message processing."""

from typing import Optional, Dict, Any

from care.users.models import User
from care.emr.models import Patient


class BaseHandler:
    """
    Base class for all message handlers.
    
    Provides common functionality for handling WhatsApp messages.
    """
    
    def __init__(self, from_number: str, patient: Optional[Patient] = None, user: Optional[User] = None):
        """
        Initialize the base handler.
        
        Args:
            from_number: The sender's phone number
            patient: Patient object associated with this number, if any
            user: User object associated with this number, if any
        """
        self.from_number = from_number
        self.patient = patient
        self.user = user
        
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for WhatsApp API.
        
        Args:
            phone_number: Phone number to format
            
        Returns:
            Formatted phone number (without + prefix, with 91 country code)
        """
        formatted_number = phone_number.replace('+', '')
        if not formatted_number.startswith('91'):
            formatted_number = '91' + formatted_number
        return formatted_number
        
    def _handle_error(self, error: Exception, context: str = "operation") -> str:
        """
        Log and handle errors in handlers.
        
        Args:
            error: Exception that occurred
            context: Description of what was being attempted
            
        Returns:
            User-friendly error message
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.error(f"Error during {context}: {str(error)}", exc_info=True)
        return f"Sorry, I couldn't complete the {context}. Please try again later."