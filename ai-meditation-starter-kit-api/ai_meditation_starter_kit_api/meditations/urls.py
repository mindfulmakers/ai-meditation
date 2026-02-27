from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MeditationAudioView, MeditationViewSet

router = DefaultRouter()
router.register("meditations", MeditationViewSet, basename="meditations")

urlpatterns = [
    path(
        "meditations/audio/<path:audio_path>",
        MeditationAudioView.as_view(),
        name="meditations-audio",
    ),
    *router.urls,
]
