import logging
import threading

import pytest

from src.core.geometry import AnchorBBox, AnchorPoint, Align
from src.core.injector import Container
from src.core.pages import UIOp
from src.core.workflow import NodeContext
from src.service.common_workflow import Slider

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


def test_slider(ctx):
    logger.debug("\n")
    ctx.control_service.activate()

    ui = UIOp(ctx)
    points = Slider.points(ui.grap())
    logger.debug(f"points: {points}")
    for i, p in enumerate(points):
        logger.debug(f"i: {i}, p: {p}")
        ui.sleep(0.3).click_point(p, times=2, interval=0.2)

    ui.sleep(0.3)
