from __future__ import annotations

import logging
from typing import NamedTuple

logger = logging.getLogger(__name__)


class EmbeddingsModel(NamedTuple):
    name: str
    dimensions: int


OPENAI_TEXT_EMBEDDING_3_LARGE = EmbeddingsModel(
    name="text-embedding-3-large",
    dimensions=3072,
)
