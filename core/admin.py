from django.contrib import admin
from django.urls import reverse

from django.contrib.auth.models import User, Group


class CustomAdminSite(admin.AdminSite):
    site_header = "Currency Exchange Administration"
    site_title = "Currency Admin"

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        # Add custom link to Currency app
        for app in app_list:
            if app["app_label"] == "currency":
                app["models"].insert(
                    0,
                    {
                        "name": "Currency Converter",
                        "object_name": "converter",
                        "admin_url": reverse("admin:currency_convert"),
                        "view_only": True,
                    },
                )

        return app_list


# Create the global admin site instance
admin_site = CustomAdminSite(name="admin")

# Register Django's built-in auth models
admin_site.register(User)
admin_site.register(Group)
