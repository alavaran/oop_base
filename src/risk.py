from enums import RiskLevel, TransactionType, TransactionStatus
from transactions import Transaction
from datetime import timedelta


class RiskAnalyzer:
    def __init__(self, bank):
        self.bank = bank

    def analyze(self, transaction: Transaction) -> RiskLevel:
        account_id = transaction.sender_account_id

        if account_id is None:
            return RiskLevel.LOW

        client_id = self.bank.account_to_client.get(account_id)

        if client_id is None:
            return RiskLevel.LOW

        history = self.bank.transaction_history.get(client_id, [])

        recent_operations = []

        for operation in history:
            time_diff = transaction.created_at - operation.created_at

            if time_diff > timedelta(hours=0) and time_diff <= timedelta(hours=1):
                recent_operations.append(operation)

        if transaction.amount > 600_000:
            return RiskLevel.HIGH

        if transaction.created_at.hour < 5:
            return RiskLevel.HIGH

        if transaction.amount > 300_000:
            return RiskLevel.MEDIUM

        if len(recent_operations) > 5:
            return RiskLevel.MEDIUM

        if transaction.transaction_type == TransactionType.TRANSFER:
            previous_receivers = {
                operation.receiver_account_id
                for operation in history
                if operation.transaction_type == TransactionType.TRANSFER
            }

            if transaction.receiver_account_id not in previous_receivers:
                return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def get_client_risk(self, client_id: str) -> RiskLevel:
        history = self.bank.transaction_history.get(client_id, [])

        if not history:
            return RiskLevel.LOW

        risk_levels = []

        for transaction in history:
            risk_levels.append(self.analyze(transaction))

        if RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH

        if RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def get_client_report(self, client_id: str) -> dict:
        history = self.bank.transaction_history.get(client_id, [])

        high_count = 0
        medium_count = 0
        low_count = 0

        total_amount = 0
        successful_count = 0
        failed_count = 0

        suspicious_transactions = []

        for transaction in history:
            total_amount += transaction.amount

            if transaction.status == TransactionStatus.COMPLETED:
                successful_count += 1
            elif transaction.status == TransactionStatus.FAILED:
                failed_count += 1

            risk_level = self.analyze(transaction)

            if risk_level == RiskLevel.HIGH:
                high_count += 1
                suspicious_transactions.append(transaction.transaction_id)

            elif risk_level == RiskLevel.MEDIUM:
                medium_count += 1

            else:
                low_count += 1

        return {
            "client_id": client_id,
            "total_transactions": len(history),
            "total_amount": total_amount,
            "successful_transactions": successful_count,
            "failed_transactions": failed_count,
            "low_risk_transactions": low_count,
            "medium_risk_transactions": medium_count,
            "high_risk_transactions": high_count,
            "suspicious_transactions": suspicious_transactions,
            "risk_level": self.get_client_risk(client_id)
        }