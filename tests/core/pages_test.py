import logging
import threading

import pytest

from src.core.i18n import I18nText, Language
from src.core.injector import Container
from src.core.pages import UIOp
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


def test_ui_WeeklyChallenge(ctx):
    logger.debug("\n")

    ctx.spec.game_lang = Language.ZH
    # ctx.spec.game_lang = Language.EN

    ui = UIOp(ctx)
    ui.snapshot()

    remainingWeeklyAttempts = ctx.tr(I18nText.RemainingWeeklyAttempts)
    logger.debug(f"RemainingWeeklyAttempts: {remainingWeeklyAttempts}")
    result = ui.search(remainingWeeklyAttempts)
    logger.debug(f"result: {result}")

    seedOfIllusoryOrigin = ctx.tr(I18nText.SeedOfIllusoryOrigin)
    logger.debug(f"SeedOfIllusoryOrigin: {seedOfIllusoryOrigin}")
    result = ui.search(seedOfIllusoryOrigin)
    logger.debug(f"result: {result}")

    gateOfTheLostStar = ctx.tr(I18nText.GateOfTheLostStar)
    logger.debug(f"GateOfTheLostStar: {gateOfTheLostStar}")
    result = ui.search(gateOfTheLostStar)
    logger.debug(f"result: {result}")

    cinderniteApocalypse = ctx.tr(I18nText.CinderniteApocalypse)
    logger.debug(f"CinderniteApocalypse: {cinderniteApocalypse}")
    result = ui.search(cinderniteApocalypse)
    logger.debug(f"result: {result}")

    theWheelOfBrokenFate = ctx.tr(I18nText.TheWheelOfBrokenFate)
    logger.debug(f"TheWheelOfBrokenFate: {theWheelOfBrokenFate}")
    result = ui.search(theWheelOfBrokenFate)
    logger.debug(f"result: {result}")

    beyondTheCrimsonCurtain = ctx.tr(I18nText.BeyondTheCrimsonCurtain)
    logger.debug(f"BeyondTheCrimsonCurtain: {beyondTheCrimsonCurtain}")
    result = ui.search(beyondTheCrimsonCurtain)
    logger.debug(f"result: {result}")

    theFatedConfrontation = ctx.tr(I18nText.TheFatedConfrontation)
    logger.debug(f"TheFatedConfrontation: {theFatedConfrontation}")
    result = ui.search(theFatedConfrontation)
    logger.debug(f"result: {result}")

    statueOfTheCrownless = ctx.tr(I18nText.StatueOfTheCrownless)
    logger.debug(f"StatueOfTheCrownless: {statueOfTheCrownless}")
    result = ui.search(statueOfTheCrownless)
    logger.debug(f"result: {result}")

    chaoticJuncture = ctx.tr(I18nText.ChaoticJuncture)
    logger.debug(f"ChaoticJuncture: {chaoticJuncture}")
    result = ui.search(chaoticJuncture)
    logger.debug(f"result: {result}")

    bellOfArchaicChants = ctx.tr(I18nText.BellOfArchaicChants)
    logger.debug(f"BellOfArchaicChants: {bellOfArchaicChants}")
    result = ui.search(bellOfArchaicChants)
    logger.debug(f"result: {result}")
