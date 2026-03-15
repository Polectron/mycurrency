from django.urls import include, path
from rest_framework import routers

from currency import views

router = routers.DefaultRouter()
router.register(r"currencies", views.CurrencyViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("rates/", views.CurrencyRatesView.as_view()),
    path("convert/", views.CurrencyConvertView.as_view()),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
