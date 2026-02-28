from sites.utils import get_or_create_current_site


def global_settings(request):
    current_site = get_or_create_current_site(request)
    product_name = current_site.name if current_site is not None else ""
    return {
        "product_name": product_name,
    }
