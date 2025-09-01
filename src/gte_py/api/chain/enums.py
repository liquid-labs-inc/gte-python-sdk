# Enums
class BookType(IntEnum):
    STANDARD = 0
    BACKSTOP = 1

class CancelType(IntEnum):
    USER = 0
    EXPIRY = 1
    NON_COMPETITIVE = 2

class FeeTier(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2

class FeeTiers(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2

class FillOrderType(IntEnum):
    MARKET = 0
    LIMIT = 1

class LimitOrderType(IntEnum):
    GOOD_TILL_CANCELLED = 0
    POST_ONLY = 1

class LiquidationType(IntEnum):
    LIQUIDATEE = 0
    BACKSTOP_LIQUIDATEE = 1
    DELIST = 2
    DELEVERAGE_MAKER = 3
    DELEVERAGE_TAKER = 4

class Settlement(IntEnum):
    INSTANT = 0
    ACCOUNT = 1

class Side(IntEnum):
    BUY = 0
    SELL = 1

class Status(IntEnum):
    NULL = 0
    INACTIVE = 1
    ACTIVE = 2
    DELISTED = 3

class TiF(IntEnum):
    GTC = 0
    MOC = 1
    FOK = 2
    IOC = 3