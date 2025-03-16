

import requests
import logging
from typing import Dict, Any, Optional
from care_im.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppSender:
    """
    Class for sending WhatsApp messages using the WhatsApp Business API
    """

    def __init__(self):
        """
        Initialize the WhatsApp sender
        """
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_url = f"https://graph.facebook.com/v22.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    def send_template(self, to_number: str, template_name: str, language: str = "en",
                      params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a WhatsApp template message

        Args:
            to_number: Recipient's phone number with country code (e.g. "911234567890")
            template_name: Name of the template to send
            language: Language code for the template
            params: Parameters to pass to the template (if any)

        Returns:
            API response as dictionary
        """
        logger.info(f"Sending WhatsApp template to {to_number} - {template_name}")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

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
            for param_type, values in params.items():
                component = {"type": param_type, "parameters": []}
                for value in values:
                    component["parameters"].append(value)
                components.append(component)

            if components:
                payload["template"]["components"] = components

        try:
            logger.info(f"Sendy WhatsApp template: {payload}")
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp template: {e}")
            return {"error": str(e)}

    def send_text_message(self, to_number: str, text: str) -> Dict[str, Any]:
        """
        Send a regular text message using WhatsApp API

        Args:
            to_number: Recipient's phone number with country code
            text: Message text to send

        Returns:
            API response as dictionary
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

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
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return {"error": str(e)}
