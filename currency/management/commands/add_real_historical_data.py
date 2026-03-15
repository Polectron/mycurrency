import asyncio
import datetime

from django.core.management.base import BaseCommand
from currency.models import Currency, CurrencyExchangeRate, CurrencyProvider
from currency.providers import get_exchange_rate_data_async


async def setup_workers(
    n_workers: int,
    from_date: datetime.date,
    to_date: datetime.date,
    historical_data: list[CurrencyExchangeRate],
    provider: CurrencyProvider,
    currencies: list[Currency]
):
    # Generate list of dates from from_date to to_date
    valuation_dates = []
    current_date = from_date
    while current_date <= to_date:
        valuation_dates.append(current_date)
        current_date += datetime.timedelta(days=1)

    lock = asyncio.Lock()
    queue = asyncio.Queue()

    for c1 in currencies:
        for c2 in currencies:
            for valuation_date in valuation_dates:
                if c1 != c2:
                    queue.put_nowait((c1, c2, valuation_date))

    workers = [
        asyncio.create_task(get_data_worker(historical_data, provider, queue, lock))
        for _ in range(n_workers)
    ]
    await queue.join()

    for worker in workers:
        worker.cancel()

    await asyncio.gather(*workers, return_exceptions=True)


async def get_data_worker(
    historical_data: list[CurrencyExchangeRate],
    provider: CurrencyProvider,
    queue: asyncio.Queue,
    lock: asyncio.Lock,
):
    while True:
        try:
            source_currency, exchanged_currency, valuation_date = await queue.get()
            exchange_rate = await get_exchange_rate_data_async(
                source_currency, exchanged_currency, valuation_date, provider
            )
            async with lock:
                print(f"Storing data for {source_currency} {exchanged_currency} to {valuation_date} -> {exchange_rate}")
                historical_data.append(
                    CurrencyExchangeRate(
                        source_currency=source_currency,
                        exchanged_currency=exchanged_currency,
                        valuation_date=valuation_date,
                        rate_value=exchange_rate,
                    )
                )
        except Exception as e:
            print(f"Error processing {source_currency} -> {exchanged_currency} on {valuation_date}: {e}")
        finally:
            queue.task_done()


class Command(BaseCommand):
    help = "Fills the database with historical data from the selected provider"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from_date", type=lambda x: datetime.date.fromisoformat(x), required=True
        )
        parser.add_argument(
            "--to_date", type=lambda x: datetime.date.fromisoformat(x), required=True
        )
        parser.add_argument("--provider", type=str, required=True)
        parser.add_argument("--workers", type=int, default=10)

    def handle(self, *args, **options):
        historical_data = []

        from_date = options["from_date"]
        to_date = options["to_date"]
        provider = options["provider"]
        n_workers = options["workers"]

        provider = CurrencyProvider.objects.filter(name=provider).get()
        currencies = list(Currency.objects.all())

        asyncio.run(
            setup_workers(n_workers, from_date, to_date, historical_data, provider, currencies)
        )

        CurrencyExchangeRate.objects.bulk_create(
            historical_data,
            update_conflicts=True,
            update_fields=["rate_value"],
            unique_fields=["source_currency", "exchanged_currency", "valuation_date"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully inserted historical data: {len(historical_data)} rows"
            )
        )
