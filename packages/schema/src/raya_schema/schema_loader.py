from __future__ import annotations

import json
from importlib import resources
from typing import Any

from jsonschema import Draft202012Validator


def load_schema(name: str) -> dict[str, Any]:
    schema_file = resources.files("raya_schema.schemas").joinpath(name)
    with schema_file.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise TypeError(f"Schema {name} did not load as an object")
    return loaded


def validator_for(name: str) -> Draft202012Validator:
    return Draft202012Validator(load_schema(name))
