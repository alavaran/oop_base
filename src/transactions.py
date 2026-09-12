from dataclasses import dataclass, field
from enums import (
    Currency,
    TransactionType,
    TransactionStatus,
    TransactionPriority,
)
from datetime import datetime
from typing import Optional
from exceptions import (
    InvalidOperationError,
)

@dataclass
class Transaction:
    """Модель транзакции с полной историей"""

    transaction_id: str
    transaction_type: TransactionType
    amount: float
    currency: Currency
    sender_account_id: Optional[str] = None
    receiver_account_id: Optional[str] = None
    fee: float = 0.0
    status: TransactionStatus = TransactionStatus.PENDING
    failure_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    priority: TransactionPriority = TransactionPriority.NORMAL

    def mark_completed(self) -> None:
        """Отметить транзакцию как успешную"""
        self.status = TransactionStatus.COMPLETED
        self.processed_at = datetime.now()

    def mark_failed(self, reason: str) -> None:
        """Отметить транзакцию как неудачную"""
        self.status = TransactionStatus.FAILED
        self.failure_reason = reason
        self.processed_at = datetime.now()

    def mark_cancelled(self) -> None:
        """Отменить транзакцию"""
        if self.status == TransactionStatus.PENDING:
            self.status = TransactionStatus.CANCELLED
            self.processed_at = datetime.now()
        else:
            raise InvalidOperationError("Cannot cancel non-pending transaction")

    def get_total_amount(self) -> float:
        """Сумма с комиссией"""
        return self.amount + self.fee

    def __lt__(self, other):
        """Сравнение для приоритетной очереди"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at