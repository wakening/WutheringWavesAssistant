import logging

import cv2
import mss
import numpy as np
from mss.base import MSSBase
from mss.models import Monitor

logger = logging.getLogger(__name__)


def create_mss() -> MSSBase:
    return mss.mss()


def screenshot(sct: MSSBase, monitor: Monitor | tuple[int, int, int, int] | None = None) -> np.ndarray:
    if not isinstance(sct, MSSBase):
        raise ValueError("参数异常")
    if monitor is None:
        sct_img = sct.shot()
    else:
        sct_img = sct.grab(monitor)
    img_bgra = np.array(sct_img)
    img_bgr = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
    # logger.debug("mss img shape: %s", img_bgra.shape)
    return img_bgr
