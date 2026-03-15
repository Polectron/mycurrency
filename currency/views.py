import datetime
from decimal import Decimal

from django.forms import ValidationError
from rest_framework import generics, permissions, viewsets, views
from rest_framework.response import Response
from rest_framework.request import Request

from currency.models import Currency, CurrencyExchangeRate
from currency.serializers import CurrencySerializer, CurrencyExchangeRateSerializer
from currency.services import get_exchange_rate


# Currency rates list Service to retrieve a List of currency rates for a specific time period
# - source_currency
# - date from
# - date to
# A time series list of rate values for each available Currency
class CurrencyRatesView(generics.ListAPIView):
    serializer_class = CurrencyExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):  # type: ignore
        """
        Return a list of currency rates.
        """
        queryset = CurrencyExchangeRate.objects.all()
        source_currency_code = self.request.query_params.get("source_currency")  # type: ignore
        date_from = self.request.query_params.get("date_from")  # type: ignore
        date_to = self.request.query_params.get("date_to")  # type: ignore

        missing = []
        if not source_currency_code:
            missing.append("source_currency")
        if not date_from:
            missing.append("date_from")
        if not date_to:
            missing.append("date_to")

        if missing:
            raise ValidationError(
                {field: "This parameter is required." for field in missing}
            )

        currency = Currency.objects.filter(code=source_currency_code).get()

        queryset = queryset.filter(source_currency=currency.id)
        queryset = queryset.filter(valuation_date__gte=date_from)
        queryset = queryset.filter(valuation_date__lte=date_to)

        return queryset.order_by("-valuation_date")


# Convert amount
# Service that calculates (latest) amount in a currency exchanged into a different currency (currency converter)
# - source_currency
# - amount
# - exchanged_currency
# An object containing at least the rate value between source and exchange currencies.
class CurrencyConvertView(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request: Request, format=None):
        """
        Return currency conversion.
        """

        source_currency_code = request.query_params.get("source_currency")
        try:
            amount = request.query_params.get("amount")
            if amount is None:
                return Response({"error": "Amount parameter not provided"}, status=422)
            amount = Decimal(amount)
        except (TypeError, ValueError):
            return Response({"error": "Invalid amount parameter"}, status=422)
        exchanged_currency_code = request.query_params.get("exchanged_currency")

        source_currency = Currency.objects.filter(code=source_currency_code).get()
        exchanged_currency = Currency.objects.filter(code=exchanged_currency_code).get()
        valuation_date = datetime.date.today()

        exchange_rate_value = get_exchange_rate(source_currency, exchanged_currency, valuation_date, amount)

        return Response(
            {
                "source_currency": source_currency_code,
                "original_amount": amount,
                "rate_value": exchange_rate_value,
                "exchanged_currency": exchanged_currency_code,
                "converted_amount": amount * exchange_rate_value,
            }
        )


# Currency CRUD Rest service to manage Currencies
class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all().order_by("code")
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
