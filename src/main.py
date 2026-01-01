from abc import ABC, abstractmethod
import uuid
from enum import Enum


class AbstractAccount(ABC):
    def __init__(self, UUID, firts_last_name, balance, status):
        self.UUID = UUID  # Уникальный идентификатор клиента
        self.firts_last_name = firts_last_name  # Данные клиента
        self._balance = balance  # Баланс счета
        self.status = status  # Статус счета

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


class Currency(Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


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
        self, UUID=None, firts_last_name=None, balance=0, status=AccountStatus.ACTIVE
    ):
        if UUID is None:
            UUID = AbstractAccount.generate_uuid_by_mask()

        super().__init__(UUID, firts_last_name, balance, status)

    def deposit(self, amount):
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError("Wrong input amount")
        self._balance += amount
        print("Внесено:", amount)
        print("На счету:", self._balance)

    def withdraw(self, amount):
        pass

    def get_account_info(self, balance):
        pass


test_account = BankAccount(
    firts_last_name="Igor Igorevich",
    UUID=None,
    balance=1000,
    status=AccountStatus.ACTIVE,
)

try:
    test_account.deposit(1500)
except InvalidOperationError as e:
    print(e)

print(test_account.UUID)
