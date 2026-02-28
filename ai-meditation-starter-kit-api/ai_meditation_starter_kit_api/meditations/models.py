from __future__ import annotations

from config.fields import PublicIdField
from django.db import models


class Meditation(models.Model):
    """🧘 Persisted meditation timeline definition."""

    public_id = PublicIdField()
    meditation_id = models.SlugField(max_length=120, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    duration_ms = models.PositiveIntegerField()
    timeline = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "meditation_id"]

    def __str__(self):
        return self.title


class MeditationAudio(models.Model):
    """🔊 Persisted meditation audio asset."""

    public_id = PublicIdField()
    audio_key = models.CharField(max_length=255, unique=True, db_index=True)
    file = models.FileField(upload_to="meditations/audio/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["audio_key"]

    def __str__(self):
        return self.audio_key


class MeditationHaptic(models.Model):
    """📳 Persisted meditation haptic (AHAP) asset."""

    public_id = PublicIdField()
    haptic_key = models.CharField(max_length=255, unique=True, db_index=True)
    file = models.FileField(upload_to="meditations/haptics/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["haptic_key"]

    def __str__(self):
        return self.haptic_key
