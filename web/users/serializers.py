from __future__ import annotations

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from rest_framework import serializers

from config.serializers import BaseModelSerializer

User = get_user_model()


class UserSerializer(BaseModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "balance",
            "active_subscription",
            "is_staff",
        ]
        read_only_fields = ["email", "balance", "is_staff"]

    balance = serializers.SerializerMethodField()
    active_subscription = serializers.SerializerMethodField()

    def get_balance(self, obj):
        return obj.get_account().balance

    def get_active_subscription(self, obj):
        return async_to_sync(obj.active_subscription)()
