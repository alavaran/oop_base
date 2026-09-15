import random

from bank import Bank
from client import Client
from accounts import PremiumAccount
from enums import Currency, TransactionType, TransactionStatus
from transactions import Transaction
from queue import TransactionQueue
from processor import TransactionProcessor
from reports import ReportBuilder

def create_demo_bank() -> Bank:
    """Создать демонстрационный банк с клиентами и счетами."""

    bank = Bank()

    clients = []

    # 5 клиентов
    for i in range(1, 6):
        client = Client(
            client_id=f"FL{i:03d}",
            full_name=f"Client {i}",
            birth_date=f"1990-01-{i:02d}"
        )

        bank.add_client(client)
        clients.append(client)

    # По 2 счета каждому клиенту = 10 счетов
    for client in clients:
        for _ in range(2):
            bank.open_account(
                client_id=client.client_id,
                account_type=PremiumAccount,
                currency=Currency.RUB
            )

    return bank


def create_demo_transactions(account_ids: list[str]) -> list[Transaction]:
    """Создать 40 демонстрационных транзакций."""

    transactions = []

    for i in range(5, 45):
        sender = random.choice(account_ids)

        receiver = random.choice(account_ids)

        while receiver == sender:
            receiver = random.choice(account_ids)

        transaction = Transaction(
            transaction_id=f"TX{i:03d}",
            transaction_type=TransactionType.TRANSFER,
            amount=random.choice([
                10_000,
                25_000,
                50_000,
                100_000,
                350_000,
                700_000,
            ]),
            currency=Currency.RUB,
            sender_account_id=sender,
            receiver_account_id=receiver,
        )

        transactions.append(transaction)

    return transactions


def process_queue(
    queue: TransactionQueue,
    processor: TransactionProcessor
) -> None:
    """Выполнить все транзакции из очереди."""

    while queue.get_pending_count() > 0:
        transaction = queue.get_next_transaction()

        if transaction:
            processor.process_transaction(transaction)


def main() -> None:
    # =========================
    # 1. Создание банка
    # =========================

    bank = create_demo_bank()

    print("\n=== DEMO BANK CREATED ===")
    print(f"Clients: {len(bank.clients)}")
    print(f"Accounts: {len(bank.accounts)}")

    # =========================
    # 2. Создание очереди
    # =========================

    queue = TransactionQueue()
    processor = TransactionProcessor(bank)

    # =========================
    # 3. Получаем счета
    # =========================

    account_ids = list(bank.accounts.keys())

    account_1 = account_ids[0]
    account_2 = account_ids[1]

    # =========================
    # 4. Первая транзакция —
    #    пополнение счета
    # =========================

    deposit = Transaction(
        transaction_id="TX001",
        transaction_type=TransactionType.DEPOSIT,
        amount=100_000,
        currency=Currency.RUB,
        receiver_account_id=account_1,
    )

    queue.add_transaction(deposit)

    # =========================
    # 5. Успешный перевод
    # =========================

    transfer = Transaction(
        transaction_id="TX002",
        transaction_type=TransactionType.TRANSFER,
        amount=50_000,
        currency=Currency.RUB,
        sender_account_id=account_1,
        receiver_account_id=account_2,
    )

    queue.add_transaction(transfer)

    # =========================
    # 6. Ошибочная транзакция —
    #    недостаточно средств
    # =========================

    withdrawal = Transaction(
        transaction_id="TX003",
        transaction_type=TransactionType.WITHDRAWAL,
        amount=999_999,
        currency=Currency.RUB,
        sender_account_id=account_1,
    )

    queue.add_transaction(withdrawal)

    # =========================
    # 7. HIGH RISK транзакция
    # =========================

    suspicious_transfer = Transaction(
        transaction_id="TX004",
        transaction_type=TransactionType.TRANSFER,
        amount=700_000,
        currency=Currency.RUB,
        sender_account_id=account_1,
        receiver_account_id=account_2,
    )

    queue.add_transaction(suspicious_transfer)

    # =========================
    # 8. Обрабатываем очередь
    # =========================

    print("\n=== PROCESSING MANUAL TRANSACTIONS ===")

    process_queue(queue, processor)

    # =========================
    # 9. Создаём ещё 40
    #    автоматических транзакций
    # =========================

    print("\n=== GENERATING 40 TRANSACTIONS ===")

    transactions = create_demo_transactions(account_ids)

    for transaction in transactions:
        queue.add_transaction(transaction)

    # =========================
    # 10. Обрабатываем их
    # =========================

    print("\n=== PROCESSING GENERATED TRANSACTIONS ===")

    process_queue(queue, processor)

    print("\n=== CLIENT ACCOUNTS ===")

    client_id = "FL001"
    accounts = bank.search_accounts(client_id)

    for account in accounts:
        print(
            f"Account: {account['uuid']} | "
            f"Balance: {account['balance']} RUB | "
            f"Status: {account['status']} | "
            f"Type: {account['account_subtype']}"
        )

    print("\n=== TRANSACTION HISTORY ===")

    history = bank.transaction_history.get(client_id, [])

    for transaction in history:
        print(
            f"{transaction.transaction_id} | "
            f"Type: {transaction.transaction_type.value} | "
            f"Amount: {transaction.amount} RUB | "
            f"Status: {transaction.status.value}"
        )

    print("\n=== SUSPICIOUS OPERATIONS ===")

    suspicious_events = processor.audit_log.get_suspicious_events()

    for event in suspicious_events:
        print(
            f"{event.transaction_id} | "
            f"Risk: {event.risk_level.value} | "
            f"Message: {event.message}"
        )

    print("\n=== TOP 3 CLIENTS ===")

    ranking = bank.get_clients_ranking(top_n=3)

    for i, item in enumerate(ranking, start=1):
        print(
            f"{i}. {item['client']} — "
            f"{item['total']:.2f} RUB"
        )


    all_transactions = [
    deposit,
    transfer,
    withdrawal,
    suspicious_transfer,
    *transactions,
    ]

    print("\n=== TRANSACTION STATISTICS ===")
    total = len(all_transactions)

    successful = sum(
        t.status == TransactionStatus.COMPLETED
        for t in all_transactions
    )

    failed = sum(
        t.status == TransactionStatus.FAILED
        for t in all_transactions
    )

    print(f"Total transactions: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    print("\n=== TOTAL BALANCE ===")

    total_balance = bank.get_total_balance()

    print(f"Total balance: {total_balance:.2f} RUB")

    report_builder = ReportBuilder(bank)

    report_builder.export_bank_report_json("bank_report.json")
    report_builder.export_clients_csv("clients_report.csv")

    report_builder.export_risk_report_json(
        processor.audit_log,
        "risk_report.json"
    )

    report_builder.save_charts(
    all_transactions,
    processor.audit_log
    )
        
if __name__ == "__main__":
    main()