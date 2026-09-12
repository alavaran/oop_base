from enums import (
    Currency
)
# ============ Currency Converter ============
class CurrencyConverter:
    """Конвертер валют с курсами"""

    # Упрощённые курсы относительно RUB
    RATES = {
        Currency.RUB: 1.0,
        Currency.USD: 95.0,
        Currency.EUR: 105.0,
        Currency.KZT: 0.21,
        Currency.CNY: 13.5,
    }

    @classmethod
    def convert(
        cls, amount: float, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Конвертация между валютами"""
        if from_currency == to_currency:
            return amount

        # Конвертируем через RUB
        amount_in_rub = amount * cls.RATES[from_currency]
        result = amount_in_rub / cls.RATES[to_currency]
        return round(result, 2)

    @classmethod
    def get_rate(cls, from_currency: Currency, to_currency: Currency) -> float:
        """Получить курс конвертации"""
        return cls.RATES[from_currency] / cls.RATES[to_currency]

