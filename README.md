# Care Instant Messaging wrapper (care_im)

Care IM (Instant Messaging) is a WhatsApp integration plugin for Care, providing a seamless messaging interface through WhatsApp Business API. This plugin enables healthcare facilities to communicate with patients via WhatsApp, supporting automated notifications and interactive messaging.

## Key Features

- WhatsApp Business API integration
- Automated patient notifications
- Two-way messaging support
- Secure message handling
- Configurable message templates
- Modular architecture for easy extension

## Architecture

The plugin is structured in a modular way for better maintainability and extensibility:

- **Core**: Configuration and essential utilities
- **Messaging**: WhatsApp client, template sending, and message handling
- **Templates**: Message templates and formatting logic
- **Handlers**: Specialized handlers for different message types
- **API**: REST API endpoints for webhook integration
- **Signals**: Django signal handlers for event-driven messaging

## Usage Examples

### Sending a WhatsApp message

```python
from care_im.messaging.client import WhatsAppClient

client = WhatsAppClient()
client.send_message("+919876543210", "Hello from Care IM!")
```

### Sending a template message

```python
from care_im.messaging.template_sender import WhatsAppSender

sender = WhatsAppSender()
sender.send_template(
    "+919876543210", 
    "care_appointment_reminder",
    params={
        "body": [
            {"type": "text", "text": "Dr. Smith"},
            {"type": "text", "text": "March 30, 2025"},
            {"type": "text", "text": "10:30 AM"}
        ]
    }
)
```

### Processing an incoming message

```python
from care_im.messaging.handler import WhatsAppMessageHandler

handler = WhatsAppMessageHandler("+919876543210")
response = handler.process_message("medications")
```

## Local Development

To develop the plugin in a local environment along with care, follow the steps below:

1. Go to the care root directory and clone the plugin repository:

```bash
cd care
git clone git@github.com:shauryag2002/care_im.git
```

2. Add the plugin config in plug_config.py

```python
...

im_plugin = Plug(
    name="care_im", # name of the django app in the plugin
    package_name="/app/care_im", # this has to be /app/ + plugin folder name
    version="", # keep it empty for local development
    configs={}, # plugin configurations if any
)
plugs = [im_plugin]

...
```

3. Tweak the code in plugs/manager.py, install the plugin in editable mode

```python
...

subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-e", *packages] # add -e flag to install in editable mode
)

...
```

4. Rebuild the docker image and run the server

```bash
make re-build
make up
```

> [!IMPORTANT]
> Do not push these changes in a PR. These changes are only for local development.

## Production Setup

To install care care_im, you can add the plugin config in [care/plug_config.py](https://github.com/ohcnetwork/care/blob/develop/plug_config.py) as follows:

```python
...

im_plug = Plug(
    name="care_im",
    package_name="git+https://github.com/ohcnetwork/care_im.git",
    version="@master",
    configs={},
)
plugs = [im_plug]
...
```

[Extended Docs on Plug Installation](https://care-be-docs.ohc.network/pluggable-apps/configuration.html)

## Configuration

The following configuration variables are required for Care IM:

- `WHATSAPP_ACCESS_TOKEN`: WhatsApp Business API access token
- `WHATSAPP_PHONE_NUMBER_ID`: Your WhatsApp phone number ID
- `WHATSAPP_VERIFY_TOKEN`: Token for webhook verification
- `WHATSAPP_API_VERSION`: WhatsApp API version to use (default: v22.0)
- `WHATSAPP_BUSINESS_ACCOUNT_ID`: Your WhatsApp Business Account ID

## Extending the Plugin

To add a new message handler:

1. Create a new handler class that extends `BaseHandler` in `messaging/handlers/`
2. Implement your handler logic
3. Integrate it with the main `WhatsAppMessageHandler` class

## License

This project is licensed under the terms of the [MIT license](LICENSE).

---

This plugin was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) using the [ohcnetwork/care-plugin-cookiecutter](https://github.com/ohcnetwork/care-plugin-cookiecutter).
