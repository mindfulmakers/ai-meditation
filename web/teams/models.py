import re

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class Team(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    owner = models.ForeignKey(
        get_user_model(),
        related_name="owned_teams",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    @classmethod
    def get_access_user_username(cls, slug):
        return f"team_{slug.replace('-', '_')}"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = name_to_slug(self.name)
            if Team.objects.filter(slug=self.slug).exists():
                raise ValidationError(f"Team with slug {self.slug} already exists.")
        super().save(force_insert, force_update, using, update_fields)

    @property
    def billable_users(self):
        return self.users

    def num_billable_users(self):
        """
        Excludes the API access user and any non-active users.
        """
        return self.billable_users.count()

    def get_email(self):
        return self.owner.email if self.owner else None

    def __str__(self):
        return self.name


def name_to_slug(name):
    return re.sub(r"[^a-zA-Z0-9\-]", "", name.lower().replace(" ", "-"))


def get_user_or_team_ownership_mixin(
    related_name, on_delete=models.SET_NULL, relation_type=models.ForeignKey
):
    class UserOrTeamOwnershipMixin(models.Model):
        class Meta:
            abstract = True

        user_owner = relation_type(
            get_user_model(),
            related_name=related_name,
            on_delete=on_delete,
            null=True,
            blank=True,
        )
        team_owner = relation_type(
            "teams.Team",
            related_name=related_name,
            on_delete=on_delete,
            null=True,
            blank=True,
        )

        @property
        def owner(self):
            return self.user_owner or self.team_owner

        def validate_owner(self):
            if self.user_owner and self.team_owner:
                raise serializers.ValidationError(
                    "Cannot have both user_owner and team_owner"
                )

    return UserOrTeamOwnershipMixin
