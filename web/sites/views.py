from __future__ import annotations

import httpx
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.middleware.csrf import get_token

from .utils import aget_current_site_attributes


async def serve_index(request, resource):
    # Check if requested type is JSON - in this case the error is likely 404
    # NOTE: This may mess things up if we end up wanting to serve JSON files statically.
    if "application/json" in (request.META.get("HTTP_ACCEPT") or []):
        return HttpResponse(status=404)

    site_attributes = await aget_current_site_attributes(request)
    if not site_attributes:
        return HttpResponse("Site not found.", status=404)

    site_s3_folder = site_attributes.s3_frontend_folder
    cache_key = f"index_html_cache_{site_s3_folder}"
    cache_timeout = 10  # Cache timeout in seconds

    # Attempt to get the cached content asynchronously
    cached_content = await cache.aget(cache_key)
    if cached_content:
        response = HttpResponse(cached_content, content_type="text/html")
    else:
        # Fetch the content using httpx
        async with httpx.AsyncClient() as client:
            try:
                url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{site_s3_folder}/index.html"
                response = await client.get(url)
                response.raise_for_status()
                file_contents = response.text

                # Cache the fetched content asynchronously
                await cache.aset(cache_key, file_contents, cache_timeout)

                response = HttpResponse(file_contents, content_type="text/html")
            except httpx.HTTPStatusError as e:
                return HttpResponse(
                    f"Error fetching index.html from S3: {e}",
                    status=e.response.status_code,
                )
            except Exception as e:
                return HttpResponse(
                    f"Error fetching index.html from S3: {e!s}",
                    status=500,
                )

    # Manually ensure a CSRF token is generated and set the CSRF cookie
    get_token(request)
    return response
