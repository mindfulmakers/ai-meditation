from __future__ import annotations

from django.contrib.sites.models import Site
from drf_spectacular.generators import SchemaGenerator


class TitleSettingGenerator(SchemaGenerator):
    def get_schema(self, request=None, public: bool = False):
        current_site = Site.objects.get_current(request)
        full_schema = super().get_schema(request, public)

        # Keep only the schemas
        only_schemas = {
            "components": {
                "schemas": full_schema.get("components", {}).get("schemas", {})
            },
            "info": {
                "title": f"{current_site.name} API Schemas",
                "description": f"Generated schemas for {current_site.name}",
                "version": full_schema.get("info", {}).get("version", "1.0.0"),
            },
            "openapi": full_schema.get("openapi", "3.0.3"),
        }
        return only_schemas
