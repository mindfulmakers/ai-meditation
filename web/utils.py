from __future__ import annotations

import os
import subprocess
from functools import wraps
from textwrap import dedent

import django


def dedent_strip(text):
    """
    Dedent and strip a multi-line string.
    """
    return dedent(text).strip()


def dedent_strip_format(text, **kwargs):
    """
    Dedent and strip a multi-line string, then format it with the given kwargs.
    """
    return dedent(text).strip().format(**kwargs)


def truncate_strings_in_json_data(json_data, n=100):
    """
    Truncate all strings in a JSON object to a maximum length of n characters.
    """
    if isinstance(json_data, str):
        return json_data[:n]
    if isinstance(json_data, list):
        return [truncate_strings_in_json_data(item, n) for item in json_data]
    if isinstance(json_data, dict):
        return {
            key: truncate_strings_in_json_data(value, n)
            for key, value in json_data.items()
        }
    return json_data


def clean_generated_python_code(python_code: str) -> str:
    """
    Clean up generated Python code by removing markdown formatting.
    """
    python_code = python_code.strip()
    python_code = python_code.removeprefix("```python")
    python_code = python_code.removeprefix("```")
    python_code = python_code.removesuffix("```")

    return python_code.strip()


def remove_triple_quotes(text: str) -> str:
    """
    Remove triple quotes from a string.
    """
    if text.startswith("'''") and text.endswith("'''"):
        return text[3:-3].strip()
    return text


def django_orm(func):
    """
    Decorator to ensure that the Django ORM is available to the function.
    Models must be imported locally within the function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Set up Django settings (adjust the path as needed)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        django.setup()

        # Execute the function
        func(*args, **kwargs)

    return wrapper


def copy_osx(text: str) -> None:
    """
    Copy text to the clipboard on macOS.
    """
    subprocess.run(["pbcopy"], check=False, text=True, input=text)
