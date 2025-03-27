#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "requests>=2.25.0",
    "celery>=5.0.0",
    "django>=3.2.0",
    "djangorestframework>=3.12.0",
    "django-environ>=0.8.0",
    "django-filter>=2.4.0",
    "jsonschema>=4.0.0",
    "drf-spectacular>=0.22.0",
]

test_requirements = [
    "pytest>=6.0.0",
    "pytest-django>=4.4.0",
    "factory-boy>=3.2.0",
]

setup(
    author="Open Healthcare Network",
    author_email="info@ohc.network",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="WhatsApp integration plugin for Care to enable messaging capabilities",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="care_im,whatsapp,messaging,healthcare",
    name="care_im",
    packages=find_packages(include=["care_im", "care_im.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ohcnetwork/care_im",
    version="0.2.0",
    zip_safe=False,
)
