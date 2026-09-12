from transactions import (
    Transaction
)
from currency import (
    CurrencyConverter
)
from enums import (
    Currency,
    TransactionType,
    TransactionPriority,
)
from utils import (
    UUIDGenerator
)
from fees import (
    FeeCalculator
)
# ============ Transaction Factory ============
class TransactionFactory:
    """Фабрика для создания транзакций"""

    @staticmethod
    def create_deposit(
        receiver_account_id: str,
        amount: float,
        currency: Currency,
        priority: TransactionPriority = TransactionPriority.NORMAL,
    ) -> Transaction:
        """Создать транзакцию пополнения"""
        return Transaction(
            transaction_id=UUIDGenerator.generate()[:8],
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            currency=currency,
            receiver_account_id=receiver_account_id,
            priority=priority,
        )

    @staticmethod
    def create_transfer(
        sender_account_id: str,
        receiver_account_id: str,
        amount: float,
        currency: Currency,
        priority: TransactionPriority = TransactionPriority.NORMAL,
    ) -> Transaction:
        """Создать транзакцию перевода"""
        fee = FeeCalculator.calculate_fee(TransactionType.TRANSFER, amount, currency)

        return Transaction(
            transaction_id=UUIDGenerator.generate()[:8],
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            currency=currency,
            sender_account_id=sender_account_id,
            receiver_account_id=receiver_account_id,
            fee=fee,
            priority=priority,
        )

    @staticmethod
    def create_external_transfer(
        sender_account_id: str,
        amount: float,
        currency: Currency,
        priority: TransactionPriority = TransactionPriority.NORMAL,
    ) -> Transaction:
        """Создать внешний перевод"""
        fee = FeeCalculator.calculate_fee(
            TransactionType.EXTERNAL_TRANSFER, amount, currency
        )

        return Transaction(
            transaction_id=UUIDGenerator.generate()[:8],
            transaction_type=TransactionType.EXTERNAL_TRANSFER,
            amount=amount,
            currency=currency,
            sender_account_id=sender_account_id,
            fee=fee,
            priority=priority,
        )