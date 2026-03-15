# mycurrency
My Currency project for Backbase

A REST API service for converting between different currencies at current valuations and checking historical rates

## .env file
A .env file is required with the following variables

|name | description   | required
|-----|---------------|----------
| CURRENCY_BEACON_API_KEY | API key for currencybeacon.com API service | true

## Initial setup
- Start up database with `python manage.py migrate` (will create a db.sqlite3 database file)
- Initial data setup with `python manage.py loaddata initial_data.json`
    - Adds superuser
        - User: admin
        - Password: admin123
    - Adds initial currencies: EUR, CHF, USD, GBP
    - Registers default currency exchange provider CurrencyBeacon
- To load historical exchange data:
    - `python manage.py add_test_historical_data --from_date YYYY-MM-DD --to_date YYYY-MM-DD` for test historical data
    - `python manage.py add_test_historical_data --from_date YYYY-MM-DD --to_date YYYY-MM-DD --provider CurrencyBeacon` for real historical data
        - WARNING: consumes CurrencyBeacon requests and is much slower as it runs real API requests
- To startup server: `python manage.py runserver`
    - Server will be available at http://localhost:8000