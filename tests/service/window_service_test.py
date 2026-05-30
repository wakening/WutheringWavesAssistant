import logging
import threading

import pytest

from src.core.injector import Container
from src.core.workflow import NodeContext

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def ctx():
    logger.debug("\n")

    ctx = NodeContext()
    ctx.runtime.stop_event = threading.Event()
    ctx.runtime.stop_event.set()

    Container.build(ctx)

    return ctx


def test_window(ctx):
    logger.debug("\n")
    logger.debug(ctx.window_service.handle)
    logger.debug(ctx.window_service.get_lang())
    logger.debug(ctx.window_service.window_bbox())
    logger.debug(ctx.window_service.is_foreground_window())
