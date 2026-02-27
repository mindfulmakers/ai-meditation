from __future__ import annotations

import json
import os

import allauth.headless.urls

# from django.contrib import admin
from django.conf import settings

# from django.contrib import admin # Comment out or remove, as we use the custom site instance directly
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from oauth2_provider.urls import (
    base_urlpatterns as oauth_base_url_patterns,
)
from oauth2_provider.urls import (
    urlpatterns as oauth_url_patterns,
)

from config.app_packages import get_package_apps
from sites import views

admin_suffix = f"-{settings.ADMIN_SUFFIX}" if not settings.DEBUG else ""

# admin.autodiscover() # autodiscover is usually called by AdminSite instance or when Django initializes admin
# Our custom site should handle registrations. If models are in admin.py files, they should be registered with dynamic_admin_site

# if not settings.DEBUG:
#     # If you re-enable this, apply to dynamic_admin_site.login
#     dynamic_admin_site.login = secure_admin_login(dynamic_admin_site.login)

urlpatterns = [
    path(f"admin{admin_suffix}/", admin.site.urls),  # Use custom admin site
    path(
        "o/",
        include(
            (
                oauth_base_url_patterns if not settings.DEBUG else oauth_url_patterns,
                "oauth2_provider",
            ),
            namespace="oauth2_provider",
        ),
    ),
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    path("api/", include("users.urls")),
    path("api/", include("contact.urls")),
    path("api/", include("payment.urls")),
    path("api/", include("agent.urls")),
]

extra_urls = allauth.headless.urls

# Load site prefixes from JSON env variable
url_prefixes = json.loads(os.environ.get("URL_PREFIXES", "{}"))

# Add enabled site URLs
for app in get_package_apps():
    # Check for exact match first
    if app in url_prefixes:
        prefix = url_prefixes[app].rstrip("/") + "/"
    else:
        # Check for wildcard patterns (ending with .*)
        matched_prefix = None
        for pattern, pattern_prefix in url_prefixes.items():
            if pattern.endswith(".*") and app.startswith(pattern[:-2]):
                prefix = pattern_prefix.rstrip("/") + "/"
                break
        else:
            prefix = "api/" + app.split(".")[0].removesuffix("_api") + "/"

    urlpatterns.append(path(prefix, include(f"{app}.urls")))

# Add catch-all routes at the end
urlpatterns += [
    path("", views.serve_index, {"resource": ""}),
]


if not settings.DEBUG:
    urlpatterns += [
        path("<path:resource>", views.serve_index),
    ]
else:
    urlpatterns += [
        # API Schema documentation
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
