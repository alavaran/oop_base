# ============ Exceptions ============
class InvalidOperationError(Exception):
    """Исключение для неверных операций"""

    pass


class InsufficientFundsError(Exception):
    """Исключение для недостаточных средств"""

    pass


class AccountClosedError(Exception):
    """Исключение для закрытого счета"""

    pass


class AccountFrozenError(Exception):
    """Исключение для замороженного счета"""

    pass
