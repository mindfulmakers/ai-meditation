from __future__ import annotations

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class UserEventsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        from django.contrib.auth.models import AnonymousUser

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        self.user_group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()
        logger.info(f"WebSocket connected for user {self.user.id}")

    async def disconnect(self, code):
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )
            logger.info(f"WebSocket disconnected for user {self.user.id}")

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def user_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": event.get("event_type", "message"),
                    "data": event.get("data", {}),
                }
            )
        )
