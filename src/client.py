from datetime import datetime
from utils import (
    UUIDGenerator
)

from enums import (
    AccountStatus
)

from exceptions import (
    AccountFrozenError,
    InvalidOperationError,
)

class Client:
    def __init__(
        self,
        client_id: str,
        full_name: str,
        birth_date: str,  # Формат YYYY-MM-DD
        phone: str = "",
        email: str = "",
        status: AccountStatus = AccountStatus.ACTIVE,
        pin: str = "1234",
    ):
        self.client_id = client_id or UUIDGenerator.generate()
        self.full_name = full_name
        self.birth_date = birth_date
        self.phone = phone
        self.email = email
        self.status = status
        self.pin = pin
        self.accounts: list[str] = []  # UUID счетов

        self._validate_age()

    def add_account(self, account_uuid: str) -> None:  # ← ДОБАВЬ ЭТОТ МЕТОД
        """Добавить UUID счёта к списку счетов клиента"""
        if self.status != AccountStatus.ACTIVE:
            raise AccountFrozenError("Cannot add accounts to inactive client")
        self.accounts.append(account_uuid)

    def _validate_age(self) -> None:
        # Проверяем возраст только для физических лиц
        if self.client_id[:2].upper() != "FL":
            return

        birth = datetime.strptime(self.birth_date, "%Y-%m-%d")
        age = datetime.now().year - birth.year

        if age < 18:
            raise InvalidOperationError("Client must be at least 18 years old")