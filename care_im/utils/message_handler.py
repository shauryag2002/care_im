"""
Backward compatibility module for WhatsAppMessageHandler.

This module provides backward compatibility for code that imports
WhatsAppMessageHandler from the old location.

For new code, import from care_im.messaging.handler instead.
"""

import warnings
from care_im.messaging.handler import WhatsAppMessageHandler as ModernWhatsAppMessageHandler

class WhatsAppMessageHandler(ModernWhatsAppMessageHandler):
    """
    Backward compatibility wrapper for WhatsAppMessageHandler.
    
    This class inherits from the new WhatsAppMessageHandler for backward compatibility.
    """
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Importing WhatsAppMessageHandler from care_im.utils.message_handler is deprecated. "
            "Please import from care_im.messaging.handler instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
