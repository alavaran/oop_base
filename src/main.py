from abc import ABC, abstractmethod
import uuid
from enum import Enum
from typing import Protocol
from datetime import datetime, timedelta
import logging
import heapq
from typing import Optional, Callable
from dataclasses import dataclass, field


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


class Asset:
    """Базовый класс для активов"""

    def __init__(self, symbol: str, quantity: float, price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

    def get_value(self) -> float:
        return self.quantity * self.price

    def __str__(self) -> str:
        return f"{self.symbol}: {self.quantity} шт. @ {self.price}"


class Stock(Asset):
    """Акции"""

    def __init__(
        self, symbol: str, quantity: float, price: float, dividend_yield: float = 0.0
    ):
        super().__init__(symbol, quantity, price)
        self.dividend_yield = dividend_yield


class Bond(Asset):
    """Облигации"""

    def __init__(
        self, symbol: str, quantity: float, price: float, coupon_rate: float = 0.0
    ):
        super().__init__(symbol, quantity, price)
        self.coupon_rate = coupon_rate


class ETF(Asset):
    """ETF-фонды"""

    def __init__(
        self, symbol: str, quantity: float, price: float, expense_ratio: float = 0.0
    ):
        super().__init__(symbol, quantity, price)
        self.expense_ratio = expense_ratio


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


# ============ SavingsAccount  ============
class SavingsAccount(BankAccount):
    """Сберегательный счет с процентами"""

    def __init__(
        self,
        first_last_name: str,
        account_type: AccountType,
        currency: Currency,
        monthly_interest_rate: float,
        balance: float = 0,
        min_balance: float = 1000,
        status: AccountStatus = AccountStatus.ACTIVE,
        account_uuid: str = None,
        logger: TransactionLogger = None,
    ):
        if min_balance < 0:
            raise InsufficientFundsError("Minimum balance cannot be negative")

        super().__init__(
            first_last_name=first_last_name,
            account_type=account_type,
            currency=currency,
            balance=balance,
            status=status,
            account_uuid=account_uuid,
            logger=logger,
        )
        self.min_balance = min_balance
        self.monthly_interest_rate = monthly_interest_rate

    def withdraw(self, amount: float) -> None:
        """Снятие со счета с учетом минимального остатка"""
        AmountValidator.validate(amount)
        AccountStatusValidator.validate_for_operation(self.status)

        if self._balance - amount < self.min_balance:
            raise InsufficientFundsError(
                f"Withdrawal would violate minimum balance requirement of {self.min_balance}"
            )

        self._balance -= amount
        self._logger.log_withdrawal(amount, self._balance)

    def apply_monthly_interest(self) -> None:
        """Начисление месячных процентов"""
        AccountStatusValidator.validate_for_operation(self.status)

        interest = self._balance * self.monthly_interest_rate
        self._balance += interest
        print(f"💰 Начислены проценты: {interest:.2f} {self.currency.value}")
        print(f"📈 Новый баланс: {self._balance:.2f} {self.currency.value}")

    def get_account_info(self) -> dict:
        """Получение информации о счете"""
        info = super().get_account_info()
        info.update(
            {
                "account_subtype": "Savings",
                "min_balance": self.min_balance,
                "monthly_interest_rate": f"{self.monthly_interest_rate * 100}%",
            }
        )
        return info

    def __str__(self) -> str:
        return (
            f"{'=' * 30}\n"
            f"💰 СБЕРЕГАТЕЛЬНЫЙ СЧЕТ\n"
            f"{'=' * 30}\n"
            f"UUID: {self.account_uuid}\n"
            f"Владелец: {self.first_last_name}\n"
            f"Тип: {self.account_type.value}\n"
            f"Валюта: {self.currency.value}\n"
            f"Баланс: {self._balance:.2f}\n"
            f"Мин. остаток: {self.min_balance:.2f}\n"
            f"Ставка: {self.monthly_interest_rate * 100:.2f}%/мес\n"
            f"Статус: {self.status.value}\n"
            f"{'=' * 30}"
        )


# ============ PremiumAccount ============
class PremiumAccount(BankAccount):
    """Премиум счет с овердрафтом"""

    def __init__(
        self,
        first_last_name: str,
        account_type: AccountType,
        currency: Currency,
        balance: float = 0,
        overdraft_limit: float = 10000,
        fixed_fee: float = 50,
        status: AccountStatus = AccountStatus.ACTIVE,
        account_uuid: str = None,
        logger: TransactionLogger = None,
    ):
        super().__init__(
            first_last_name=first_last_name,
            account_type=account_type,
            currency=currency,
            balance=balance,
            status=status,
            account_uuid=account_uuid,
            logger=logger,
        )
        self.overdraft_limit = overdraft_limit
        self.fixed_fee = fixed_fee
        self._fee_charged = False

    @property
    def fee_charged(self) -> bool:
        """Получение статуса комиссии"""
        return self._fee_charged

    def withdraw(self, amount: float) -> None:
        """Снятие со счета с учетом овердрафта"""
        AmountValidator.validate(amount)
        AccountStatusValidator.validate_for_operation(self.status)

        if self._balance - amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"Withdrawal exceeds overdraft limit of {self.overdraft_limit}"
            )

        was_positive = self._balance >= 0
        self._balance -= amount
        is_negative = self._balance < 0

        # Начисляем комиссию при ПЕРВОМ уходе в овердрафт
        if was_positive and is_negative and not self._fee_charged:
            self._balance -= self.fixed_fee
            self._fee_charged = True
            print(
                f"💳 Начислена комиссия за овердрафт: {self.fixed_fee} {self.currency.value}"
            )

        self._logger.log_withdrawal(amount, self._balance)

    def deposit(self, amount: float) -> None:
        """Пополнение с возвратом статуса комиссии"""
        super().deposit(amount)

        # Сбрасываем флаг комиссии, если вышли из овердрафта
        if self._balance >= 0:
            self._fee_charged = False

    def get_account_info(self) -> dict:
        """Получение информации о счете"""
        info = super().get_account_info()
        info.update(
            {
                "account_subtype": "Premium",
                "overdraft_limit": self.overdraft_limit,
                "fixed_fee": self.fixed_fee,
                "available_balance": self._balance + self.overdraft_limit,
            }
        )
        return info

    def __str__(self) -> str:
        available = self._balance + self.overdraft_limit
        return (
            f"{'=' * 30}\n"
            f"⭐ ПРЕМИУМ СЧЕТ\n"
            f"{'=' * 30}\n"
            f"UUID: {self.account_uuid}\n"
            f"Владелец: {self.first_last_name}\n"
            f"Тип: {self.account_type.value}\n"
            f"Валюта: {self.currency.value}\n"
            f"Баланс: {self._balance:.2f}\n"
            f"Лимит овердрафта: {self.overdraft_limit:.2f}\n"
            f"Доступно: {available:.2f}\n"
            f"Комиссия: {self.fixed_fee:.2f}\n"
            f"Статус: {self.status.value}\n"
            f"{'=' * 30}"
        )


# ============ InvestmentAccount ============
class InvestmentAccount(BankAccount):
    """Инвестиционный счет с портфелем активов"""

    def __init__(
        self,
        first_last_name: str,
        account_type: AccountType,
        currency: Currency,
        balance: float = 0,
        expected_annual_return: float = 0.08,
        status: AccountStatus = AccountStatus.ACTIVE,
        account_uuid: str = None,
        logger: TransactionLogger = None,
    ):
        super().__init__(
            first_last_name=first_last_name,
            account_type=account_type,
            currency=currency,
            balance=balance,
            status=status,
            account_uuid=account_uuid,
            logger=logger,
        )
        self.portfolio: list[Asset] = []
        self.expected_annual_return = expected_annual_return

    def add_asset(self, asset: Asset) -> None:
        """Добавление актива в портфель"""
        AccountStatusValidator.validate_for_operation(self.status)

        cost = asset.get_value()
        if self._balance < cost:
            raise InsufficientFundsError(
                f"Insufficient funds to buy asset. Need: {cost}"
            )

        self._balance -= cost
        self.portfolio.append(asset)
        print(f"📊 Куплен актив: {asset}")
        print(f"💰 Потрачено: {cost:.2f} {self.currency.value}")

    def get_portfolio_value(self) -> float:
        """Общая стоимость портфеля"""
        return sum(asset.get_value() for asset in self.portfolio)

    def get_total_value(self) -> float:
        """Общая стоимость счета (баланс + портфель)"""
        return self._balance + self.get_portfolio_value()

    def project_yearly_growth(self, years: int = 1) -> dict:
        """Прогноз роста на N лет"""
        current_value = self.get_total_value()
        projected_values = {}

        for year in range(1, years + 1):
            projected_value = current_value * (
                (1 + self.expected_annual_return) ** year
            )
            projected_values[f"year_{year}"] = round(projected_value, 2)

        return {
            "current_value": round(current_value, 2),
            "expected_return": f"{self.expected_annual_return * 100}%",
            "projections": projected_values,
        }

    def withdraw(self, amount: float) -> None:
        """Снятие только из свободных средств (не из портфеля)"""
        AmountValidator.validate(amount)
        AccountStatusValidator.validate_for_operation(self.status)

        if self._balance < amount:
            raise InsufficientFundsError(
                f"Insufficient free cash. Available: {self._balance}, "
                f"Portfolio value: {self.get_portfolio_value()}"
            )

        self._balance -= amount
        self._logger.log_withdrawal(amount, self._balance)

    def get_account_info(self) -> dict:
        """Получение информации о счете"""
        info = super().get_account_info()
        info.update(
            {
                "account_subtype": "Investment",
                "portfolio_value": self.get_portfolio_value(),
                "total_value": self.get_total_value(),
                "assets_count": len(self.portfolio),
                "expected_annual_return": f"{self.expected_annual_return * 100}%",
            }
        )
        return info

    def __str__(self) -> str:
        portfolio_value = self.get_portfolio_value()
        total_value = self.get_total_value()

        portfolio_str = (
            "\n".join([f"  • {asset}" for asset in self.portfolio]) or "  (пусто)"
        )

        return (
            f"{'=' * 30}\n"
            f"📈 ИНВЕСТИЦИОННЫЙ СЧЕТ\n"
            f"{'=' * 30}\n"
            f"UUID: {self.account_uuid}\n"
            f"Владелец: {self.first_last_name}\n"
            f"Тип: {self.account_type.value}\n"
            f"Валюта: {self.currency.value}\n"
            f"Свободные средства: {self._balance:.2f}\n"
            f"Стоимость портфеля: {portfolio_value:.2f}\n"
            f"Общая стоимость: {total_value:.2f}\n"
            f"Ожидаемая доходность: {self.expected_annual_return * 100:.1f}%/год\n"
            f"Портфель ({len(self.portfolio)} активов):\n{portfolio_str}\n"
            f"Статус: {self.status.value}\n"
            f"{'=' * 30}"
        )


class Client(BankAccount):
    def __init__(
        self,
        client_id: str,
        full_name: str,
        birth_date: str,  # Формат YYYY-MM-DD
        phone: str = "",
        email: str = "",
        status: AccountStatus = AccountStatus.ACTIVE,
    ):
        self.client_id = client_id or UUIDGenerator.generate()
        self.full_name = full_name
        self.birth_date = birth_date
        self.phone = phone
        self.email = email
        self.status = status
        self.accounts: list[str] = []  # UUID счетов

        self._validate_age()

    def add_account(self, account_uuid: str) -> None:  # ← ДОБАВЬ ЭТОТ МЕТОД
        """Добавить UUID счёта к списку счетов клиента"""
        if self.status != AccountStatus.ACTIVE:
            raise AccountFrozenError("Cannot add accounts to inactive client")
        self.accounts.append(account_uuid)

    def _validate_age(self) -> None:
        birth = datetime.strptime(self.birth_date, "%Y-%m-%d")
        age = datetime.now().year - birth.year
        if age < 18:
            raise InvalidOperationError("Client must be at least 18 years old")


class Bank:
    def __init__(self, logger: TransactionLogger = None):
        self.clients: dict[str, Client] = {}  # client_id -> Client
        self.accounts: dict[str, AbstractAccount] = {}  # account_uuid -> Account
        self.failed_attempts: dict[str, int] = {}  # client_id -> count
        self.suspicious_actions: set[str] = set()  # client_ids
        self._logger = logger or ConsoleLogger()

    def add_client(self, client: Client) -> None:
        if client.client_id in self.clients:
            raise InvalidOperationError("Client already exists")
        self.clients[client.client_id] = client

    def authenticate_client(self, client_id: str, pin: str) -> bool:
        now_hour = datetime.now().hour
        if 0 <= now_hour < 5:
            raise InvalidOperationError("Operations forbidden from 00:00 to 05:00")

        if client_id not in self.clients:
            return False

        if self.failed_attempts.get(client_id, 0) >= 3:
            self.suspicious_actions.add(client_id)
            return False

        return True

    def open_account(
        self,
        client_id: str,
        account_type: type[AbstractAccount],
        currency: Currency,
        **kwargs,
    ) -> str:
        if not self.authenticate_client(client_id, "1234"):
            raise AccountClosedError("Authentication failed")

        client = self.clients[client_id]
        if client.status != AccountStatus.ACTIVE:
            raise AccountFrozenError("Client inactive")

        account = account_type(
            first_last_name=client.full_name,
            account_type=client_id[:2].upper(),  # UL/FL из ID
            currency=currency,
            **kwargs,
        )
        account_uuid = account.account_uuid
        self.accounts[account_uuid] = account
        client.add_account(account_uuid)
        return account_uuid

    def close_account(self, account_uuid: str, client_id: str) -> None:
        if not self.authenticate_client(client_id, "1234"):
            raise AccountClosedError("Authentication failed")
        if account_uuid not in self.accounts:
            raise InvalidOperationError("Account not found")
        self.accounts[account_uuid].status = AccountStatus.CLOSED
        self.suspicious_actions.discard(client_id)

    def freeze_account(self, account_uuid: str, admin_id: str) -> None:
        if account_uuid in self.accounts:
            self.accounts[account_uuid].status = AccountStatus.FROZEN
            self.suspicious_actions.add(self.accounts[account_uuid].first_last_name)

    def unfreeze_account(self, account_uuid: str, admin_id: str) -> None:
        if account_uuid in self.accounts:
            self.accounts[account_uuid].status = AccountStatus.ACTIVE

    def search_accounts(self, client_id: str) -> list[dict]:
        if client_id not in self.clients:
            return []
        return [
            self.accounts[uuid].get_account_info()
            for uuid in self.clients[client_id].accounts
        ]

    def get_total_balance(self) -> float:
        return sum(
            acc.balance
            for acc in self.accounts.values()
            if acc.status == AccountStatus.ACTIVE
        )

    def get_clients_ranking(self, top_n: int = 10) -> list[dict]:
        ranking = []
        for client in self.clients.values():
            total = sum(
                self.accounts[uuid].balance
                for uuid in client.accounts
                if uuid in self.accounts
            )
            ranking.append({"client": client.full_name, "total": total})
        return sorted(ranking, key=lambda x: x["total"], reverse=True)[:top_n]


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    EXTERNAL_TRANSFER = "external_transfer"


class TransactionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionPriority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


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


class TransactionQueue:
    """Очередь транзакций с приоритетами и отложенным выполнением"""

    def __init__(self):
        self._queue: list[tuple] = []  # heap: (priority, timestamp, transaction)
        self._scheduled: list[tuple] = []  # (execute_at, transaction)
        self._transactions: dict[str, Transaction] = {}

    def add_transaction(self, transaction: Transaction, delay_seconds: int = 0) -> None:
        """Добавить транзакцию в очередь"""
        self._transactions[transaction.transaction_id] = transaction

        if delay_seconds > 0:
            execute_at = datetime.now() + timedelta(seconds=delay_seconds)
            self._scheduled.append((execute_at, transaction))
            print(
                f"⏳ Транзакция {transaction.transaction_id} отложена до {execute_at.strftime('%H:%M:%S')}"
            )
        else:
            heapq.heappush(
                self._queue,
                (transaction.priority.value, transaction.created_at, transaction),
            )
            print(
                f"➕ Транзакция {transaction.transaction_id} добавлена с приоритетом {transaction.priority.name}"
            )

    def get_next_transaction(self) -> Optional[Transaction]:
        """Получить следующую транзакцию из очереди"""
        # Проверяем отложенные транзакции
        self._process_scheduled()

        if not self._queue:
            return None

        _, _, transaction = heapq.heappop(self._queue)
        transaction.status = TransactionStatus.PROCESSING
        return transaction

    def _process_scheduled(self) -> None:
        """Переместить готовые отложенные транзакции в основную очередь"""
        now = datetime.now()
        ready = []
        still_scheduled = []

        for execute_at, transaction in self._scheduled:
            if execute_at <= now:
                ready.append(transaction)
            else:
                still_scheduled.append((execute_at, transaction))

        self._scheduled = still_scheduled

        for transaction in ready:
            heapq.heappush(
                self._queue,
                (transaction.priority.value, transaction.created_at, transaction),
            )
            print(
                f"⏰ Отложенная транзакция {transaction.transaction_id} готова к выполнению"
            )

    def cancel_transaction(self, transaction_id: str) -> bool:
        """Отменить транзакцию"""
        if transaction_id not in self._transactions:
            return False

        transaction = self._transactions[transaction_id]

        try:
            transaction.mark_cancelled()
            # Удаляем из очереди (помечаем как отменённую)
            return True
        except InvalidOperationError:
            return False

    def get_pending_count(self) -> int:
        """Количество ожидающих транзакций"""
        return len(self._queue) + len(self._scheduled)

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Получить транзакцию по ID"""
        return self._transactions.get(transaction_id)


# ============ Currency Converter ============
class CurrencyConverter:
    """Конвертер валют с курсами"""

    # Упрощённые курсы относительно RUB
    RATES = {
        Currency.RUB: 1.0,
        Currency.USD: 95.0,
        Currency.EUR: 105.0,
        Currency.KZT: 0.21,
        Currency.CNY: 13.5,
    }

    @classmethod
    def convert(
        cls, amount: float, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Конвертация между валютами"""
        if from_currency == to_currency:
            return amount

        # Конвертируем через RUB
        amount_in_rub = amount * cls.RATES[from_currency]
        result = amount_in_rub / cls.RATES[to_currency]
        return round(result, 2)

    @classmethod
    def get_rate(cls, from_currency: Currency, to_currency: Currency) -> float:
        """Получить курс конвертации"""
        return cls.RATES[from_currency] / cls.RATES[to_currency]


# ============ Fee Calculator ============
class FeeCalculator:
    """Калькулятор комиссий"""

    INTERNAL_TRANSFER_FEE = 0.0  # Бесплатно
    EXTERNAL_TRANSFER_FEE_PERCENT = 0.015  # 1.5%
    EXTERNAL_TRANSFER_MIN_FEE = 50.0  # Минимум 50 RUB
    CURRENCY_CONVERSION_FEE_PERCENT = 0.01  # 1%

    @classmethod
    def calculate_fee(
        cls,
        transaction_type: TransactionType,
        amount: float,
        currency: Currency,
        currency_conversion: bool = False,
    ) -> float:
        """Расчёт комиссии"""
        fee = 0.0

        if transaction_type == TransactionType.EXTERNAL_TRANSFER:
            fee = max(
                amount * cls.EXTERNAL_TRANSFER_FEE_PERCENT,
                cls.EXTERNAL_TRANSFER_MIN_FEE,
            )

        if currency_conversion:
            fee += amount * cls.CURRENCY_CONVERSION_FEE_PERCENT

        return round(fee, 2)


# ============ Transaction Processor ============
class TransactionProcessor:
    """Обработчик транзакций с повторами и логированием"""

    def __init__(self, bank: "Bank", max_retries: int = 3):
        self.bank = bank
        self.max_retries = max_retries
        self.failed_transactions: list[Transaction] = []

    def process_transaction(self, transaction: Transaction) -> bool:
        """Обработать транзакцию с повторами"""
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
