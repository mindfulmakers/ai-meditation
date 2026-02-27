from django.apps import AppConfig


class SitesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sites"
    label = "site_attributes"
    verbose_name = "Site Attributes"
