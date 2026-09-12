class Asset:
    """Базовый класс для активов"""

    def __init__(self, symbol: str, quantity: float, price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

    def get_value(self) -> float:
        return self.quantity * self.price

    def __str__(self) -> str:
        return f"{self.symbol}: {self.quantity} шт. @ {self.price}"


class Stock(Asset):
    """Акции"""

    def __init__(
        self, symbol: str, quantity: float, price: float, dividend_yield: float = 0.0
    ):
        super().__init__(symbol, quantity, price)
        self.dividend_yield = dividend_yield


class Bond(Asset):
    """Облигации"""

    def __init__(
        self, symbol: str, quantity: float, price: float, coupon_rate: float = 0.0
    ):
        super().__init__(symbol, quantity, price)
        self.coupon_rate = coupon_rate


class ETF(Asset):
    """ETF-фонды"""

    def __init__(
        self, symbol: str, quantity: float, price: float, expense_ratio: float = 0.0
    ):
        super().__init__(symbol, quantity, price)
        self.expense_ratio = expense_ratio
