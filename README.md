# Care Instant Messaging wrapper (care_im)

Care IM (Instant Messaging) is a WhatsApp integration plugin for Care, providing a seamless messaging interface through WhatsApp Business API. This plugin enables healthcare facilities to communicate with patients via WhatsApp, supporting automated notifications and interactive messaging.

Key Features:
- WhatsApp Business API integration
- Automated patient notifications
- Two-way messaging support
- Secure message handling
- Configurable message templates


## Local Development

To develop the plug in local environment along with care, follow the steps below:

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

The following configurations variables are available for Care Hello:

- `HELLO_DUMMY_ENV`: Dummy environment variable for testing

The plugin will try to find the API key from the config first and then from the environment variable.

## License

This project is licensed under the terms of the [MIT license](LICENSE).

---

This plugin was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) using the [ohcnetwork/care-plugin-cookiecutter](https://github.com/ohcnetwork/care-plugin-cookiecutter).
