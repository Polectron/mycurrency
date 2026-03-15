import datetime
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status
from django.test import TestCase

from currency.models import Currency, CurrencyExchangeRate, CurrencyProvider
from currency.providers import (
    get_exchange_rate_data_smart,
    FailingMockCurrencyClient,
    MockCurrencyClient,
)
from currency.services import get_exchange_rate


class CurrencyViewSetTestCase(APITestCase):
    """Tests for CurrencyViewSet"""

    def setUp(self):
        """Set up test data"""
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")

    def test_list_currencies(self):
        """Test listing all currencies"""
        response = self.client.get("/v1/currencies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_currency(self):
        """Test retrieving a single currency"""
        response = self.client.get(f"/v1/currencies/{self.usd.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "USD")
        self.assertEqual(response.data["name"], "US Dollar")
        self.assertEqual(response.data["symbol"], "$")


class CurrencyRatesViewTestCase(APITestCase):
    """Tests for CurrencyRatesView"""

    def setUp(self):
        """Set up test data"""
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        self.gbp = Currency.objects.create(code="GBP", name="British Pound", symbol="£")

        # Create some exchange rates
        CurrencyExchangeRate.objects.create(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=datetime.date(2026, 3, 10),
            rate_value=Decimal("0.92"),
        )
        CurrencyExchangeRate.objects.create(
            source_currency=self.usd,
            exchanged_currency=self.gbp,
            valuation_date=datetime.date(2026, 3, 12),
            rate_value=Decimal("0.78"),
        )

    def test_get_currency_rates_with_params(self):
        """Test getting currency rates with all required parameters"""
        response = self.client.get(
            "/v1/rates/",
            {
                "source_currency": "USD",
                "date_from": "2026-03-01",
                "date_to": "2026-03-15",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Verify the rates are ordered correctly (most recent first)
        self.assertEqual(response.data[0]["valuation_date"], "2026-03-12")
        self.assertEqual(response.data[1]["valuation_date"], "2026-03-10")


class CurrencyConvertViewTestCase(APITestCase):
    """Tests for CurrencyConvertView"""

    def setUp(self):
        """Set up test data"""
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")

        # Create an exchange rate for today
        CurrencyExchangeRate.objects.create(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=datetime.date.today(),
            rate_value=Decimal("0.92"),
        )

    def test_convert_currency_success(self):
        """Test successful currency conversion"""
        response = self.client.get(
            "/v1/convert/",
            {
                "source_currency": "USD",
                "amount": "100",
                "exchanged_currency": "EUR",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_currency"], "USD")
        self.assertEqual(response.data["exchanged_currency"], "EUR")
        self.assertEqual(response.data["original_amount"], Decimal("100"))
        self.assertEqual(response.data["rate_value"], Decimal("0.92"))

    def test_convert_same_currency(self):
        """Test currency conversion with same source and target currency"""
        response = self.client.get(
            "/v1/convert/",
            {
                "source_currency": "USD",
                "amount": "50",
                "exchanged_currency": "USD",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["original_amount"], Decimal("50"))


class ProviderFailoverTestCase(TestCase):
    """Tests for provider failover logic in get_exchange_rate_data_smart"""

    def setUp(self):
        """Set up test data"""
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")

        # Create two providers: one that always fails (higher priority), one that works (lower priority)
        self.failing_provider = CurrencyProvider.objects.create(
            name="FailingMockCurrencyClient",
            active=True,
            priority=10.0,
        )
        self.working_provider = CurrencyProvider.objects.create(
            name="MockCurrencyClient",
            active=True,
            priority=5.0,
        )

    @patch.object(
        MockCurrencyClient,
        "get_exchange_rate_data",
        wraps=MockCurrencyClient.get_exchange_rate_data,
    )
    @patch.object(
        FailingMockCurrencyClient,
        "get_exchange_rate_data",
        wraps=FailingMockCurrencyClient.get_exchange_rate_data,
    )
    def test_failover_to_second_provider(
        self, mock_failing_client, mock_working_client
    ):
        """Test that failover works when FailingMockCurrencyClient fails and MockCurrencyClient succeeds"""
        # Call the smart function - FailingMockCurrencyClient should fail, then MockCurrencyClient should succeed
        rate = get_exchange_rate_data_smart(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=datetime.date.today(),
        )

        # Should get a random value from MockCurrencyClient (between 0 and 1)
        # This proves the failover happened from FailingMockCurrencyClient to MockCurrencyClient
        self.assertIsInstance(rate, float)
        self.assertGreaterEqual(rate, 0)
        self.assertLessEqual(rate, 1)

        # Verify that FailingMockCurrencyClient was called first and actually raised an exception
        mock_failing_client.assert_called_once()

        # Verify that MockCurrencyClient was called second (after failover)
        mock_working_client.assert_called_once()

    @patch.object(
        MockCurrencyClient,
        "get_exchange_rate_data",
        wraps=MockCurrencyClient.get_exchange_rate_data,
    )
    @patch.object(
        FailingMockCurrencyClient,
        "get_exchange_rate_data",
        wraps=FailingMockCurrencyClient.get_exchange_rate_data,
    )
    def test_only_working_provider_active(
        self, mock_failing_client, mock_working_client
    ):
        """Test that when only the working provider is active, it's used directly"""
        # Deactivate the failing provider
        self.failing_provider.active = False
        self.failing_provider.save()

        # Call the smart function
        rate = get_exchange_rate_data_smart(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=datetime.date.today(),
        )

        # Should get a random value from MockCurrencyClient
        self.assertIsInstance(rate, float)
        self.assertGreaterEqual(rate, 0)
        self.assertLessEqual(rate, 1)

        # Verify that only MockCurrencyClient was called (FailingMockCurrencyClient is inactive)
        mock_working_client.assert_called_once()
        mock_failing_client.assert_not_called()

    @patch.object(
        FailingMockCurrencyClient,
        "get_exchange_rate_data",
        wraps=FailingMockCurrencyClient.get_exchange_rate_data,
    )
    def test_all_providers_fail(self, mock_failing_client):
        """Test that exception is raised when all providers fail"""
        # Deactivate the working provider so only FailingMockCurrencyClient is active
        self.working_provider.active = False
        self.working_provider.save()

        with self.assertRaises(ValueError) as context:
            get_exchange_rate_data_smart(
                source_currency=self.usd,
                exchanged_currency=self.eur,
                valuation_date=datetime.date.today(),
            )

        self.assertIn("Couldn't fetch an exchange rate", str(context.exception))

        # Verify that FailingMockCurrencyClient was called and actually failed
        mock_failing_client.assert_called_once()


class ExchangeRateServiceTestCase(TestCase):
    """Tests for get_exchange_rate service function"""

    def setUp(self):
        """Set up test data"""
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        self.gbp = Currency.objects.create(code="GBP", name="British Pound", symbol="£")
        self.valuation_date = datetime.date(2026, 3, 15)

    @patch("currency.services.get_exchange_rate_data_smart")
    def test_same_currency_returns_one(self, mock_get_rate_smart):
        """Test that converting same currency returns 1 without calling external services"""
        rate = get_exchange_rate(
            source_currency=self.usd,
            exchanged_currency=self.usd,
            valuation_date=self.valuation_date,
        )

        # Should return 1 for same currency
        self.assertEqual(rate, 1)

        # Should NOT call get_exchange_rate_data_smart
        mock_get_rate_smart.assert_not_called()

        # Should NOT create a database entry
        self.assertEqual(CurrencyExchangeRate.objects.count(), 0)

    @patch("currency.services.get_exchange_rate_data_smart")
    def test_existing_exchange_rate(self, mock_get_rate_smart):
        """Test that existing exchange rate is retrieved from database without calling external services"""
        # Create an existing exchange rate in the database
        CurrencyExchangeRate.objects.create(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=self.valuation_date,
            rate_value=Decimal("0.85"),
        )

        rate = get_exchange_rate(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=self.valuation_date,
        )

        # Should return the existing rate
        self.assertEqual(rate, Decimal("0.85"))

        # Should NOT call get_exchange_rate_data_smart since rate exists in DB
        mock_get_rate_smart.assert_not_called()

        # Should still have only one exchange rate in DB
        self.assertEqual(CurrencyExchangeRate.objects.count(), 1)

    @patch("currency.services.get_exchange_rate_data_smart")
    def test_non_existing_exchange_rate(self, mock_get_rate_smart):
        """Test that non-existing exchange rate is fetched and stored"""
        # Mock the external service to return a rate
        mock_get_rate_smart.return_value = 0.92

        # Verify no exchange rate exists initially
        self.assertEqual(CurrencyExchangeRate.objects.count(), 0)

        rate = get_exchange_rate(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=self.valuation_date,
        )

        # Should return the fetched rate (as returned from get_exchange_rate_data_smart)
        self.assertEqual(rate, 0.92)

        # Should have called get_exchange_rate_data_smart to fetch the rate
        mock_get_rate_smart.assert_called_once_with(
            source_currency=self.usd,
            exchanged_currency=self.eur,
            valuation_date=self.valuation_date,
        )

        # Should have stored the new exchange rate in the database
        self.assertEqual(CurrencyExchangeRate.objects.count(), 1)
