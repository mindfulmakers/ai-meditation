from django.contrib import admin
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

from .models import SiteAttributes


class SiteAttributesInline(admin.StackedInline):
    model = SiteAttributes
    can_delete = False
    fields = (
        "s3_frontend_folder",
        "stripe_product_id",
        "stripe_price_cents",
        "from_email",
    )


# Unregister the default Site admin
admin.site.unregister(Site)


# Register our custom Site admin with the inline attributes
@admin.register(Site)
class CustomSiteAdmin(SiteAdmin):
    inlines = [SiteAttributesInline]


# Register the SiteAttributes model
admin.site.register(SiteAttributes)
