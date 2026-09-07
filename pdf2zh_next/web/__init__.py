"""HTTP application layer for the React client."""

from pdf2zh_next.web.api import create_api_router
from pdf2zh_next.web.tasks import TranslationTaskManager

__all__ = ["TranslationTaskManager", "create_api_router"]
