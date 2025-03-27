"""
Backward compatibility module for WhatsAppSender.

This module provides backward compatibility for code that imports
WhatsAppSender from the old location.

For new code, import from care_im.messaging.template_sender instead.
"""

import warnings
from care_im.messaging.template_sender import WhatsAppSender as ModernWhatsAppSender

class WhatsAppSender(ModernWhatsAppSender):
    """
    Backward compatibility wrapper for WhatsAppSender.
    
    This class inherits from the new WhatsAppSender for backward compatibility.
    """
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Importing WhatsAppSender from care_im.utils.send_message_templates is deprecated. "
            "Please import from care_im.messaging.template_sender instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
