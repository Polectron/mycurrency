from django.contrib import admin

from currency.models import Currency, CurrencyExchangeRate, CurrencyProvider

admin.site.register(Currency)
admin.site.register(CurrencyExchangeRate)
admin.site.register(CurrencyProvider)