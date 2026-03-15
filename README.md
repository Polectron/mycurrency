# mycurrency
My Currency project for Backbase

A REST API service for converting between different currencies at current valuations and checking historical rates

## .env file
A .env file is required with the following variables

|name | description   | required
|-----|---------------|----------
| CURRENCY_BEACON_API_KEY | API key for currencybeacon.com API service | true

## Initial setup
- Make sure to have [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed
- Run `uv sync` to setup the virtual environment with all necessary dependencies
- Setup vscode venv or append  `uv run` to all commands eg: `uv run python manage.py runserver`
- Start up database with `python manage.py migrate` (will create a db.sqlite3 database file)
- Initial data setup with `python manage.py loaddata initial_data.json`
    - Adds superuser
        - User: admin
        - Password: admin123
    - Adds initial currencies: EUR, CHF, USD, GBP
    - Registers default currency exchange provider CurrencyBeacon
- To load historical exchange data:
    - `python manage.py add_test_historical_data --from_date YYYY-MM-DD --to_date YYYY-MM-DD` for test historical data
    - `python manage.py add_real_historical_data --from_date YYYY-MM-DD --to_date YYYY-MM-DD --provider CurrencyBeacon` for real historical data
        - WARNING: consumes CurrencyBeacon requests and is much slower as it runs real API requests
- To startup server: `python manage.py runserver`
    - Server will be available at http://localhost:8000

## Testing

Run `python manage.py test` to run the tests

## Concurrency vs Parallelism

Python only provides ture parallelism on multiprocessing, threads (for now) are limited by the GIL so are actually using concurrency.

For this project, concurrency is the optimal choice:
- Exchange rate API calls are IO bound, they have to wait on network responses
- asyncio allows efficient concurrent IO without the overhead of multiple processes

**Implementation:**
- **Real historical data** Uses asyncio with concurrent workers to fetch data from CurrencyBeacon API efficiently
- **Test historical data** Uses as thread pool for simplicity, as mock data generation is trivial and doesn't require the async complexities

True parallelism with multiprocessing would be appropriate for CPU-bound tasks like complex calculations.

## Potential improvements

- Celery / huey based crontab job for fetching up to date exchange rates for registered currencies.
- Implement better authentication methods to the API like oauth2 or at least the simple token authentication provided by DRF
- Add API limits like requests per second
- Add a circuit breaker for the providers when failuers are detected