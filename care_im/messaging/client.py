"""WhatsApp API client implementation."""

import logging
import requests
from typing import Dict, Any, Optional

from care_im.core.config import plugin_settings

logger = logging.getLogger(__name__)

class WhatsAppClient:
    """
    Client for the WhatsApp Business API.
    
    Handles sending messages, webhook verification, and processing incoming events.
    """
    
    def __init__(self):
        """Initialize the WhatsApp client with configuration from settings."""
        self.access_token = plugin_settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = plugin_settings.WHATSAPP_PHONE_NUMBER_ID
        self.webhook_verify_token = plugin_settings.WHATSAPP_VERIFY_TOKEN
        self.api_version = plugin_settings.WHATSAPP_API_VERSION
        self.base_url = f'https://graph.facebook.com/{self.api_version}'

        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp configuration is incomplete. Check environment variables or settings.")

        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp number.
        
        Args:
            to_number: Recipient's phone number with country code (e.g., "911234567890")
            message: Text message content
            
        Returns:
            API response as dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        endpoint = f'{self.base_url}/{self.phone_number_id}/messages'

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            raise

    def verify_webhook(self, token: str) -> bool:
        """
        Verify the webhook token from Meta.
        
        Args:
            token: The token to verify
            
        Returns:
            True if token matches the configured verify token, False otherwise
        """
        return token == self.webhook_verify_token

    def process_webhook_event(self, data: Dict[str, Any]) -> None:
        """
        Process incoming webhook events from WhatsApp.
        
        Args:
            data: Webhook event data
            
        Raises:
            KeyError, IndexError: If the webhook data is malformed
        """
        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']

            if 'messages' in value:
                message = value['messages'][0]
                self._handle_incoming_message(message)

        except (KeyError, IndexError) as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            raise

    def _handle_incoming_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming messages from WhatsApp.
        
        Args:
            message: Message data from webhook
        """
        try:
            if 'text' in message:
                from_number = message['from']
                message_body = message['text']['body']
            elif 'button' in message:
                from_number = message['from']
                message_body = message['button']['payload']
            else:
                logger.warning(f"Unsupported message format received: {message}")
                return

            # Import here to avoid circular imports
            from care_im.messaging.handler import WhatsAppMessageHandler
            
            handler = WhatsAppMessageHandler(from_number)
            handler.process_message(message_body)
            return "Message processed successfully"
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            # Try to send an error message back to the user
            if 'from' in message:
                self.send_message(
                    message['from'],
                    "Sorry, I couldn't process your request. Please try again later."
                )