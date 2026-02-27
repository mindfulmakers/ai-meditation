from __future__ import annotations

from rest_framework import serializers


class PublicIDField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("source", "public_id")
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)


class BaseModelSerializer(serializers.ModelSerializer):
    id = PublicIDField()

    class Meta:
        abstract = True


class PublicIDRelatedField(serializers.RelatedField):
    """
    A field that represents a relationship using the public_id of the target.
    Similar to PrimaryKeyRelatedField but uses public_id instead of pk.
    """

    def to_representation(self, value):
        if value is None:
            return None
        return getattr(value, "public_id", None)

    def to_internal_value(self, data):
        if self.queryset is None:
            raise NotImplementedError(
                "Writable PublicIDRelatedField must include a `queryset` argument."
            )

        try:
            return self.queryset.get(public_id=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)
        except self.queryset.model.DoesNotExist:
            self.fail("does_not_exist", public_id=data)
        except self.queryset.model.MultipleObjectsReturned:
            self.fail("multiple_objects", public_id=data)

    default_error_messages = {
        "does_not_exist": "Object with public_id={public_id} does not exist.",
        "incorrect_type": "Incorrect type. Expected str, but got {data_type}.",
        "multiple_objects": "Multiple objects found for public_id={public_id}.",
    }
