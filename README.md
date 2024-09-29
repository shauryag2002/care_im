# Care Hello

[![Release Status](https://img.shields.io/pypi/v/care_hello.svg)](https://pypi.python.org/pypi/care_hello)
[![Build Status](https://github.com/ohcnetwork/care_hello/actions/workflows/build.yaml/badge.svg)](https://github.com/ohcnetwork/care_hello/actions/workflows/build.yaml)

Care Hello is a plugin for care to add voice auto fill support using external services like OpenAI whisper and Google Speech to Text.

## Features

- Voice auto fill support for care
- Support for OpenAI whisper and Google Speech to Text

## Installation

https://care-be-docs.ohc.network/pluggable-apps/configuration.html

https://github.com/ohcnetwork/care/blob/develop/plug_config.py

To install care hello, you can add the plugin config in [care/plug_config.py](https://github.com/ohcnetwork/care/blob/develop/plug_config.py) as follows:

```python
...

hello_plug = Plug(
    name="hello",
    package_name="git+https://github.com/ohcnetwork/care_hello.git",
    version="@master",
    configs={},
)
plugs = [hello_plug]
...
```

## Configuration

The following configurations variables are available for Care Hello:

- `HELLO_DUMMY_ENV`: Dummy environment variable for testing

The plugin will try to find the API key from the config first and then from the environment variable.

## License

This project is licensed under the terms of the [MIT license](LICENSE).

---

This plugin was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) using the [ohcnetwork/care-plugin-cookiecutter](https://github.com/ohcnetwork/care-plugin-cookiecutter).
