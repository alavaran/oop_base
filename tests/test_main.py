print("Тесты запускаются...")
import unittest
import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, "src")
sys.path.insert(0, src_dir)


from main import (
    BankAccount,
    AccountType,
    AccountStatus,
    Currency,
    InsufficientFundsError,
    AccountFrozenError,
    AccountClosedError,
    InvalidOperationError,
    TransactionLogger,
)


class MockLogger(TransactionLogger):
    """Mock-логгер для тестирования"""

    def __init__(self):
        self.deposits = []
        self.withdrawals = []

    def log_deposit(self, amount: float, balance: float) -> None:
        self.deposits.append({"amount": amount, "balance": balance})

    def log_withdrawal(self, amount: float, balance: float) -> None:
        self.withdrawals.append({"amount": amount, "balance": balance})


class TestBankAccount(unittest.TestCase):
    """Тесты для класса BankAccount"""

    def test_deposit_success(self):
        """Тест успешного пополнения и снятия"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )
        account.deposit(500)
        account.withdraw(500)
        self.assertEqual(account.balance, 1000)

    def test_withdraw_frozen_account(self):
        """Тест снятия с замороженного счёта - должно вызвать исключение"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            status=AccountStatus.FROZEN,
            logger=mock_logger,
        )

        with self.assertRaises(AccountFrozenError):
            account.withdraw(500)

    def test_deposit_frozen_account(self):
        """Тест пополнения замороженного счёта - должно вызвать исключение"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            status=AccountStatus.FROZEN,
            logger=mock_logger,
        )

        with self.assertRaises(AccountFrozenError):
            account.deposit(500)

    def test_insufficient_funds(self):
        """Тест снятия суммы больше баланса"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(1500)

    def test_invalid_amount_deposit(self):
        """Тест пополнения с невалидной суммой"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        with self.assertRaises(InvalidOperationError):
            account.deposit("invalid")

        with self.assertRaises(InvalidOperationError):
            account.deposit(-100)

    def test_invalid_amount_withdraw(self):
        """Тест снятия с невалидной суммой"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        with self.assertRaises(InvalidOperationError):
            account.withdraw(0)

        with self.assertRaises(InvalidOperationError):
            account.withdraw(-50)

    def test_closed_account_operations(self):
        """Тест операций с закрытым счётом"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            status=AccountStatus.CLOSED,
            logger=mock_logger,
        )

        with self.assertRaises(AccountClosedError):
            account.deposit(100)

        with self.assertRaises(AccountClosedError):
            account.withdraw(100)

    def test_negative_balance_init(self):
        """Тест создания счёта с отрицательным балансом"""
        mock_logger = MockLogger()

        with self.assertRaises(InsufficientFundsError):
            BankAccount(
                first_last_name="Test User",
                account_type=AccountType.INDIVIDUAL,
                currency=Currency.RUB,
                balance=-100,
                logger=mock_logger,
            )

    def test_get_account_info(self):
        """Тест получения информации о счёте"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        info = account.get_account_info()

        self.assertEqual(info["owner"], "Test User")
        self.assertEqual(info["currency"], "RUB")
        self.assertEqual(info["balance"], 1000)
        self.assertEqual(info["status"], "active")
        self.assertEqual(info["type"], "FL")
        self.assertIn("uuid", info)

    def test_uuid_generation(self):
        """Тест автоматической генерации UUID"""
        mock_logger = MockLogger()
        account1 = BankAccount(
            first_last_name="User1",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        account2 = BankAccount(
            first_last_name="User2",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        self.assertNotEqual(account1.account_uuid, account2.account_uuid)

    def test_balance_property(self):
        """Тест свойства balance"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        self.assertEqual(account.balance, 1000)
        account.deposit(500)
        self.assertEqual(account.balance, 1500)

    def test_legal_account_type(self):
        """Тест создания счёта юридического лица"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="ООО Рога и Копыта",
            account_type=AccountType.LEGAL,
            currency=Currency.USD,
            balance=5000,
            logger=mock_logger,
        )

        info = account.get_account_info()
        self.assertEqual(info["type"], "UL")
        self.assertEqual(info["currency"], "USD")

    def test_different_currencies(self):
        """Тест создания счетов с разными валютами"""
        mock_logger = MockLogger()
        currencies = [
            Currency.RUB,
            Currency.USD,
            Currency.EUR,
            Currency.KZT,
            Currency.CNY,
        ]

        for currency in currencies:
            account = BankAccount(
                first_last_name="Test User",
                account_type=AccountType.INDIVIDUAL,
                currency=currency,
                balance=1000,
                logger=mock_logger,
            )
            self.assertEqual(account.currency, currency)

    def test_multiple_transactions_logging(self):
        """Тест логирования нескольких транзакций"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            logger=mock_logger,
        )

        account.deposit(500)
        account.withdraw(200)
        account.deposit(100)

        self.assertEqual(len(mock_logger.deposits), 2)
        self.assertEqual(len(mock_logger.withdrawals), 1)
        self.assertEqual(account.balance, 1400)

    def test_frozen_account_no_logging(self):
        """Тест: замороженный счёт не логирует операции"""
        mock_logger = MockLogger()
        account = BankAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            balance=1000,
            status=AccountStatus.FROZEN,
            logger=mock_logger,
        )

        with self.assertRaises(AccountFrozenError):
            account.deposit(500)

        with self.assertRaises(AccountFrozenError):
            account.withdraw(200)

        # Логирование не должно произойти
        self.assertEqual(len(mock_logger.deposits), 0)
        self.assertEqual(len(mock_logger.withdrawals), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
