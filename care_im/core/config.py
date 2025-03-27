"""Configuration management for care_im."""

from typing import Any, Dict, Set

import environ
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import setting_changed
from django.dispatch import receiver
from rest_framework.settings import perform_import

from care_im.apps import PLUGIN_NAME

env = environ.Env()


class PluginSettings:
    """
    A settings object that allows plugin settings to be accessed as properties.
    
    Example:
        from care_im.core.config import plugin_settings
        print(plugin_settings.WHATSAPP_ACCESS_TOKEN)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(
        self,
        plugin_name: str = None,
        defaults: Dict[str, Any] | None = None,
        import_strings: Set[str] | None = None,
        required_settings: Set[str] | None = None,
    ) -> None:
        if not plugin_name:
            raise ValueError("Plugin name must be provided")
        self.plugin_name = plugin_name
        self.defaults = defaults or {}
        self.import_strings = import_strings or set()
        self.required_settings = required_settings or set()
        self._cached_attrs = set()
        self.validate()

    def __getattr__(self, attr) -> Any:
        if attr not in self.defaults:
            raise AttributeError(f"Invalid setting: '{attr}'")

        # Try to find the setting from user settings, then from environment variables
        val = self.defaults[attr]
        try:
            val = self.user_settings[attr]
        except KeyError:
            try:
                val = env(attr, cast=type(val))
            except environ.ImproperlyConfigured:
                # Fall back to defaults
                pass

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    @property
    def user_settings(self) -> Dict[str, Any]:
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "PLUGIN_CONFIGS", {}).get(
                self.plugin_name, {}
            )
        return self._user_settings

    def validate(self) -> None:
        """
        Validate the plugin settings.
        
        Checks if all required settings are provided and non-empty.
        """
        for setting in self.required_settings:
            if not getattr(self, setting):
                raise ImproperlyConfigured(
                    f'The "{setting}" setting is required. '
                    f'Please set the "{setting}" in the environment or the {PLUGIN_NAME} plugin config.'
                )

    def reload(self) -> None:
        """
        Reset cached attributes so they will be recalculated on next access.
        """
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


# WhatsApp settings definition
REQUIRED_SETTINGS = {
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_VERIFY_TOKEN",
    "WHATSAPP_API_VERSION",
    "WHATSAPP_BUSINESS_ACCOUNT_ID",
}

DEFAULTS = {
    "WHATSAPP_ACCESS_TOKEN": "",
    "WHATSAPP_PHONE_NUMBER_ID": "",
    "WHATSAPP_VERIFY_TOKEN": "123456",
    "WHATSAPP_API_VERSION": "v22.0",
    "WHATSAPP_BUSINESS_ACCOUNT_ID": "",
}

# Create plugin settings instance
plugin_settings = PluginSettings(
    PLUGIN_NAME, defaults=DEFAULTS, required_settings=REQUIRED_SETTINGS
)


@receiver(setting_changed)
def reload_plugin_settings(*args, **kwargs) -> None:
    """Signal handler to reload settings when they change."""
    setting = kwargs["setting"]
    if setting == "PLUGIN_CONFIGS":
        plugin_settings.reload()