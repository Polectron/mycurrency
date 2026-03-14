from django.contrib import admin

from currency.models import Currency, CurrencyExchangeRate

admin.site.register(Currency)
admin.site.register(CurrencyExchangeRate)