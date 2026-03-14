import datetime

import httpx
import requests

from currency.providers import CurrencyClient
from currency.models import Currency
from django.conf import settings


class CurrencyBeaconCurrencyClient(CurrencyClient):
    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        response = requests.get(
            "https://api.currencybeacon.com/v1/historical",
            params={
                "api_key": settings.CURRENCY_BEACON_API_KEY,
                "base": source_currency.code,
                "symbols": exchanged_currency.code,
                "date": valuation_date.isoformat(),
            },
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
            response = await client.get(
                "https://api.currencybeacon.com/v1/historical",
                params={
                    "api_key": settings.CURRENCY_BEACON_API_KEY,
                    "base": source_currency.code,
                    "symbols": exchanged_currency.code,
                    "date": valuation_date.isoformat(),
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]["rates"][exchanged_currency.code]
