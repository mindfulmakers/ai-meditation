from __future__ import annotations

import contextlib

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.authtoken.models import Token

stripe.api_key = settings.STRIPE_SECRET_KEY


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            msg = "The Email field must be set"
            raise ValueError(msg)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    phone_number_in_validation = models.CharField(max_length=32, blank=True)
    phone_number_validation_code = models.CharField(max_length=32, blank=True)
    phone_number = models.CharField(
        max_length=32,
        blank=True,
    )
    timezone = models.CharField(
        max_length=32, null=False, blank=False, default="America/New_York"
    )

    site = models.ForeignKey(
        "sites.Site", on_delete=models.SET_NULL, null=True, blank=True
    )

    def get_account(self):
        if not hasattr(self, "account") or self.account is None:
            from payment.models import Account

            account = Account.objects.create(user_owner=self)
        else:
            account = self.account
        if not account.customer_id:
            with contextlib.suppress(stripe.error.AuthenticationError):
                customer = stripe.Customer.create(
                    email=self.email,
                    metadata={"user_id": self.id},
                )
                customer_id = customer.id
                account.customer_id = customer_id
                account.save()
        return account

    async def aget_account(self):
        from payment.models import Account

        account = await Account.objects.filter(user_owner=self).afirst()
        if account is None:
            account = await Account.objects.acreate(user_owner=self)
        if not account.customer_id:
            customer = await stripe.Customer.create_async(
                email=self.email,
                metadata={"user_id": self.id},
            )
            customer_id = customer.id
            account.customer_id = customer_id
            await account.asave()
        return account

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.get_account()

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name

    async def active_subscription(self):
        """Returns the subscription type if there's an active subscription, None otherwise"""
        from payment.models import Subscription  # Move import here

        account = await self.aget_account()
        subscription = await Subscription.objects.filter(account=account).afirst()
        if subscription and subscription.is_active():
            return subscription.subscription_type
        return None


@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class UserAPNSToken(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="apns_token"
    )
    token = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Token for {self.user}"
