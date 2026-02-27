from __future__ import annotations

import logging
import os

from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
from django.conf import settings

if not settings.configured:
    django.setup()

from taskiq_redis import ListQueueBroker

logger = logging.getLogger(__name__)

broker = ListQueueBroker(
    url=settings.BROKER_URL,
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
