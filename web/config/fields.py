from __future__ import annotations

import secrets

from django.db import models
from rest_framework import serializers
from rest_framework.fields import CharField


def generate_random_id(length=12):
    return secrets.token_hex(length // 2)


class PublicIdField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        kwargs.setdefault("unique", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("editable", True)
        kwargs.setdefault("db_index", True)
        kwargs.setdefault("help_text", "Public-facing random ID")
        kwargs.setdefault("default", generate_random_id)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if not value:
            value = generate_random_id()
            setattr(model_instance, self.attname, value)
        return value


class PublicIdRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", CharField())
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        # TODO: Reset to False
        return False

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        queryset = self.get_queryset()
        try:
            if isinstance(data, bool):
                raise TypeError
            return queryset.get(public_id=data)
        except models.ObjectDoesNotExist:
            self.fail("does_not_exist", pk_value=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)

    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.public_id)
        return value.public_id


class UserOwnedPublicIdRelatedField(PublicIdRelatedField):
    def get_queryset(self):
        request = self.context.get("request", None)
        queryset = super().get_queryset()
        if not request or not queryset:
            msg = "Request or queryset is missing"
            raise ValueError(msg)
        return queryset.filter(user=request.user)
