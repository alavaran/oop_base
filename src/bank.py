from datetime import datetime
from app_logging import (
    TransactionLogger,
    ConsoleLogger,
    FileLogger
)

from enums import (
    AccountStatus,
    AccountType,
    Currency
)

from accounts import (
    AbstractAccount,
    PremiumAccount
)

from client import (
    Client
)

from exceptions import (
    InsufficientFundsError,
    AccountFrozenError,
    AccountClosedError,
    InvalidOperationError,
)
from enums import (
    Currency,
    TransactionType,
    TransactionStatus,
    TransactionPriority,
)
from transactions import Transaction

class Bank:
    def __init__(self, logger: TransactionLogger = None):
        self.clients: dict[str, Client] = {}  # client_id -> Client
        self.accounts: dict[str, AbstractAccount] = {}  # account_uuid -> Account
        self.failed_attempts: dict[str, int] = {}  # client_id -> count
        self.suspicious_actions: set[str] = set()  # client_ids
        self._logger = logger or ConsoleLogger()
        self.transaction_history: dict[str, list[Transaction]] = {}
        self.account_to_client: dict[str, str] = {}

    def add_client(self, client: Client) -> None:
        if client.client_id in self.clients:
            raise InvalidOperationError("Client already exists")
        self.clients[client.client_id] = client

    def authenticate_client(self, client_id: str, pin: str) -> bool:
        now_hour = datetime.now().hour

        if 0 <= now_hour < 5:
            raise InvalidOperationError(
                "Operations forbidden from 00:00 to 05:00"
            )

        if client_id not in self.clients:
            return False

        if self.failed_attempts.get(client_id, 0) >= 3:
            self.suspicious_actions.add(client_id)
            return False

        client = self.clients[client_id]

        if pin != client.pin:
            self.failed_attempts[client_id] = (
                self.failed_attempts.get(client_id, 0) + 1
            )

            if self.failed_attempts[client_id] >= 3:
                self.suspicious_actions.add(client_id)

            return False

        self.failed_attempts[client_id] = 0

        return True

    def open_account(
        self,
        client_id: str,
        pin: str,
        account_type: type[AbstractAccount],
        currency: Currency,
        **kwargs,
    ) -> str:
        if not self.authenticate_client(client_id, pin):
            raise AccountClosedError("Authentication failed")

        client = self.clients[client_id]
        if client.status != AccountStatus.ACTIVE:
            raise AccountFrozenError("Client inactive")

        account_type_value = AccountType(client_id[:2].upper())

        account = account_type(
            first_last_name=client.full_name,
            account_type=account_type_value,
            currency=currency,
            **kwargs,
        )
        account_uuid = account.account_uuid
        self.accounts[account_uuid] = account
        client.add_account(account_uuid)
        self.account_to_client[account_uuid] = client_id
        return account_uuid

    def close_account(
        self,
        account_uuid: str,
        client_id: str,
        pin: str,
    ) -> None:
        if not self.authenticate_client(client_id, pin):
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
    
    def record_transaction(self, transaction: Transaction) -> None:
        account_ids = []

        if transaction.transaction_type == TransactionType.DEPOSIT:
            account_ids.append(transaction.receiver_account_id)

        elif transaction.transaction_type == TransactionType.TRANSFER:
            account_ids.append(transaction.sender_account_id)
            account_ids.append(transaction.receiver_account_id)

        else:
            account_ids.append(transaction.sender_account_id)

        # Собираем уникальных клиентов
        client_ids = set()

        for account_id in account_ids:
            client_id = self.account_to_client.get(account_id)

            if client_id is not None:
                client_ids.add(client_id)

        # Записываем транзакцию каждому клиенту только один раз
        for client_id in client_ids:
            if client_id not in self.transaction_history:
                self.transaction_history[client_id] = []

            self.transaction_history[client_id].append(transaction)