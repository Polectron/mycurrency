from currency.models import Currency, CurrencyExchangeRate
from rest_framework import serializers


class CurrencySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Currency
        fields = ["code", "name", "symbol"]


class CurrencyExchangeRateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CurrencyExchangeRate
        fields = ["source_currency", "exchanged_currency", "valuation_date", "rate_value"]
