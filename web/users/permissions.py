from django.conf import settings
from rest_framework import permissions
from twilio.request_validator import RequestValidator


class ValidateTwilioRequest(permissions.BasePermission):
    """
    Permission class to validate that incoming requests genuinely originated from Twilio.
    """

    def has_permission(self, request, view):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.build_absolute_uri(),
            request.data,  # DRF uses request.data instead of request.POST
            request.META.get("HTTP_X_TWILIO_SIGNATURE", ""),
        )

        # Return True if the request is valid, False otherwise
        return request_valid

    def has_object_permission(self, request, view, obj):
        return True


class IsToOwnedNumber(permissions.BasePermission):
    """
    Permission class to validate the 'To' field in the POST request.
    """

    def has_permission(self, request, view):
        # Validate 'To' number
        to_number = request.data.get("To", None)
        if to_number != settings.OWNED_TWILIO_NUMBER:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return True
