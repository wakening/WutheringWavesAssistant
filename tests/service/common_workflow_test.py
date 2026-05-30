import logging
import threading

import pytest

from src.core.injector import Container
from src.core.workflow import NodeContext
from src.service.common_workflow import object_detection

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def ctx():
    logger.debug("\n")

    ctx = NodeContext()
    ctx.runtime.stop_event = threading.Event()
    ctx.runtime.stop_event.set()

    Container.build(ctx)

    return ctx


def test_search_reward(ctx):
    logger.debug("\n")
    found = ctx.od_service.search_reward()
    logger.debug(f"found: {found}")
    object_detection(ctx, search_reward=True)
