import logging
import math
import time
from collections import deque

import win32gui
import ctypes

from src.util import hwnd_util

logger = logging.getLogger(__name__)

# =========================================================
# 光标防护工具，当监测到鼠标跳到游戏中心后，自动将鼠标移回原位
# =========================================================

POLL_INTERVAL = 0.01

CENTER_TOLERANCE = 100

HISTORY_SIZE = 30
RESTORE_INDEX = 8

RECOVERY_COOLDOWN = 0.25

# ClipCursor 限流
UNLOCK_INTERVAL = 0.2


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def get_center(hwnd):
    # 不做 ClientToScreen cache，因为窗口可能移动
    l, t, r, b = win32gui.GetClientRect(hwnd)
    x1, y1 = win32gui.ClientToScreen(hwnd, (l, t))
    x2, y2 = win32gui.ClientToScreen(hwnd, (r, b))
    return (x1 + x2) / 2, (y1 + y2) / 2


def near(p, c):
    return dist(p, c) < CENTER_TOLERANCE


def unlock_cursor():
    ctypes.windll.user32.ClipCursor(None)


def get_pos():
    pt = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def set_pos(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)


def run(event, **kwargs):
    try:
        logger.info("cursor guard started")

        hwnd_util.enable_dpi_awareness()

        hwnd = None

        history = deque(maxlen=HISTORY_SIZE)
        history.append(get_pos())

        cooldown_until = 0.0
        last_unlock_time = 0.0

        while event.is_set():
            time.sleep(POLL_INTERVAL)

            # hwnd cache
            if hwnd is None or not win32gui.IsWindow(hwnd):
                hwnd = hwnd_util.get_hwnd()
                logger.debug(f"[HWND] refreshed -> {hwnd}")
                continue

            now = time.perf_counter()

            # cooldown
            if now < cooldown_until:
                history.append(get_pos())
                continue

            # 限流 ClipCursor
            if now - last_unlock_time > UNLOCK_INTERVAL:
                unlock_cursor()
                last_unlock_time = now

            prev = history[-1]
            curr = get_pos()

            move = dist(prev, curr)

            center = get_center(hwnd)

            prev_c = near(prev, center)
            curr_c = near(curr, center)

            entered_center = (not prev_c) and curr_c

            # 检测异常
            if entered_center and move > 200:
                restore = (
                    history[-RESTORE_INDEX]
                    if len(history) > RESTORE_INDEX
                    else history[0]
                )

                logger.debug(f"[RECOVER] move={move:.1f} -> {restore}")

                set_pos(*restore)

                cooldown_until = now + RECOVERY_COOLDOWN

                history.append(curr)
                continue

            # history update
            history.append(curr)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        logger.info("cursor guard finished")
