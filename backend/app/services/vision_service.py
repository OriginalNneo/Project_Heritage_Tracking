import httpx
import base64
import logging
import io

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def identify_checkpoint(image_bytes: bytes, checkpoints: list[dict]) -> dict | None:
    return None
