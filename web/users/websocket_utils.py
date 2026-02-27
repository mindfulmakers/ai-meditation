from __future__ import annotations

import logging
from typing import Any, Type

from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from rest_framework.serializers import Serializer

logger = logging.getLogger(__name__)


def send_event_to_user(user_id: int, event_type: str, data: dict[str, Any] | None = None) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available")
        return

    group_name = f"user_{user_id}"

    event = {
        "type": "user.event",
        "event_type": event_type,
        "data": data or {},
    }

    async_to_sync(channel_layer.group_send)(group_name, event)
    logger.debug(f"Sent {event_type} event to user {user_id}")


async def send_event_to_user_async(user_id: int, event_type: str, data: dict[str, Any] | None = None) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available")
        return

    group_name = f"user_{user_id}"

    event = {
        "type": "user.event",
        "event_type": event_type,
        "data": data or {},
    }

    await channel_layer.group_send(group_name, event)
    logger.debug(f"Sent {event_type} event to user {user_id}")


async def send_serialized_event_to_user_async(
    user_id: int,
    event_type: str,
    instance: Any,
    serializer_class: Type[Serializer],
    context: dict[str, Any] | None = None,
) -> None:
    """
    Send a WebSocket event with serialized model instance data.
    Handles the sync_to_async wrapping automatically.

    Args:
        user_id: The user ID to send the event to
        event_type: The type of event (e.g., "new_message", "document_updated")
        instance: The model instance to serialize
        serializer_class: The serializer class to use for serialization
        context: Optional context dictionary for the serializer
    """
    @sync_to_async
    def serialize_instance():
        serializer = serializer_class(instance, context=context or {})
        return dict(serializer.data)

    serialized_data = await serialize_instance()
    await send_event_to_user_async(user_id, event_type, serialized_data)