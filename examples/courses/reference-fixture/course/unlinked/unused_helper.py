"""Unlinked reference fixture support file.

This file proves that unlinked source support is not copied into reference
artifact storage.
"""


def unused_value() -> str:
    return "not copied"
