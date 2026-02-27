from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from payment.models import Subscription

User = get_user_model()


def user_has_active_subscription(user: User) -> bool:
    """Return True when the user has an active personal or team subscription."""
    if not user or not user.is_authenticated:
        return False

    now = timezone.now()
    return Subscription.objects.filter(
        Q(account__user_owner=user) | Q(account__team_owner__owner=user),
        expiration_date__gt=now,
    ).exists()


def require_active_subscription(
    user: User,
    detail: str = "An active subscription is required.",
) -> None:
    if not user_has_active_subscription(user):
        raise PermissionDenied(detail=detail)


def _seconds_until_next_day(now):
    next_day = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return max(1, int((next_day - now).total_seconds()))


def require_within_hard_cap(
    *,
    current_count: int,
    cap: int,
    detail: str,
) -> None:
    # `cap <= 0` disables creation for that resource.
    if cap <= 0 or current_count >= cap:
        raise PermissionDenied(detail=detail)


def require_user_project_capacity(user: User) -> None:
    from openbase_api.dev.models import Project

    cap = getattr(settings, "BILLING_MAX_PROJECTS_PER_USER", 1)
    current_count = Project.objects.filter(user=user).count()
    require_within_hard_cap(
        current_count=current_count,
        cap=cap,
        detail=f"Project limit reached ({cap} max per user).",
    )


def consume_daily_user_quota(
    *,
    user: User,
    quota_name: str,
    max_daily_actions: int,
    detail: str,
) -> int:
    now = timezone.now()
    key = f"billing:quota:{quota_name}:{user.pk}:{now.date().isoformat()}"
    timeout = _seconds_until_next_day(now)
    current = cache.get(key, 0)

    if current >= max_daily_actions:
        raise PermissionDenied(detail=detail)

    if cache.add(key, 1, timeout=timeout):
        return max_daily_actions - 1

    try:
        updated = cache.incr(key)
    except ValueError:
        updated = current + 1
        cache.set(key, updated, timeout=timeout)

    return max(0, max_daily_actions - updated)
