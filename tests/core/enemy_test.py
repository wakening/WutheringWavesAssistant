import logging
import time

from src.core.enemy import EnemyHpBar, EnemyVsBar
from src.util import img_util, file_util

logger = logging.getLogger(__name__)


def test_hp():
    logger.debug("\n")

    img = img_util.read_img(file_util.get_temp_screenshot("screenshot_1788474488_22802743.png"))

    start_time = time.monotonic()
    hp = EnemyHpBar.detect(img)
    if hp is not None:
        logger.debug(f"hp: {hp * 100:.2f}%")
    else:
        logger.debug(f"hp: {hp}")

    stance = EnemyVsBar.detect(img)
    logger.debug(f"stance: {stance * 100:.2f}%")

    logger.debug(f"耗时: {time.monotonic() - start_time:.2f}")

    img_util.show_img(img)
