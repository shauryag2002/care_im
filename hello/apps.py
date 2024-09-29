from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "hello"


class HelloConfig(AppConfig):
    name = PLUGIN_NAME
    verbose_name = _("Hello")
