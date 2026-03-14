import abc
import datetime

from currency.models import Currency, CurrencyProvider
from currency.providers.currency_beacon import CurrencyBeaconCurrencyClient


class CurrencyClient(abc.ABC):
    @abc.abstractmethod
    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    @staticmethod
    async def get_exchange_rate_data_async(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        raise NotImplementedError


def _get_provider_client(name: str) -> CurrencyClient:
    """Load provider client class by name"""
    provider_class = CLIENTS.get(name)
    if not provider_class:
        raise ValueError(f"Provider client {name} not found in registry")
    return provider_class()


def get_exchange_rate_data(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
    provider: CurrencyProvider,
) -> float:
    client = _get_provider_client(provider.name)
    return client.get_exchange_rate_data(
        source_currency, exchanged_currency, valuation_date
    )


CLIENTS = {"CurrencyBeacon": CurrencyBeaconCurrencyClient}


def get_exchange_rate_data_smart(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
) -> float:
    providers = CurrencyProvider.objects.filter(active=True).order_by("-priority").get()
    exchange_rate: float | None = None
    for provider in providers:
        try:
            exchange_rate = get_exchange_rate_data(
                source_currency, exchanged_currency, valuation_date, provider
            )
            return exchange_rate
        except Exception:
            continue
    raise ValueError("Couldn't fetch an exchange rate")
