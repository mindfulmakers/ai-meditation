from asgiref.sync import sync_to_async
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from .models import SiteAttributes

# Local memory cache mapping hosts to site attributes
_site_attributes_cache = {}


def get_current_site_attributes(request) -> SiteAttributes | None:
    """
    Get the attributes for the current site, using a local memory cache.
    """
    host = request.get_host()

    # Check cache first
    if host in _site_attributes_cache:
        return _site_attributes_cache[host]

    # Get site and its attributes
    site = get_current_site(request)
    if not isinstance(
        site, Site
    ):  # Skip caching for RequestSite objects (used in tests)
        return None

    try:
        attributes = SiteAttributes.objects.get(site=site)
        _site_attributes_cache[host] = attributes
        return attributes
    except SiteAttributes.DoesNotExist:
        _site_attributes_cache[host] = None
        return None


async def aget_current_site_attributes(request) -> SiteAttributes | None:
    """
    Async version of get_current_site_attributes.
    """
    host = request.get_host()

    # Check cache first
    if host in _site_attributes_cache:
        return _site_attributes_cache[host]

    # Get site and its attributes
    site = await sync_to_async(get_current_site)(request)
    if not isinstance(
        site, Site
    ):  # Skip caching for RequestSite objects (used in tests)
        return None

    try:
        attributes = await SiteAttributes.objects.aget(site=site)
        _site_attributes_cache[host] = attributes
        return attributes
    except SiteAttributes.DoesNotExist:
        _site_attributes_cache[host] = None
        return None
