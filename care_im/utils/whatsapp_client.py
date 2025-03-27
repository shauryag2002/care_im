"""
Backward compatibility module for WhatsAppClient.

This module provides backward compatibility for code that imports
WhatsAppClient from the old location.

For new code, import from care_im.messaging.client instead.
"""

import warnings
from care_im.messaging.client import WhatsAppClient as ModernWhatsAppClient

class WhatsAppClient(ModernWhatsAppClient):
    """
    Backward compatibility wrapper for WhatsAppClient.
    
    This class inherits from the new WhatsAppClient for backward compatibility.
    """
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Importing WhatsAppClient from care_im.utils.whatsapp_client is deprecated. "
            "Please import from care_im.messaging.client instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
