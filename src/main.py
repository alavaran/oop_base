from abc import ABC, abstractmethod
import uuid
from enum import Enum


class AbstractAccount(ABC):
    def __init__(self, UUID, firts_last_name, balance, status, type_account, currency):
        self.UUID = UUID  # Уникальный идентификатор клиента
        self.firts_last_name = firts_last_name  # Данные клиента
        self._balance = balance  # Баланс счета
        self.status = status  # Статус счета
        self.type_account = type_account  # Тип аккаунта
        self.currency = currency

    def generate_uuid_by_mask():
        return str(uuid.uuid4())

    @abstractmethod
    def deposit(self, amount):  # Пополнение
        pass

    @abstractmethod
    def withdraw(self, amount):  # Снятие
        pass

    @abstractmethod
    def get_account_info(self):  # Инфо об аккаунте
        pass


class AllowedCurrencys:
    ALLOWED_VALUES = ["RUB", "USD", "EUR", "KZT", "CNY"]


class BankAccountTypes:
    ALLOWED_TYPES = ["UL", "FL"]


class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class InvalidOperationError(Exception):
    def __init__(self, message="Wrong operation"):
        self.message = message
        super().__init__(self.message)


class InsufficientFundsError(Exception):
    def __init__(self, message="Insufficient funds"):
        self.message = message
        super().__init__(self.message)


class AccountClosedError(Exception):
    def __init__(self, message="Account closed"):
        self.message = message
        super().__init__(self.message)


class AccountFrozenError(Exception):
    def __init__(self, message="Account frozen"):
        self.message = message
        super().__init__(self.message)


class BankAccount(AbstractAccount):
    def __init__(
        self,
        type_account=None,
        UUID=None,
        firts_last_name=None,
        balance=0,
        status=AccountStatus.ACTIVE,
        currency=None,
    ):
        if UUID is None:
            UUID = AbstractAccount.generate_uuid_by_mask()

        if balance < 0:
            raise InsufficientFundsError("Balance must be positive")

        if currency not in AllowedCurrencys.ALLOWED_VALUES:
            raise ValueError(
                f"Значение должно быть одним из {AllowedCurrencys.ALLOWED_VALUES}"
            )

        if type_account not in BankAccountTypes.ALLOWED_TYPES:
            raise ValueError(
                f"Значение должно быть одним из {BankAccountTypes.ALLOWED_TYPES}"
            )

        super().__init__(UUID, firts_last_name, balance, status, type_account, currency)

    def deposit(self, amount):
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError("Wrong input amount")
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Account frozen, can't deposit")
        if self.status == AccountStatus.CLOSED:
            raise AccountFrozenError("Account closed, can't deposit")
        self._balance += amount
        print("Внесено:", amount)
        print("На счету:", self._balance)

    def withdraw(self, amount):
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError("Wrong input amount")
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Account frozen, can't withdraw")
        if self.status == AccountStatus.CLOSED:
            raise AccountFrozenError("Account closed, can't withdraw")
        if self._balance < amount:
            raise InsufficientFundsError("Malo sredst")
        self._balance -= amount
        print("Cнято:", amount)
        print("На счету:", self._balance)

    def get_account_info(self, balance):
        pass

    def __str__(self):
        return (
            f"{'=' * 20}\n"
            f"Счет {self.UUID}\n"
            f"Владелец: {self.firts_last_name}\n"
            f"Валюта: {self.currency}\n"
            f"Баланс: {self._balance}\n"
            f"Статус: {self.status.value}\n"
            f"{'=' * 20}"
        )
