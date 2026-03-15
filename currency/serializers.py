from currency.models import Currency, CurrencyExchangeRate
from rest_framework import serializers


class CurrencySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "name", "symbol"]


class CurrencyExchangeRateSerializer(serializers.HyperlinkedModelSerializer):
    source_currency = serializers.SlugRelatedField(slug_field='code', read_only=True)
    exchanged_currency = serializers.SlugRelatedField(slug_field='code', read_only=True)
    class Meta:
        model = CurrencyExchangeRate
        fields = ["id", "source_currency", "exchanged_currency", "valuation_date", "rate_value"]
