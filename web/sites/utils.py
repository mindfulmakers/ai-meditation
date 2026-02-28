from asgiref.sync import sync_to_async
from django.conf import settings
from django.http.request import split_domain_port
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import SITE_CACHE, Site
from .models import SiteAttributes

# Local memory cache mapping hosts to site attributes
_site_attributes_cache = {}


def get_or_create_current_site(request):
    """
    Return the current site and, in DEBUG only, create one for unknown hosts.
    """
    try:
        return get_current_site(request)
    except Site.DoesNotExist:
        if not settings.DEBUG:
            raise

        host = request.get_host().lower()
        domain, _ = split_domain_port(host)

        site = Site.objects.filter(domain__iexact=host).first()
        if site is None and domain:
            site = Site.objects.filter(domain__iexact=domain).first()
        if site is None:
            site = Site.objects.create(domain=host, name=domain or host)

        SITE_CACHE[host] = site
        if domain:
            SITE_CACHE[domain] = site
        return site


async def aget_or_create_current_site(request):
    return await sync_to_async(get_or_create_current_site)(request)


def get_current_site_attributes(request) -> SiteAttributes | None:
    """
    Get the attributes for the current site, using a local memory cache.
    """
    host = request.get_host()

    # Check cache first
    if host in _site_attributes_cache:
        return _site_attributes_cache[host]

    # Get site and its attributes
    site = get_or_create_current_site(request)
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
    site = await aget_or_create_current_site(request)
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
