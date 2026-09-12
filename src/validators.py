from exceptions import (
    InsufficientFundsError,
    AccountFrozenError,
    AccountClosedError,
    InvalidOperationError,
)

from enums import (
    AccountStatus
)

# ============ Validators (Single Responsibility) ============
class AmountValidator:
    """Валидация сумм операций"""

    @staticmethod
    def validate(amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError("Amount must be a number")
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")


class BalanceValidator:
    """Валидация баланса"""

    @staticmethod
    def validate(balance: float) -> None:
        if balance < 0:
            raise InsufficientFundsError("Balance cannot be negative")

class AccountStatusValidator:
    """Валидация статуса счета"""

    @staticmethod
    def validate_for_operation(status: AccountStatus) -> None:
        if status == AccountStatus.FROZEN:
            raise AccountFrozenError("Account is frozen")
        if status == AccountStatus.CLOSED:
            raise AccountClosedError("Account is closed")
