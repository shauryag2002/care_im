"""
Backward compatibility module for care_im settings.

For new code, import from care_im.core.config instead.
"""

from care_im.core.config import plugin_settings, DEFAULTS, REQUIRED_SETTINGS

# Make settings accessible from the old location for backward compatibility
PluginSettings = plugin_settings.__class__

# Re-export values for backward compatibility
WHATSAPP_ACCESS_TOKEN = plugin_settings.WHATSAPP_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID = plugin_settings.WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_VERIFY_TOKEN = plugin_settings.WHATSAPP_VERIFY_TOKEN
WHATSAPP_API_VERSION = plugin_settings.WHATSAPP_API_VERSION
WHATSAPP_BUSINESS_ACCOUNT_ID = plugin_settings.WHATSAPP_BUSINESS_ACCOUNT_ID
