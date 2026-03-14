import datetime
import random

from mycurrency.core.currency_clients import CurrencyClient
from mycurrency.core.models import Currency


class MockCurrencyClient(CurrencyClient):
    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        return random.random()