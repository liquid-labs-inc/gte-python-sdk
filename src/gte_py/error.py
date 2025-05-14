"""
Custom exceptions for GTE protocol error codes.
"""

from typing import Optional


class GTEError(Exception):
    """Base exception class for all GTE protocol errors."""

    error_code: str = ""

    def __init__(self, message: Optional[str] = None):
        self.message = message or self.__class__.__doc__
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__} ({self.error_code}): {self.message}"


class InsufficientBalance(GTEError):
    """Insufficient balance for the requested operation."""

    error_code = "0xf4d678b8"


class NotFactory(GTEError):
    """Operation can only be performed by the factory."""

    error_code = "0x32cc7236"


class FOKNotFilled(GTEError):
    """Fill-or-kill order could not be completely filled."""

    error_code = "0x87e393a7"


class UnauthorizedAmend(GTEError):
    """Unauthorized attempt to amend an order."""

    error_code = "0x60ab4840"


class UnauthorizedCancel(GTEError):
    """Unauthorized attempt to cancel an order."""

    error_code = "0x45bb6073"


class InvalidAmend(GTEError):
    """Invalid amendment to an order."""

    error_code = "0x4b22649a"


class OrderAlreadyExpired(GTEError):
    """The order has already expired."""

    error_code = "0x3154078e"


class InvalidAccountOrOperator(GTEError):
    """Invalid account or operator for the requested operation."""

    error_code = "0x3d104567"


class PostOnlyOrderWouldBeFilled(GTEError):
    """Post-only order would be immediately filled."""

    error_code = "0x52409ba3"


class MaxOrdersInBookPostNotCompetitive(GTEError):
    """Maximum orders in book reached and post is not competitive."""

    error_code = "0x315ff5e5"


class NonPostOnlyAmend(GTEError):
    """Non-post-only amendment is not allowed."""

    error_code = "0xc1008f10"


class ZeroCostTrade(GTEError):
    """Trade with zero cost is not allowed."""

    error_code = "0xd8a00083"


class ZeroTrade(GTEError):
    """Trade with zero quantity is not allowed."""

    error_code = "0x4ef36a18"


class ZeroOrder(GTEError):
    """Order with zero quantity is not allowed."""

    error_code = "0xb82df155"


class TransferFromFailed(GTEError):
    """Transfer from operation failed."""

    error_code = "0x7939f424"
