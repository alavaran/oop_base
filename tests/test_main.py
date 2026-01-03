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
    AccountStatus,
    InsufficientFundsError,
    AccountFrozenError,
    InvalidOperationError,
)


class TestBankAccount(unittest.TestCase):
    def test_deposit_success(self):
        """Тест успешного пополнения"""
        account = BankAccount(
            firts_last_name="Test User", balance=1000, currency="RUB", type_account="FL"
        )
        account.deposit(500)
        account.withdraw(500)
        self.assertEqual(account._balance, 1000)

    def test_withdraw_success(self):
        """Тест успешного снятия"""
        account = BankAccount(
            firts_last_name="Test User", balance=1000, currency="RUB", type_account="FL", status=AccountStatus.FROZEN
        )
        account.withdraw(500)
        self.assertEqual(account._balance, 500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
