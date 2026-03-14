import datetime
import random

from currency.providers import CurrencyClient
from currency.models import Currency


class MockCurrencyClient(CurrencyClient):
    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        return random.random()
    
    @staticmethod
    async def get_exchange_rate_data_async(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        # makes no sense to have an async method
        # for just returning the result of a sync function call
        raise NotImplementedError