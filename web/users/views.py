from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import serializers
from .models import (
    UserAPNSToken,
)

User = get_user_model()


class UserDetail(generics.RetrieveAPIView):
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user


class APNSView(APIView):
    """
    View for registering and unregistering APNS devices for push notifications.
    """

    def post(self, request):
        user = request.user
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Device token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(user, "apns_token") and user.apns_token is not None:
            user.apns_token.token = token
            user.apns_token.save()
            return Response(
                {"message": "Device token updated successfully."},
                status=status.HTTP_200_OK,
            )
        UserAPNSToken.objects.create(user=user, token=token)
        return Response(
            {"message": "Device token registered successfully."},
            status=status.HTTP_200_OK,
        )


class DeleteUserView(APIView):
    # Commonly known as "delete-account".  This will remove the user from the system (and their associated Account object if they have one).

    def post(self, request):
        payload = request.data
        confirm = payload.get("confirm")
        if not confirm or confirm != "yes":
            msg = "Key 'confirm' is required. Must be set to 'yes'"
            raise ValidationError(msg)
        self.request.user.delete()
        return Response({"message": "Account deleted successfully."})
