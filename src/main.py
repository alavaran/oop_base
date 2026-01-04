from abc import ABC, abstractmethod
import uuid
from enum import Enum
from typing import Protocol
import logging


# ============ Enums ============
class Currency(Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class AccountType(Enum):
    LEGAL = "UL"  # Юридическое лицо
    INDIVIDUAL = "FL"  # Физическое лицо


class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


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


# ============ Protocols (Interface Segregation) ============
class Depositable(Protocol):
    """Интерфейс для операций пополнения"""

    def deposit(self, amount: float) -> None: ...


class Withdrawable(Protocol):
    """Интерфейс для операций снятия"""

    def withdraw(self, amount: float) -> None: ...


class AccountInfo(Protocol):
    """Интерфейс для получения информации"""

    def get_account_info(self) -> dict: ...


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


# ============ Logger Interface (Dependency Inversion) ============
class TransactionLogger(ABC):
    """Абстракция для логирования транзакций"""

    @abstractmethod
    def log_deposit(self, amount: float, balance: float) -> None:
        pass

    @abstractmethod
    def log_withdrawal(self, amount: float, balance: float) -> None:
        pass


class ConsoleLogger(TransactionLogger):
    """Логирование в консоль"""

    def log_deposit(self, amount: float, balance: float) -> None:
        print(f"Внесено: {amount}")
        print(f"На счету: {balance}")

    def log_withdrawal(self, amount: float, balance: float) -> None:
        print(f"Снято: {amount}")
        print(f"На счету: {balance}")


class FileLogger(TransactionLogger):
    """Логирование в файл"""

    def __init__(self, filename: str = "transactions.log"):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(filename)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_deposit(self, amount: float, balance: float) -> None:
        self.logger.info(f"Deposit: {amount}, New balance: {balance}")

    def log_withdrawal(self, amount: float, balance: float) -> None:
        self.logger.info(f"Withdrawal: {amount}, New balance: {balance}")


# ============ UUID Generator (Single Responsibility) ============
class UUIDGenerator:
    """Генерация уникальных идентификаторов"""

    @staticmethod
    def generate() -> str:
        return str(uuid.uuid4())


# ============ Abstract Account ============
class AbstractAccount(ABC):
    """Базовый абстрактный класс счета"""

    def __init__(
        self,
        account_uuid: str,
        first_last_name: str,
        balance: float,
        status: AccountStatus,
        account_type: AccountType,
        currency: Currency,
    ):
        self.account_uuid = account_uuid
        self.first_last_name = first_last_name
        self._balance = balance
        self.status = status
        self.account_type = account_type
        self.currency = currency

    @abstractmethod
    def deposit(self, amount: float) -> None:
        """Пополнение счета"""
        pass

    @abstractmethod
    def withdraw(self, amount: float) -> None:
        """Снятие со счета"""
        pass

    @abstractmethod
    def get_account_info(self) -> dict:
        """Получение информации о счете"""
        pass

    @property
    def balance(self) -> float:
        """Получение баланса"""
        return self._balance


# ============ Bank Account Implementation ============
class BankAccount(AbstractAccount):
    """Банковский счет с dependency injection"""

    def __init__(
        self,
        first_last_name: str,
        account_type: AccountType,
        currency: Currency,
        balance: float = 0,
        status: AccountStatus = AccountStatus.ACTIVE,
        account_uuid: str = None,
        logger: TransactionLogger = None,
    ):
        # Валидация при создании
        BalanceValidator.validate(balance)

        # Генерация UUID если не предоставлен
        if account_uuid is None:
            account_uuid = UUIDGenerator.generate()

        # Dependency Injection для логгера
        if logger is None:
            logger = ConsoleLogger()

        self._logger = logger

        super().__init__(
            account_uuid=account_uuid,
            first_last_name=first_last_name,
            balance=balance,
            status=status,
            account_type=account_type,
            currency=currency,
        )

    def deposit(self, amount: float) -> None:
        """Пополнение счета"""
        AmountValidator.validate(amount)
        AccountStatusValidator.validate_for_operation(self.status)

        self._balance += amount
        self._logger.log_deposit(amount, self._balance)

    def withdraw(self, amount: float) -> None:
        """Снятие со счета"""
        AmountValidator.validate(amount)
        AccountStatusValidator.validate_for_operation(self.status)

        if self._balance < amount:
            raise InsufficientFundsError("Insufficient funds for withdrawal")

        self._balance -= amount
        self._logger.log_withdrawal(amount, self._balance)

    def get_account_info(self) -> dict:
        """Получение информации о счете"""
        return {
            "uuid": self.account_uuid,
            "owner": self.first_last_name,
            "type": self.account_type.value,
            "currency": self.currency.value,
            "balance": self._balance,
            "status": self.status.value,
        }

    def __str__(self) -> str:
        return (
            f"{'=' * 20}\n"
            f"Счет {self.account_uuid}\n"
            f"Владелец: {self.first_last_name}\n"
            f"Тип: {self.account_type.value}\n"
            f"Валюта: {self.currency.value}\n"
            f"Баланс: {self._balance}\n"
            f"Статус: {self.status.value}\n"
            f"{'=' * 20}"
        )
