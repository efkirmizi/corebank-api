"""Shared marshmallow field helpers."""
from __future__ import annotations

from marshmallow import fields


def money(**kwargs) -> fields.Decimal:
    """Currency as a fixed-2-place decimal, serialized as a string so no value
    ever passes through a float."""
    return fields.Decimal(places=2, as_string=True, **kwargs)
