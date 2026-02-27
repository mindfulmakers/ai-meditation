from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_display
from allauth.core import context
from allauth.headless.adapter import DefaultHeadlessAdapter
from django.contrib.sites.shortcuts import get_current_site

from sites.utils import get_current_site_attributes


class AccountAdapter(DefaultAccountAdapter):
    def get_from_email(self) -> str:
        """
        Formats the given email subject.
        """
        site = get_current_site(context.request)
        site_attributes = get_current_site_attributes(context.request)
        assert site is not None
        assert site_attributes is not None

        return f"{site.name} <{site_attributes.from_email}>"


@dataclass
class UserDataclass:
    id: int
    email: str
    first_name: str
    last_name: str
    display: str


class HeadlessAdapter(DefaultHeadlessAdapter):
    def get_user_dataclass(self):
        return UserDataclass

    def user_as_dataclass(self, user):
        return UserDataclass(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            display=user_display(user),
        )

    def serialize_user(self, user) -> dict[str, Any]:
        """
        From allauth docs: Do not override this method if you would like your customized user payloads
        to be reflected in the (dynamically rendered) OpenAPI specification. In that
        case, override ``get_user_dataclass()`` and ``user_as_dataclass`` instead.
        """
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display": user_display(user),
            "has_usable_password": user.has_usable_password(),
        }
