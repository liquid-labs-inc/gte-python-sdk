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
import pprint
from typing import Any
from typing_extensions import Self

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from gte_py.api.openapi.models.token import Token
from gte_py.api.openapi.models.token_metadata import TokenMetadata

GETTOKENLISTRESPONSEINNER_ONE_OF_SCHEMAS = ["Token", "TokenMetadata"]


class GetTokenListResponseInner(BaseModel):
    """
    GetTokenListResponseInner
    """

    # data type: Token
    oneof_schema_1_validator: Token | None = None
    # data type: TokenMetadata
    oneof_schema_2_validator: TokenMetadata | None = None
    actual_instance: Token | TokenMetadata | None = None
    one_of_schemas: set[str] = {"Token", "TokenMetadata"}

    model_config = ConfigDict(
        validate_assignment=True,
        protected_namespaces=(),
    )

    def __init__(self, *args, **kwargs) -> None:
        if args:
            if len(args) > 1:
                raise ValueError(
                    "If a position argument is used, only 1 is allowed to set `actual_instance`"
                )
            if kwargs:
                raise ValueError(
                    "If a position argument is used, keyword arguments cannot be used."
                )
            super().__init__(actual_instance=args[0])
        else:
            super().__init__(**kwargs)

    @field_validator("actual_instance")
    def actual_instance_must_validate_oneof(cls, v):
        instance = GetTokenListResponseInner.model_construct()
        error_messages = []
        match = 0
        # validate data type: Token
        if not isinstance(v, Token):
            error_messages.append(f"Error! Input type `{type(v)}` is not `Token`")
        else:
            match += 1
        # validate data type: TokenMetadata
        if not isinstance(v, TokenMetadata):
            error_messages.append(f"Error! Input type `{type(v)}` is not `TokenMetadata`")
        else:
            match += 1
        if match > 1:
            # more than 1 match
            raise ValueError(
                "Multiple matches found when setting `actual_instance` in GetTokenListResponseInner with oneOf schemas: Token, TokenMetadata. Details: "
                + ", ".join(error_messages)
            )
        elif match == 0:
            # no match
            raise ValueError(
                "No match found when setting `actual_instance` in GetTokenListResponseInner with oneOf schemas: Token, TokenMetadata. Details: "
                + ", ".join(error_messages)
            )
        else:
            return v

    @classmethod
    def from_dict(cls, obj: str | dict[str, Any]) -> Self:
        return cls.from_json(json.dumps(obj))

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Returns the object represented by the json string"""
        instance = cls.model_construct()
        error_messages = []
        match = 0

        # deserialize data into Token
        try:
            instance.actual_instance = Token.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into TokenMetadata
        try:
            instance.actual_instance = TokenMetadata.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))

        if match > 1:
            # more than 1 match
            raise ValueError(
                "Multiple matches found when deserializing the JSON string into GetTokenListResponseInner with oneOf schemas: Token, TokenMetadata. Details: "
                + ", ".join(error_messages)
            )
        elif match == 0:
            # no match
            raise ValueError(
                "No match found when deserializing the JSON string into GetTokenListResponseInner with oneOf schemas: Token, TokenMetadata. Details: "
                + ", ".join(error_messages)
            )
        else:
            return instance

    def to_json(self) -> str:
        """Returns the JSON representation of the actual instance"""
        if self.actual_instance is None:
            return "null"

        if hasattr(self.actual_instance, "to_json") and callable(self.actual_instance.to_json):
            return self.actual_instance.to_json()
        else:
            return json.dumps(self.actual_instance)

    def to_dict(self) -> dict[str, Any] | Token | TokenMetadata | None:
        """Returns the dict representation of the actual instance"""
        if self.actual_instance is None:
            return None

        if hasattr(self.actual_instance, "to_dict") and callable(self.actual_instance.to_dict):
            return self.actual_instance.to_dict()
        else:
            # primitive type
            return self.actual_instance

    def to_str(self) -> str:
        """Returns the string representation of the actual instance"""
        return pprint.pformat(self.model_dump())
