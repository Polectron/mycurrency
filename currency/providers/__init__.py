import abc
import datetime
import random

import httpx
import requests
from django.conf import settings

from currency.models import Currency, CurrencyExchangeRate, CurrencyProvider


class CurrencyClient(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    async def get_exchange_rate_data_async(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        raise NotImplementedError


class CurrencyBeaconCurrencyClient(CurrencyClient):
    @staticmethod
    def build_query(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> tuple[str, dict[str, str]]:
        url = "https://api.currencybeacon.com/v1/historical"
        params = {
            "api_key": settings.CURRENCY_BEACON_API_KEY,
            "base": source_currency.code,
            "symbols": exchanged_currency.code,
        }
        if valuation_date == datetime.date.today():
            url = "https://api.currencybeacon.com/v1/latest"
            params["date"] = valuation_date.isoformat()
        return url, params

    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        url, params = CurrencyBeaconCurrencyClient.build_query(source_currency, exchanged_currency, valuation_date)
        response = requests.get(
            url,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]["rates"][exchanged_currency.code]

    @staticmethod
    async def get_exchange_rate_data_async(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        async with httpx.AsyncClient() as client:
            url, params = CurrencyBeaconCurrencyClient.build_query(source_currency, exchanged_currency, valuation_date)
            response = await client.get(
                url,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]["rates"][exchanged_currency.code]


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


PROVIDER_CLIENTS: dict[str, type[CurrencyClient]] = {
    "CurrencyBeacon": CurrencyBeaconCurrencyClient
}


def _get_provider_client(name: str) -> CurrencyClient:
    """Load provider client class by name"""
    provider_class = PROVIDER_CLIENTS.get(name)
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


async def get_exchange_rate_data_async(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
    provider: CurrencyProvider,
) -> float:
    client = _get_provider_client(provider.name)
    return await client.get_exchange_rate_data_async(
        source_currency, exchanged_currency, valuation_date
    )


def get_exchange_rate_data_smart(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
) -> float:
    providers = CurrencyProvider.objects.filter(active=True).order_by("-priority").all()
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
