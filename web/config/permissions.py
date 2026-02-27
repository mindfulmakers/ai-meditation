_required_site_key = "required_site_key"


"""
Provides a set of pluggable permission policies.
"""


from rest_framework.permissions import SAFE_METHODS


class AllowAny:
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    async def has_permission(self, request, view):
        return True


class IsAuthenticated:
    """
    Allows access only to authenticated users.
    """

    async def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminUser:
    """
    Allows access only to admin users.
    """

    async def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAuthenticatedOrReadOnly:
    """
    The request is authenticated as a user, or is a read-only request.
    """

    async def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_authenticated
        )


class IsAuthenticatedForSite(IsAuthenticated):
    async def has_permission(self, request, view):
        if not await super().has_permission(request, view):
            return False
        required_site_id = getattr(view, _required_site_key, None)
        if not required_site_id:
            return False
        if not request.user.site == required_site_id:
            return False
        return True
