"""Shared response envelopes and helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

SYNTHETIC_DISCLAIMER = (
    "All values are synthetic demonstration data. Not live government land records."
)


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


class Meta(BaseModel):
    model_config = ConfigDict(extra="allow")

    page: int | None = None
    page_size: int | None = None
    total: int | None = None
    data_source: str = "SYNTHETIC"
    disclaimer: str = SYNTHETIC_DISCLAIMER


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: Meta = Field(default_factory=Meta)


def envelope(data: Any, **meta: Any) -> dict[str, Any]:
    payload = {
        "data_source": "SYNTHETIC",
        "disclaimer": SYNTHETIC_DISCLAIMER,
    }
    payload.update({k: v for k, v in meta.items() if v is not None})
    return {"data": data, "meta": payload}


def clamp_page(page: int, page_size: int) -> tuple[int, int]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    return page, page_size
