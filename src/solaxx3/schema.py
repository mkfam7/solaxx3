"""Schema validation for the register catalog JSON file.

Deliberately dependency-free (no ``jsonschema`` package) — the catalog only
needs a handful of keywords, and hand-rolling them keeps validation working
in minimal environments without an extra install. The schema below is
written in real JSON Schema shape (``type``/``properties``/``required``/
``enum``/``minimum``/``additionalProperties``), so swapping in the real
``jsonschema`` library later is a drop-in change if the schema ever needs
keywords this validator doesn't support.

Validating at load time means a typo or bad edit in ``registers.json``
fails loudly and specifically (naming the register and field) at import
time, instead of surfacing later as a confusing ``KeyError`` or ``TypeError``
deep inside decoding.
"""

from __future__ import annotations

from typing import Any

REGISTER_ENTRY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "address",
        "register_type",
        "data_format",
        "si_adj",
        "signed",
        "data_unit",
        "data_length",
        "description",
    ],
    "properties": {
        "address": {"type": "integer", "minimum": 0},
        "register_type": {"type": "string", "enum": ["input", "holding"]},
        "data_format": {
            "type": "string",
            "enum": ["uint16", "int16", "uint32", "int32", "varchar", "datetime"],
        },
        "si_adj": {"type": "number"},
        "signed": {"type": "boolean"},
        "data_unit": {"type": "string"},
        "data_length": {"type": "integer", "minimum": 1},
        "description": {"type": "string"},
        # optional sanity bounds for decoded numeric values
        "min_value": {"type": "number"},
        "max_value": {"type": "number"},
    },
    "additionalProperties": False,
}


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        # bool is a subclass of int in Python; exclude it explicitly.
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    raise ValueError(f"Unsupported schema type: {expected!r}")


def _validate_instance(instance: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type and not _type_matches(instance, expected_type):
        errors.append(
            f"{path}: expected type '{expected_type}', got "
            f"'{type(instance).__name__}' ({instance!r})"
        )
        return errors  # further structural checks would be meaningless

    if expected_type == "object":
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required field '{key}'")

        properties = schema.get("properties", {})
        if not schema.get("additionalProperties", True):
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}: unexpected field '{key}'")

        for key, sub_schema in properties.items():
            if key in instance:
                errors.extend(
                    _validate_instance(instance[key], sub_schema, f"{path}.{key}")
                )
        return errors

    enum = schema.get("enum")
    if enum is not None and instance not in enum:
        errors.append(f"{path}: {instance!r} is not one of {enum}")

    minimum = schema.get("minimum")
    if minimum is not None and instance < minimum:
        errors.append(f"{path}: {instance} is below minimum {minimum}")

    return errors


def validate_catalog(raw: Any) -> list[str]:
    """Validate a raw (just-parsed-from-JSON) register catalog.

    Returns a list of human-readable error strings — empty if the catalog
    is valid. Every entry is checked, and all errors are collected, rather
    than stopping at the first problem.
    """

    if not isinstance(raw, dict):
        return [
            (
                "<root>: expected an object mapping register name -> "
                f"definition, got '{type(raw).__name__}'"
            )
        ]

    errors: list[str] = []
    for name, entry in raw.items():
        errors.extend(_validate_instance(entry, REGISTER_ENTRY_SCHEMA, name))

        # cross-field check that plain per-field validation can't express
        if isinstance(entry, dict):
            min_value = entry.get("min_value")
            max_value = entry.get("max_value")
            if (
                isinstance(min_value, (int, float))
                and isinstance(max_value, (int, float))
                and min_value > max_value
            ):
                errors.append(
                    f"{name}: min_value ({min_value}) is greater than "
                    f"max_value ({max_value})"
                )

    return errors
