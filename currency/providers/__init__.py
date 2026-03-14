import abc
import datetime

from mycurrency.core.models import Currency


class CurrencyClient(abc.ABC):
    @abc.abstractmethod
    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        raise NotImplementedError


def get_exchange_rate_data(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
    provider: CurrencyClient,
) -> float:
    return provider.get_exchange_rate_data(source_currency, exchanged_currency, valuation_date)

    
