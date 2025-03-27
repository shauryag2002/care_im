"""Unit tests for care_im message handlers."""

import pytest
from unittest.mock import patch, MagicMock

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.handler import WhatsAppMessageHandler
from care_im.templates.message_templates import MessageTemplates


class TestBaseHandler:
    """Unit tests for the BaseHandler class."""
    
    def test_format_phone_number(self):
        """Test phone number formatting."""
        handler = BaseHandler("+919876543210")
        
        assert handler._format_phone_number("+919876543210") == "919876543210"
        assert handler._format_phone_number("9876543210") == "919876543210"
        assert handler._format_phone_number("919876543210") == "919876543210"
        
    def test_handle_error(self):
        """Test error handling."""
        handler = BaseHandler("+919876543210")
        error = ValueError("Test error")
        
        with patch("logging.getLogger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            result = handler._handle_error(error, "testing")
            
            mock_logger_instance.error.assert_called_once()
            assert "Sorry, I couldn't complete the testing" in result


@pytest.mark.django_db
class TestMessageHandler:
    """Unit tests for the WhatsAppMessageHandler class."""
    
    @patch("care_im.messaging.handler.WhatsAppMessageHandler._identify_user")
    def test_unregistered_user(self, mock_identify):
        """Test handling of unregistered users."""
        # Arrange
        mock_identify.return_value = None  # User not identified
        handler = WhatsAppMessageHandler("+919876543210")
        handler.user = None
        handler.patient = None
        
        # Act
        response = handler.process_message("help")
        
        # Assert
        # Should return unregistered user message
        assert "not registered" in response
        
    @patch("care_im.messaging.handler.WhatsAppMessageHandler._identify_user")
    @patch("care_im.messaging.template_sender.WhatsAppSender.send_template")
    def test_help_message(self, mock_send_template, mock_identify):
        """Test help message handling."""
        # Arrange
        mock_identify.return_value = None
        mock_send_template.return_value = {"status": "success"}
        
        handler = WhatsAppMessageHandler("+919876543210")
        handler.user = MagicMock()
        handler.patient = MagicMock()
        
        # Act
        with patch.object(handler, "_send_help_message") as mock_help:
            mock_help.return_value = "Help message sent"
            response = handler.process_message("help")
            
            # Assert
            mock_help.assert_called_once()
            assert response == "Help message sent"


class TestMessageTemplates:
    """Unit tests for message templates."""
    
    def test_error_message(self):
        """Test error message template."""
        error_msg = MessageTemplates.error_message()
        assert "Sorry, I couldn't process your request" in error_msg
        
    def test_help_message(self):
        """Test help message template."""
        patient_help = MessageTemplates.help_message(is_patient=True)
        staff_help = MessageTemplates.help_message(is_patient=False)
        
        assert "medications" in patient_help
        assert "schedule" in staff_help