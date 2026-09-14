
from transactions import (
    Transaction
)
from bank import (
    Bank
)
from enums import (
    TransactionType,
    RiskLevel
)
from currency import (
    CurrencyConverter
)
from accounts import (
    PremiumAccount
)
from exceptions import (
    InsufficientFundsError,
    AccountFrozenError,
    AccountClosedError,
    InvalidOperationError,
)
from validators import (
    AccountStatusValidator
)
from risk import RiskAnalyzer
from audit import AuditLog, AuditEvent
# ============ Transaction Processor ============
class TransactionProcessor:
    """Обработчик транзакций с повторами и логированием"""

    def __init__(self, bank: "Bank", max_retries: int = 3):
        self.bank = bank
        self.max_retries = max_retries
        self.failed_transactions = []
        self.risk_analyzer = RiskAnalyzer(bank)
        self.audit_log = AuditLog()

    def process_transaction(self, transaction: Transaction) -> bool:
        if transaction.transaction_type == TransactionType.DEPOSIT:
            risk_level = RiskLevel.LOW
        else:
            risk_level = self.risk_analyzer.analyze(transaction)

        if risk_level == RiskLevel.HIGH:
            transaction.mark_failed("High risk transaction")

            self.audit_log.record(
                AuditEvent(
                    transaction_id=transaction.transaction_id,
                    risk_level=risk_level,
                    message=f"Risk level: {risk_level.value}",
                    failure_reason=transaction.failure_reason
                )
            )

            return False

        attempts = 0

        while attempts < self.max_retries:
            try:
                if transaction.transaction_type == TransactionType.DEPOSIT:
                    self._process_deposit(transaction)
                elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                    self._process_withdrawal(transaction)
                elif transaction.transaction_type == TransactionType.TRANSFER:
                    self._process_transfer(transaction)
                elif transaction.transaction_type == TransactionType.EXTERNAL_TRANSFER:
                    self._process_external_transfer(transaction)
                transaction.mark_completed()
                self.bank.record_transaction(transaction)
                print(f"✅ Транзакция {transaction.transaction_id} выполнена успешно")
                return True

            except (
                InsufficientFundsError,
                AccountFrozenError,
                AccountClosedError,
            ) as e:
                # Критические ошибки — не повторяем
                transaction.mark_failed(str(e))
                self.failed_transactions.append(transaction)
                print(f"❌ Транзакция {transaction.transaction_id} отклонена: {e}")
                return False

            except Exception as e:
                attempts += 1
                if attempts >= self.max_retries:
                    transaction.mark_failed(f"Max retries exceeded: {e}")
                    self.failed_transactions.append(transaction)
                    print(
                        f"❌ Транзакция {transaction.transaction_id} не выполнена после {attempts} попыток"
                    )
                    return False
                else:
                    print(
                        f"⚠️ Попытка {attempts}/{self.max_retries} для транзакции {transaction.transaction_id}"
                    )

        return False

    def _process_deposit(self, transaction: Transaction) -> None:
        """Обработать пополнение"""
        account = self.bank.accounts.get(transaction.receiver_account_id)
        if not account:
            raise InvalidOperationError("Account not found")

        account.deposit(transaction.amount)

    def _process_withdrawal(self, transaction: Transaction) -> None:
        """Обработать снятие"""
        account = self.bank.accounts.get(transaction.sender_account_id)
        if not account:
            raise InvalidOperationError("Account not found")

        AccountStatusValidator.validate_for_operation(account.status)
        account.withdraw(transaction.get_total_amount())  # С учётом комиссии

    def _process_transfer(self, transaction: Transaction) -> None:
        """Обработать внутренний перевод"""
        sender = self.bank.accounts.get(transaction.sender_account_id)
        receiver = self.bank.accounts.get(transaction.receiver_account_id)

        if not sender or not receiver:
            raise InvalidOperationError("One or both accounts not found")

        # Проверки
        AccountStatusValidator.validate_for_operation(sender.status)
        AccountStatusValidator.validate_for_operation(receiver.status)

        # Проверка баланса (кроме премиум с овердрафтом)
        if not isinstance(sender, PremiumAccount):
            if sender.balance < transaction.get_total_amount():
                raise InsufficientFundsError("Insufficient funds for transfer")

        # Конвертация валюты при необходимости
        if sender.currency != receiver.currency:
            converted_amount = CurrencyConverter.convert(
                transaction.amount, sender.currency, receiver.currency
            )
        else:
            converted_amount = transaction.amount

        # Выполнение перевода
        sender.withdraw(transaction.get_total_amount())
        receiver.deposit(converted_amount)

    def _process_external_transfer(self, transaction: Transaction) -> None:
        """Обработать внешний перевод"""
        sender = self.bank.accounts.get(transaction.sender_account_id)

        if not sender:
            raise InvalidOperationError("Sender account not found")

        AccountStatusValidator.validate_for_operation(sender.status)

        # Внешний перевод — только списание
        total = transaction.get_total_amount()
        if not isinstance(sender, PremiumAccount):
            if sender.balance < total:
                raise InsufficientFundsError("Insufficient funds for external transfer")

        sender.withdraw(total)

    def get_failed_transactions(self) -> list[Transaction]:
        """Получить список неудачных транзакций"""
        return self.failed_transactions
