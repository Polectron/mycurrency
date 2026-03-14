import datetime

import requests

from currency.providers import CurrencyClient
from currency.models import Currency


class CurrencyBeaconCurrencyClient(CurrencyClient):
    @staticmethod
    def get_exchange_rate_data(
        source_currency: Currency,
        exchanged_currency: Currency,
        valuation_date: datetime.date,
    ) -> float:
        response = requests.get(
            "https://api.currencybeacon.com/v1/historical",
            params={"api_key": "YOUR_KEY", "base": source_currency.code, "symbols": exchanged_currency.code, "date": valuation_date.isoformat()},
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]["rates"][exchanged_currency.code]
