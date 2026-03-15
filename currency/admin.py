from django.contrib import admin
from django.http import HttpRequest
from django.urls import path
from django.shortcuts import render

from currency.models import Currency, CurrencyExchangeRate, CurrencyProvider
from core.admin import admin_site

from decimal import Decimal
import datetime
from currency.services import get_exchange_rate


class CurrencyAdmin(admin.ModelAdmin):

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "convert/",
                self.admin_site.admin_view(self.convert_form_view),
                name="currency_convert",
            ),
        ]
        return custom_urls + urls

    def convert_form_view(self, request: HttpRequest):

        context = dict(
            self.admin_site.each_context(request),
            title="Currency Converter",
            currencies=Currency.objects.all().order_by("code"),
        )

        if request.method == "POST":
            from_currency_code = request.POST.get("from_currency")
            to_currency_codes = request.POST.getlist("to_currency")
            amount = request.POST.get("amount")

            if from_currency_code and to_currency_codes and amount:
                try:
                    amount = Decimal(amount)
                    source_currency = Currency.objects.get(code=from_currency_code)
                    valuation_date = datetime.date.today()
                    results = []

                    for to_code in to_currency_codes:
                            exchanged_currency = Currency.objects.filter(code=to_code).get()

                            exchange_rate_value = get_exchange_rate(source_currency, exchanged_currency, valuation_date, amount)

                            results.append(
                                {
                                    "from": from_currency_code,
                                    "to": to_code,
                                    "exchange_rate": exchange_rate_value,
                                    "converted_amount": amount * exchange_rate_value,
                                }
                            )

                    context["results"] = results
                    context["amount"] = amount
                except Exception as e:
                    context["error"] = str(e)

        return render(request, "admin/convert.html", context)


# Register currency models with the global admin site
admin_site.register(Currency, CurrencyAdmin)
admin_site.register(CurrencyExchangeRate)
admin_site.register(CurrencyProvider)
