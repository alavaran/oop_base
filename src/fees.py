from enums import (
    Currency,
    TransactionType,
)
# ============ Fee Calculator ============
class FeeCalculator:
    """Калькулятор комиссий"""

    INTERNAL_TRANSFER_FEE = 0.0  # Бесплатно
    EXTERNAL_TRANSFER_FEE_PERCENT = 0.015  # 1.5%
    EXTERNAL_TRANSFER_MIN_FEE = 50.0  # Минимум 50 RUB
    CURRENCY_CONVERSION_FEE_PERCENT = 0.01  # 1%

    @classmethod
    def calculate_fee(
        cls,
        transaction_type: TransactionType,
        amount: float,
        currency: Currency,
        currency_conversion: bool = False,
    ) -> float:
        """Расчёт комиссии"""
        fee = 0.0

        if transaction_type == TransactionType.EXTERNAL_TRANSFER:
            fee = max(
                amount * cls.EXTERNAL_TRANSFER_FEE_PERCENT,
                cls.EXTERNAL_TRANSFER_MIN_FEE,
            )

        if currency_conversion:
            fee += amount * cls.CURRENCY_CONVERSION_FEE_PERCENT

        return round(fee, 2)