"""WhatsApp template message sender implementation."""

import logging
import requests
from typing import Dict, Any, Optional, List

from care_im.core.config import plugin_settings

logger = logging.getLogger(__name__)


class WhatsAppSender:
    """
    Class for sending WhatsApp template messages using the WhatsApp Business API.
    
    Provides functionality to send template messages with parameters and regular text messages.
    """

    def __init__(self):
        """Initialize the WhatsApp sender with configuration from settings."""
        self.access_token = plugin_settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = plugin_settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = plugin_settings.WHATSAPP_API_VERSION
        self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def send_template(self, to_number: str, template_name: str, language: str = "en",
                      params: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, Any]:
        """
        Send a WhatsApp template message.

        Args:
            to_number: Recipient's phone number with country code (e.g., "911234567890")
            template_name: Name of the template to send
            language: Language code for the template
            params: Parameters to pass to the template, organized by component type
                   Example: {'body': [{'type': 'text', 'text': 'Hello'}]}

        Returns:
            API response as dictionary
        """
        logger.info(f"Sending WhatsApp template to {to_number} - {template_name}")

        # Basic payload for template message
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                }
            }
        }

        # Add components/parameters if provided
        if params:
            components = []
            for component_type, values in params.items():
                if component_type.lower() == "button":
                    # Create a separate component for each button
                    for button in values:
                        # Extract optional keys for button, defaulting if not provided
                        sub_type = button.pop("sub_type", "url")
                        index = button.pop("index", 0)
                        component = {
                            "type": "button",
                            "sub_type": sub_type,
                            "index": index,
                            "parameters": [button]
                        }
                        components.append(component)
                else:
                    # For other types like "body", group all provided parameters in one component
                    component = {
                        "type": component_type,
                        "parameters": values
                    }
                    components.append(component)
                    
            if components:
                payload["template"]["components"] = components

        try:
            logger.info(f"Sending WhatsApp template with payload: {payload}")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp template: {e}")
            return {"error": str(e)}

    def send_text_message(self, to_number: str, text: str) -> Dict[str, Any]:
        """
        Send a regular text message using WhatsApp API.

        Args:
            to_number: Recipient's phone number with country code
            text: Message text to send

        Returns:
            API response as dictionary
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return {"error": str(e)}