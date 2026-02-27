from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet


class BaseModelViewSet(ModelViewSet):
    lookup_field = "public_id"


class BaseReadOnlyModelViewSet(ReadOnlyModelViewSet):
    lookup_field = "public_id"
