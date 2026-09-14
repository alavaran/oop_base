from dataclasses import dataclass, field
from datetime import datetime
from enums import RiskLevel


@dataclass
class AuditEvent:
    transaction_id: str
    risk_level: RiskLevel
    message: str
    failure_reason: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

class AuditLog:
    def __init__(self):
        self.events = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)

    def filter_by_risk(self, risk_level: RiskLevel) -> list[AuditEvent]:
        return [
            event
            for event in self.events
            if event.risk_level == risk_level
        ]
    
    def save_to_file(self, filename: str) -> None:
        with open(filename, "a", encoding="utf-8") as file:
            for event in self.events:
                file.write(
                    f"{event.created_at} | "
                    f"{event.transaction_id} | "
                    f"{event.risk_level.value} | "
                    f"{event.message}\n"
                )

    def error_statistics(self) -> dict[str, int]:
        statistics = {}

        for event in self.events:
            if event.failure_reason:
                reason = event.failure_reason
                statistics[reason] = statistics.get(reason, 0) + 1

        return statistics

    def get_suspicious_events(self) -> list[AuditEvent]:
        return [
            event
            for event in self.events
            if event.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
        ]

    def get_risk_statistics(self) -> dict[str, int]:
        statistics = {
            "low": 0,
            "medium": 0,
            "high": 0
        }

        for event in self.events:
            statistics[event.risk_level.value] += 1

        return statistics