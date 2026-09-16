import json
import csv
import matplotlib.pyplot as plt
from currency import CurrencyConverter
from enums import Currency

from bank import Bank


class ReportBuilder:
    def __init__(self, bank: Bank):
        self.bank = bank

    def _get_balance_in_currency(
        self,
        account,
        target_currency: Currency
    ) -> float:
        return CurrencyConverter.convert(
            account.balance,
            account.currency,
            target_currency
        )
    
    def generate_client_report(self, client_id: str) -> str:
        client = self.bank.clients.get(client_id)

        if not client:
            return f"Client {client_id} not found"

        accounts = client.accounts

        total_balance = sum(
            self._get_balance_in_currency(
                self.bank.accounts[account_id],
                Currency.RUB
            )
            for account_id in accounts
        )

        report = []
        report.append("=== CLIENT REPORT ===")
        report.append(f"Client ID: {client.client_id}")
        report.append(f"Name: {client.full_name}")
        report.append(f"Accounts: {len(accounts)}")
        report.append(f"Total balance: {total_balance:.2f}")

        return "\n".join(report)

    def generate_bank_report(self) -> str:
        report = []
        report.append("=== BANK REPORT ===")

        total_clients = len(self.bank.clients)
        total_accounts = len(self.bank.accounts)
        total_balance = sum(
            self._get_balance_in_currency(
                account,
                Currency.RUB
            )
            for account in self.bank.accounts.values()
        )

        report.append(f"Total clients: {total_clients}")
        report.append(f"Total accounts: {total_accounts}")
        report.append(f"Total balance: {total_balance:.2f}")

        report.append("")
        report.append("=== CLIENTS ===")

        for client in self.bank.clients.values():

            client_balance = sum(
                self._get_balance_in_currency(
                    self.bank.accounts[account_id],
                    Currency.RUB
                )
                for account_id in client.accounts
            )

            report.append(
                f"{client.client_id} | "
                f"{client.full_name} | "
                f"Accounts: {len(client.accounts)} | "
                f"Balance: {client_balance:.2f}"
            )

        return "\n".join(report)

    def generate_risk_report(self, audit_log) -> str:
        statistics = audit_log.get_risk_statistics()
        suspicious_events = audit_log.get_suspicious_events()

        report = []

        report.append("=== RISK REPORT ===")
        report.append("")
        report.append("Risk statistics:")
        report.append(f"LOW: {statistics['low']}")
        report.append(f"MEDIUM: {statistics['medium']}")
        report.append(f"HIGH: {statistics['high']}")

        report.append("")
        report.append("=== SUSPICIOUS OPERATIONS ===")

        if not suspicious_events:
            report.append("No suspicious operations")
        else:
            for event in suspicious_events:
                report.append(
                    f"{event.transaction_id} | "
                    f"Risk: {event.risk_level.value} | "
                    f"{event.message}"
                )

        return "\n".join(report)

    def export_bank_report_json(self, filename: str) -> None:
        total_balance = sum(
            self._get_balance_in_currency(
                account,
                Currency.RUB
            )
            for account in self.bank.accounts.values()
        )

        report = {
            "total_clients": len(self.bank.clients),
            "total_accounts": len(self.bank.accounts),
            "total_balance": total_balance,
            "clients": []
        }

        for client in self.bank.clients.values():

            client_balance = sum(
                self._get_balance_in_currency(
                    self.bank.accounts[account_id],
                    Currency.RUB
                )
                for account_id in client.accounts
            )

            report["clients"].append({
                "client_id": client.client_id,
                "name": client.full_name,
                "accounts": len(client.accounts),
                "balance": client_balance
            })

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                ensure_ascii=False,
                indent=4
            )

    def export_clients_csv(self, filename: str) -> None:
        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "client_id",
                "name",
                "accounts",
                "balance"
            ])

            for client in self.bank.clients.values():

                client_balance = sum(
                    self._get_balance_in_currency(
                        self.bank.accounts[account_id],
                        Currency.RUB
                    )
                    for account_id in client.accounts
                )

                writer.writerow([
                    client.client_id,
                    client.full_name,
                    len(client.accounts),
                    client_balance
                ])

    def export_risk_report_json(self, audit_log, filename: str) -> None:
        statistics = audit_log.get_risk_statistics()
        suspicious_events = audit_log.get_suspicious_events()

        report = {
            "statistics": statistics,
            "suspicious_operations": []
        }

        for event in suspicious_events:
            report["suspicious_operations"].append({
                "transaction_id": event.transaction_id,
                "risk_level": event.risk_level.value,
                "message": event.message,
                "failure_reason": event.failure_reason
            })

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                ensure_ascii=False,
                indent=4
            )

    def plot_client_balances(self, filename: str) -> None:
        clients = []
        balances = []

        for client in self.bank.clients.values():
            balance = sum(
                self._get_balance_in_currency(
                    self.bank.accounts[account_id],
                    Currency.RUB
                )
                for account_id in client.accounts
            )

            clients.append(client.client_id)
            balances.append(balance)
        plt.figure(figsize=(10, 6))

        plt.bar(clients, balances)

        plt.title("Client balances")
        plt.xlabel("Client")
        plt.ylabel("Balance")

        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def plot_risk_distribution(self, audit_log, filename: str) -> None:
        statistics = audit_log.get_risk_statistics()

        labels = ["LOW", "MEDIUM", "HIGH"]
        values = [
            statistics["low"],
            statistics["medium"],
            statistics["high"]
        ]

        plt.figure(figsize=(8, 8))

        plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%"
        )

        plt.title("Risk distribution")

        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def plot_balance_history(self, transactions, filename: str) -> None:
        balance = 0
        balances = [balance]

        for transaction in transactions:
            if transaction.status.value != "completed":
                continue

            amount = CurrencyConverter.convert(
                transaction.get_total_amount(),
                transaction.currency,
                Currency.RUB
            )

            if transaction.transaction_type.value == "deposit":
                balance += amount

            elif transaction.transaction_type.value in (
                "withdrawal",
                "transfer",
                "external_transfer"
            ):
                balance -= amount

            balances.append(balance)

        plt.figure(figsize=(10, 6))

        plt.plot(
            range(len(balances)),
            balances,
            marker="o"
        )

        plt.title("Balance movement")
        plt.xlabel("Transaction")
        plt.ylabel("Balance")

        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def export_to_json(self, data: dict, filename: str) -> None:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

    def export_to_csv(
        self,
        headers: list[str],
        rows: list[list],
        filename: str
    ) -> None:
        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow(headers)
            writer.writerows(rows)

    def save_charts(self, transactions, audit_log) -> None:
        self.plot_client_balances(
            "client_balances.png"
        )

        self.plot_risk_distribution(
            audit_log,
            "risk_distribution.png"
        )

        self.plot_balance_history(
            transactions,
            "balance_history.png"
        )