from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path(
        "livekit-room-token/",
        views.create_livekit_room_token,
        name="create_livekit_room_token",
    ),
]
