from abc import ABC, abstractmethod
import app_logging

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
        self.logger = app_logging.getLogger(__name__)
        self.logger.setLevel(app_logging.INFO)
        handler = app_logging.FileHandler(filename)
        formatter = app_logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_deposit(self, amount: float, balance: float) -> None:
        self.logger.info(f"Deposit: {amount}, New balance: {balance}")

    def log_withdrawal(self, amount: float, balance: float) -> None:
        self.logger.info(f"Withdrawal: {amount}, New balance: {balance}")
