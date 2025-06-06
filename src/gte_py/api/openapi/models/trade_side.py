"""
GTE API

API for GTE trading and historical data

The version of the OpenAPI document: 0.1.0
Contact: support@liquidlabs.inc
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""

from __future__ import annotations

import json
from enum import Enum
from typing_extensions import Self


class TradeSide(str, Enum):
    """
    Side of the trade
    """

    """
    allowed enum values
    """
    BUY = "buy"
    SELL = "sell"

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of TradeSide from a JSON string"""
        return cls(json.loads(json_str))
