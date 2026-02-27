from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from teams.models import get_user_or_team_ownership_mixin

UserOrTeamOwnershipMixin = get_user_or_team_ownership_mixin(
    "account", on_delete=models.CASCADE, relation_type=models.OneToOneField
)


class Account(UserOrTeamOwnershipMixin):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customer_id = models.CharField(
        max_length=255, blank=True, help_text="Stripe customer ID"
    )
    apple_uuid = models.UUIDField(blank=True, default="")  # type: ignore

    @property
    def get_email(self):
        if self.user_owner:
            return self.user_owner.email
        elif self.team_owner:
            return self.team_owner.email
        msg = "Account has no owner"
        raise ValueError(msg)

    async def has_active_subscription(self):
        subscription = await Subscription.objects.filter(account=self).afirst()
        return subscription.is_active() if subscription else False

    @property
    def is_personal(self):
        return self.user_owner is not None

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.user_owner and self.team_owner:
            msg = "Account cannot have both user_owner and team_owner"
            raise ValidationError(msg)
        if not self.apple_uuid:
            self.apple_uuid = uuid.uuid4()
        super().save(
            force_insert=False, force_update=False, using=None, update_fields=None
        )

    def __str__(self):
        return f"{self.user_owner or self.team_owner} account"


class Subscription(models.Model):
    account = models.OneToOneField(
        Account, related_name="subscription", on_delete=models.CASCADE
    )
    subscription_type = models.CharField(max_length=100)
    expiration_date = models.DateTimeField()
    platform_data = models.JSONField(default=dict)
    is_sandbox = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.account} subscription"

    def is_active(self):
        return self.expiration_date > timezone.now()
