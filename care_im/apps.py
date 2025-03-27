"""Care Instant Messaging app configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "care_im"


class CareIMConfig(AppConfig):
    """Configuration for the Care Instant Messaging app."""
    
    name = PLUGIN_NAME
    verbose_name = _("Care Instant Messaging")
    
    def ready(self):
        """Initialize app when Django starts."""
        import care_im.signals
