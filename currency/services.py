import datetime
from decimal import Decimal

from currency.models import Currency, CurrencyExchangeRate
from currency.providers import get_exchange_rate_data_smart


def get_exchange_rate(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
) -> float:
    if source_currency == exchanged_currency:
        return 1
    exchange_rate: CurrencyExchangeRate | None = None
    try:
        exchange_rate = CurrencyExchangeRate.objects.filter(
            source_currency=source_currency,
            exchanged_currency=exchanged_currency,
            valuation_date=valuation_date,
        ).get()
        exchange_rate_value = exchange_rate.rate_value
    except CurrencyExchangeRate.DoesNotExist:
        exchange_rate_value = get_exchange_rate_data_smart(
            source_currency=source_currency,
            exchanged_currency=exchanged_currency,
            valuation_date=valuation_date,
        )
        CurrencyExchangeRate.objects.update_or_create(
            source_currency=source_currency,
            exchanged_currency=exchanged_currency,
            valuation_date=valuation_date,
            rate_value=Decimal(exchange_rate_value),
        )

    return exchange_rate_value
