from abc import ABC, abstractmethod
from exceptions import (
    InsufficientFundsError,
    InvalidOperationError
)

from enums import (
    Currency,
    AccountType,
    AccountStatus
)

from app_logging import (
    TransactionLogger,
    ConsoleLogger,
    FileLogger
)

from validators import (
    AmountValidator,
    BalanceValidator,
    AccountStatusValidator
)

from assets import (
    Asset,
    Stock,
    Bond,

    ETF
)
from utils import (
    UUIDGenerator
)

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

        was_positive = self._balance >= 0
        will_go_negative = self._balance - amount < 0

        # Комиссия начисляется только при первом уходе в овердрафт
        fee = 0
        if was_positive and will_go_negative and not self._fee_charged:
            fee = self.fixed_fee

        total_amount = amount + fee

        # Проверяем лимит с учетом комиссии
        if self._balance - total_amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"Withdrawal exceeds overdraft limit of {self.overdraft_limit}"
            )

        # Выполняем списание
        self._balance -= amount

        # Начисляем комиссию за первый уход в овердрафт
        if fee > 0:
            self._balance -= fee
            self._fee_charged = True

            print(
                f"💳 Начислена комиссия за овердрафт: "
                f"{self.fixed_fee} {self.currency.value}"
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

        if not isinstance(asset, (Stock, Bond, ETF)):
            raise InvalidOperationError("Unsupported asset type")

        cost = asset.get_value()

        if cost <= 0:
            raise InvalidOperationError("Asset value must be positive")

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

    def project_yearly_growth(self, growth_rates: dict[str, float]) -> dict:
        """Прогноз роста портфеля по типам активов."""

        current_value = self.get_total_value()

        asset_values = {
            "stocks": 0,
            "bonds": 0,
            "etf": 0,
        }

        for asset in self.portfolio:
            if isinstance(asset, Stock):
                asset_values["stocks"] += asset.get_value()
            elif isinstance(asset, Bond):
                asset_values["bonds"] += asset.get_value()
            elif isinstance(asset, ETF):
                asset_values["etf"] += asset.get_value()

        required_types = {"stocks", "bonds", "etf"}

        if not required_types.issubset(growth_rates):
            raise InvalidOperationError(
                "Growth rates must contain stocks, bonds and etf"
    )
        projections = {}

        for asset_type, value in asset_values.items():
            rate = growth_rates.get(asset_type, 0)
            projections[asset_type] = round(value * (1 + rate), 2)

        return {
            "current_value": round(current_value, 2),
            "projections": projections,
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