import datetime

from multiprocessing.pool import ThreadPool
import threading
from django.core.management.base import BaseCommand
from currency.models import Currency, CurrencyExchangeRate
from currency.providers.mock import MockCurrencyClient


def get_data(
    source_currency: Currency,
    exchanged_currency: Currency,
    valuation_date: datetime.date,
    historical_data: list[CurrencyExchangeRate],
    lock: threading.Lock,
):
    exchange_rate = MockCurrencyClient.get_exchange_rate_data(
        source_currency, exchanged_currency, valuation_date
    )
    with lock:
        historical_data.append(
            CurrencyExchangeRate(
                source_currency=source_currency,
                exchanged_currency=exchanged_currency,
                valuation_date=valuation_date,
                rate_value=exchange_rate,
            )
        )


class Command(BaseCommand):
    help = "Fills the database with mock historical data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from_date", type=lambda x: datetime.date.fromisoformat(x), required=True
        )
        parser.add_argument(
            "--to_date", type=lambda x: datetime.date.fromisoformat(x), required=True
        )
        parser.add_argument("--workers", type=int, default=4)

    def handle(self, *args, **options):
        historical_data = []
        lock = threading.Lock()

        from_date = options["from_date"]
        to_date = options["to_date"]

        # Generate list of dates from from_date to to_date
        valuation_dates = []
        current_date = from_date
        while current_date <= to_date:
            valuation_dates.append(current_date)
            current_date += datetime.timedelta(days=1)

        with ThreadPool(processes=options["workers"]) as pool:
            pool.starmap(
                get_data,
                (
                    (c1, c2, valuation_date, historical_data, lock)
                    for c1 in Currency.objects.all()
                    for c2 in Currency.objects.all()
                    for valuation_date in valuation_dates
                    if c1 != c2
                ),
            )
        
        CurrencyExchangeRate.objects.bulk_create(historical_data)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully inserted mock historical data: {len(historical_data)} rows")
        )
