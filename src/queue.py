from transactions import (
    Transaction
)
from datetime import datetime, timedelta
from typing import Optional
import heapq
from enums import (
    TransactionStatus
)
from exceptions import (
    InvalidOperationError,
)

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

        while self._queue:
            _, _, transaction = heapq.heappop(self._queue)

            # Если транзакция отменена — пропускаем её
            if transaction.status == TransactionStatus.CANCELLED:
                continue

            # Если транзакция не отменена — начинаем обработку
            transaction.status = TransactionStatus.PROCESSING
            return transaction

        return None

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
            return True
        except InvalidOperationError:
            return False

    def get_pending_count(self) -> int:
        """Количество ожидающих транзакций"""
        return len(self._queue) + len(self._scheduled)

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Получить транзакцию по ID"""
        return self._transactions.get(transaction_id)

