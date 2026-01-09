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
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
    Stock,
    ETF,
    Bond,
    Bank,
    Client
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


""""""


# ============ Тесты для SavingsAccount ============
class TestSavingsAccount(unittest.TestCase):
    """Тесты для класса SavingsAccount"""

    def test_apply_monthly_interest_success(self):
        """Тест успешного начисления процентов"""
        mock_logger = MockLogger()
        account = SavingsAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            monthly_interest_rate=0.05,
            balance=10000,
            min_balance=1000,
            logger=mock_logger,
        )

        initial_balance = account.balance
        account.apply_monthly_interest()
        expected_balance = initial_balance * 1.05

        self.assertEqual(account.balance, expected_balance)

    def test_withdraw_below_min_balance(self):
        """Тест снятия, нарушающего минимальный остаток"""
        mock_logger = MockLogger()
        account = SavingsAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            monthly_interest_rate=0.03,
            balance=5000,
            min_balance=1000,
            logger=mock_logger,
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(4500)

    def test_withdraw_respecting_min_balance(self):
        """Тест снятия с учетом минимального остатка"""
        mock_logger = MockLogger()
        account = SavingsAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            monthly_interest_rate=0.03,
            balance=5000,
            min_balance=1000,
            logger=mock_logger,
        )

        account.withdraw(4000)
        self.assertEqual(account.balance, 1000)

    def test_interest_on_frozen_account(self):
        """Тест начисления процентов на замороженный счёт"""
        mock_logger = MockLogger()
        account = SavingsAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            monthly_interest_rate=0.05,
            balance=10000,
            min_balance=1000,
            status=AccountStatus.FROZEN,
            logger=mock_logger,
        )

        with self.assertRaises(AccountFrozenError):
            account.apply_monthly_interest()

    def test_negative_min_balance_init(self):
        """Тест создания счёта с отрицательным минимальным остатком"""
        mock_logger = MockLogger()

        with self.assertRaises(InsufficientFundsError):
            SavingsAccount(
                first_last_name="Test User",
                account_type=AccountType.INDIVIDUAL,
                currency=Currency.RUB,
                monthly_interest_rate=0.03,
                balance=5000,
                min_balance=-1000,
                logger=mock_logger,
            )

    def test_get_account_info_savings(self):
        """Тест получения информации о сберегательном счёте"""
        mock_logger = MockLogger()
        account = SavingsAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.RUB,
            monthly_interest_rate=0.05,
            balance=10000,
            min_balance=1000,
            logger=mock_logger,
        )

        info = account.get_account_info()

        self.assertEqual(info["account_subtype"], "Savings")
        self.assertEqual(info["min_balance"], 1000)
        self.assertIn("monthly_interest_rate", info)


# ============ Тесты для PremiumAccount ============
class TestPremiumAccount(unittest.TestCase):
    """Тесты для класса PremiumAccount"""

    def test_withdraw_with_overdraft(self):
        """Тест снятия с использованием овердрафта"""
        mock_logger = MockLogger()
        account = PremiumAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            overdraft_limit=5000,
            fixed_fee=50,
            logger=mock_logger,
        )

        account.withdraw(3000)
        expected_balance = 1000 - 3000 - 50  # balance - withdrawal - fee
        self.assertEqual(account.balance, expected_balance)

    def test_withdraw_exceeding_overdraft_limit(self):
        """Тест снятия, превышающего лимит овердрафта"""
        mock_logger = MockLogger()
        account = PremiumAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            overdraft_limit=5000,
            fixed_fee=50,
            logger=mock_logger,
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(7000)

    def test_fee_charged_once_in_overdraft(self):
        """Тест начисления комиссии только один раз при овердрафте"""
        mock_logger = MockLogger()
        account = PremiumAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            overdraft_limit=5000,
            fixed_fee=50,
            logger=mock_logger,
        )

        account.withdraw(1500)  # Первый овердрафт
        balance_after_first = account.balance

        account.withdraw(500)  # Второй овердрафт
        balance_after_second = account.balance

        # Комиссия должна быть списана только один раз
        self.assertEqual(balance_after_second, balance_after_first - 500)

    def test_fee_reset_after_positive_balance(self):
        """Тест сброса флага комиссии после выхода из овердрафта"""
        mock_logger = MockLogger()
        account = PremiumAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            overdraft_limit=5000,
            fixed_fee=50,
            logger=mock_logger,
        )

        account.withdraw(1500)  # Овердрафт с комиссией
        account.deposit(2000)  # Возврат к положительному балансу

        self.assertFalse(account.fee_charged)

    def test_deposit_in_overdraft(self):
        """Тест пополнения счёта в овердрафте"""
        mock_logger = MockLogger()
        account = PremiumAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            overdraft_limit=5000,
            fixed_fee=50,
            logger=mock_logger,
        )

        account.withdraw(2000)  # Баланс: -1050
        account.deposit(3000)  # Баланс: 1950

        self.assertEqual(account.balance, 1950)
        self.assertFalse(account.fee_charged)

    def test_get_account_info_premium(self):
        """Тест получения информации о премиум счёте"""
        mock_logger = MockLogger()
        account = PremiumAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            overdraft_limit=5000,
            fixed_fee=50,
            logger=mock_logger,
        )

        info = account.get_account_info()

        self.assertEqual(info["account_subtype"], "Premium")
        self.assertEqual(info["overdraft_limit"], 5000)
        self.assertEqual(info["available_balance"], 6000)


# ============ Тесты для InvestmentAccount ============
class TestInvestmentAccount(unittest.TestCase):
    """Тесты для класса InvestmentAccount"""

    def test_add_asset_success(self):
        """Тест успешного добавления актива"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=10000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        stock = Stock("AAPL", 10, 150)
        account.add_asset(stock)

        self.assertEqual(len(account.portfolio), 1)
        self.assertEqual(account.balance, 10000 - 1500)

    def test_add_asset_insufficient_funds(self):
        """Тест добавления актива при недостаточных средствах"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=1000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        stock = Stock("AAPL", 10, 150)

        with self.assertRaises(InsufficientFundsError):
            account.add_asset(stock)

    def test_get_portfolio_value(self):
        """Тест расчёта стоимости портфеля"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=50000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        account.add_asset(Stock("AAPL", 10, 150))  # 1500
        account.add_asset(Bond("US10Y", 5, 1000))  # 5000
        account.add_asset(ETF("SPY", 20, 400))  # 8000

        expected_portfolio_value = 1500 + 5000 + 8000
        self.assertEqual(account.get_portfolio_value(), expected_portfolio_value)

    def test_get_total_value(self):
        """Тест расчёта общей стоимости счёта"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=50000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        account.add_asset(Stock("AAPL", 10, 150))

        expected_total = (50000 - 1500) + 1500
        self.assertEqual(account.get_total_value(), expected_total)

    def test_project_yearly_growth(self):
        """Тест прогноза годового роста"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=10000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        projection = account.project_yearly_growth(years=3)

        self.assertIn("current_value", projection)
        self.assertIn("projections", projection)
        self.assertEqual(len(projection["projections"]), 3)

        # Проверка расчёта для первого года
        expected_year_1 = round(10000 * 1.10, 2)
        self.assertEqual(projection["projections"]["year_1"], expected_year_1)

    def test_withdraw_only_free_cash(self):
        """Тест снятия только из свободных средств"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=10000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        account.add_asset(Stock("AAPL", 10, 150))

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(9000)

    def test_withdraw_free_cash_available(self):
        """Тест снятия доступных свободных средств"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=10000,
            expected_annual_return=0.10,
            logger=mock_logger,
        )

        account.add_asset(Stock("AAPL", 10, 150))
        account.withdraw(5000)

        expected_balance = 10000 - 1500 - 5000
        self.assertEqual(account.balance, expected_balance)

    def test_add_asset_frozen_account(self):
        """Тест добавления актива на замороженный счёт"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=10000,
            expected_annual_return=0.10,
            status=AccountStatus.FROZEN,
            logger=mock_logger,
        )

        stock = Stock("AAPL", 10, 150)

        with self.assertRaises(AccountFrozenError):
            account.add_asset(stock)

    def test_get_account_info_investment(self):
        """Тест получения информации об инвестиционном счёте"""
        mock_logger = MockLogger()
        account = InvestmentAccount(
            first_last_name="Test User",
            account_type=AccountType.INDIVIDUAL,
            currency=Currency.USD,
            balance=50000,
            expected_annual_return=0.12,
            logger=mock_logger,
        )

        account.add_asset(Stock("AAPL", 10, 150))

        info = account.get_account_info()

        self.assertEqual(info["account_subtype"], "Investment")
        self.assertIn("portfolio_value", info)
        self.assertIn("total_value", info)
        self.assertEqual(info["assets_count"], 1)

def test_bank_add_client_success(self):
    """Тест успешного добавления клиента"""
    client = Client(
        client_id="FL001",
        full_name="Иван Иванов",
        birth_date="1990-05-15"
    )
    
    bank = Bank()
    bank.add_client(client)
    
    self.assertIn("FL001", bank.clients)
    self.assertEqual(bank.clients["FL001"].full_name, "Иван Иванов")


def test_bank_add_client_duplicate(self):
    """Тест добавления дублирующегося клиента"""
    client = Client("FL001", "Иван Иванов", "1990-05-15")
    
    bank = Bank()
    bank.add_client(client)
    
    with self.assertRaises(InvalidOperationError):
        bank.add_client(client)  # Должен упасть


def test_bank_client_age_validation(self):
    """Тест валидации возраста клиента"""
    with self.assertRaises(InvalidOperationError):
        Client("UL999", "Младенец", "2025-01-01")  # <18 лет


def test_bank_open_account_success(self):
    """Тест открытия счёта с успешной аутентификацией"""
    client = Client("FL001", "Иван Иванов", "1990-05-15")
    bank = Bank()
    bank.add_client(client)
    
    acc_uuid = bank.open_account(
        client_id="FL001",
        account_type=BankAccount,
        currency=Currency.RUB,
        balance=10000
    )
    
    self.assertIn(acc_uuid, bank.accounts)
    self.assertEqual(bank.accounts[acc_uuid].balance, 10000)
    self.assertIn(acc_uuid, client.accounts)


def test_bank_open_account_auth_fail(self):
    """Тест отказа в открытии счёта из-за аутентификации"""
    client = Client("FL001", "Иван Иванов", "1990-05-15")
    bank = Bank()
    bank.add_client(client)
    
    with self.assertRaises(AccountClosedError):
        bank.open_account("fake_id", BankAccount, Currency.RUB)


def test_bank_three_failed_attempts(self):
    """Тест блокировки после 3 неудачных попыток"""
    bank = Bank()
    
    # 3 неудачные попытки
    for _ in range(3):
        try:
            bank.open_account("fake_id", BankAccount, Currency.RUB)
        except AccountClosedError:
            pass
    
    # 4-я попытка должна быть заблокирована
    with self.assertRaises(AccountClosedError):
        bank.open_account("fake_id", BankAccount, Currency.RUB)


def test_bank_freeze_unfreeze_account(self):
    """Тест заморозки/разморозки счёта"""
    client = Client("FL001", "Иван Иванов", "1990-05-15")
    bank = Bank()
    bank.add_client(client)
    
    acc_uuid = bank.open_account("FL001", BankAccount, Currency.RUB, balance=10000)
    account = bank.accounts[acc_uuid]
    
    # Заморозка
    bank.freeze_account(acc_uuid, "admin")
    self.assertEqual(account.status, AccountStatus.FROZEN)
    
    # Разморозка
    bank.unfreeze_account(acc_uuid, "admin")
    self.assertEqual(account.status, AccountStatus.ACTIVE)


def test_bank_search_accounts(self):
    """Тест поиска счетов клиента"""
    client = Client("FL001", "Иван Иванов", "1990-05-15")
    bank = Bank()
    bank.add_client(client)
    
    acc1 = bank.open_account("FL001", SavingsAccount, Currency.RUB, balance=5000, monthly_interest_rate=0.01)
    acc2 = bank.open_account("FL001", PremiumAccount, Currency.USD, balance=10000, overdraft_limit=2000)
    
    accounts_info = bank.search_accounts("FL001")
    
    self.assertEqual(len(accounts_info), 2)
    self.assertEqual(accounts_info[0]["balance"], 5000)
    self.assertEqual(accounts_info[1]["balance"], 10000)


def test_bank_total_balance(self):
    """Тест подсчёта общего баланса банка"""
    client1 = Client("FL001", "Иван Иванов", "1990-05-15")
    client2 = Client("UL002", "ООО Альфа", "2010-01-01")
    
    bank = Bank()
    bank.add_client(client1)
    bank.add_client(client2)
    
    bank.open_account("FL001", BankAccount, Currency.RUB, balance=10000)
    bank.open_account("UL002", BankAccount, Currency.RUB, balance=5000)
    
    self.assertEqual(bank.get_total_balance(), 15000)  # Только ACTIVE


def test_bank_clients_ranking(self):
    """Тест ранжирования клиентов по балансу"""
    client1 = Client("FL001", "Иван Иванов", "1990-05-15")
    client2 = Client("UL002", "ООО Альфа", "2015-01-01")
    
    bank = Bank()
    bank.add_client(client1)
    bank.add_client(client2)
    
    bank.open_account("FL001", BankAccount, Currency.RUB, balance=20000)
    bank.open_account("UL002", BankAccount, Currency.RUB, balance=10000)
    
    ranking = bank.get_clients_ranking(2)
    
    self.assertEqual(ranking[0]["client"], "Иван Иванов")
    self.assertEqual(ranking[0]["total"], 20000)
    self.assertEqual(ranking[1]["client"], "ООО Альфа")
    self.assertEqual(ranking[1]["total"], 10000)



if __name__ == "__main__":
    unittest.main(verbosity=2)
