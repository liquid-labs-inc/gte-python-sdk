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


class MarketType(str, Enum):
    """
    Type of the market
    """

    """
    allowed enum values
    """
    BONDING_MINUS_CURVE = "bonding-curve"
    AMM = "amm"
    CLOB_MINUS_SPOT = "clob-spot"
    PERPS = "perps"

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of MarketType from a JSON string"""
        return cls(json.loads(json_str))
