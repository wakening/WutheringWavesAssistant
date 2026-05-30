import logging
import threading

import pytest

from src.core.geometry import AnchorBBox, AnchorPoint, Align
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


def test_roi(ctx):
    logger.debug("\n")

    # ctx.spec.game_lang = Language.ZH
    # # ctx.spec.game_lang = Language.EN
    #
    # ui = UIOp(ctx)
    # ui.snapshot()

    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 200, Align.Left | Align.Middle),
        AnchorPoint(1280, 450, Align.Right | Align.Middle)
    ))
    logger.debug(f"roi: {roi}")

    p = ctx.scaler.as_point(AnchorPoint(466, 309, Align.Center | Align.Middle))
    logger.debug(f"p: {p}")
