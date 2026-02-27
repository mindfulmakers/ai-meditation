import inspect

from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.db import models


class DynamicAdminSite(admin.AdminSite):
    def get_app_list(self, request: WSGIRequest, *args, **kwargs):
        """
        Return a list of applications and models that are available for the
        current site.
        """
        app_list = super().get_app_list(request, *args, **kwargs)
        current_site = getattr(request, "site", None)

        if not current_site:
            # If there's no site on the request, or it's not what we expect,
            # return all apps or a default set.
            return app_list

        # Placeholder for logic to determine which apps are allowed for the current_site
        # For example, you might have a dictionary mapping site domains or names to app labels.
        # allowed_app_labels_for_site = {
        # "example.com": ["auth", "sites", "myapp1"],
        # "another.example.com": ["auth", "sites", "myapp2"],
        # }.get(current_site.domain, [])

        # For now, let's assume we have a way to get allowed app labels
        # This is a simplified example; you'll need to define this logic.
        if current_site.domain == "specific.domain.com":
            allowed_app_labels = ["users", "teams"]  # Example
        else:
            allowed_app_labels = [
                app["app_label"] for app in app_list
            ]  # Show all by default

        filtered_app_list = []
        for app in app_list:
            if app["app_label"] in allowed_app_labels:
                # You might also want to filter models within an app
                # app["models"] = [model for model in app["models"] if model["object_name"] in allowed_model_names]
                filtered_app_list.append(app)

        return filtered_app_list


def auto_register_models(app_models):
    """
    Automatically register all Django models from the models module.
    """
    # Get all members of the models module
    model_classes = inspect.getmembers(app_models, inspect.isclass)

    # Filter to only Django models (exclude imported models like User)
    django_models = []
    for name, model_class in model_classes:
        # Check if it's a Django model and defined in this app (not imported)
        if (
            issubclass(model_class, models.Model)
            and model_class.__module__ == app_models.__name__
            and model_class != models.Model  # Exclude the base Model class itself
        ):
            django_models.append((name, model_class))

    # Register each model with the admin
    for _, model_class in django_models:
        admin.site.register(model_class)


# Instantiate your custom admin site
site = DynamicAdminSite(name="dynamic_admin")
