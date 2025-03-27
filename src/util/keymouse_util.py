import logging
import random
import time

import win32api
import win32con
import win32gui

logger = logging.getLogger(__name__)

KEYBOARD_VK_MAPPING: dict[str, int] = {
    "0": 48,
    "1": 49,
    "2": 50,
    "3": 51,
    "4": 52,
    "5": 53,
    "6": 54,
    "7": 55,
    "8": 56,
    "9": 57,
    "A": 65,
    "B": 66,
    "C": 67,
    "D": 68,
    "E": 69,
    "F": 70,
    "G": 71,
    "H": 72,
    "I": 73,
    "J": 74,
    "K": 75,
    "L": 76,
    "M": 77,
    "N": 78,
    "O": 79,
    "P": 80,
    "Q": 81,
    "R": 82,
    "S": 83,
    "T": 84,
    "U": 85,
    "V": 86,
    "W": 87,
    "X": 88,
    "Y": 89,
    "Z": 90,
    "LSHIFT": win32con.VK_LSHIFT,
    "ESC": win32con.VK_ESCAPE,
    "SPACE": win32con.VK_SPACE,
    "F1": win32con.VK_F1,
    "F2": win32con.VK_F2,
}

VK_KEYBOARD_MAPPING: dict[int, str] = {v: k for k, v in KEYBOARD_VK_MAPPING.items()}


###### Keyboard ######


def tap_key(hwnd, key: str | int, seconds: float = 0.0):
    if isinstance(key, str):
        vk_key = KEYBOARD_VK_MAPPING.get(key.upper())
    else:
        vk_key = key
    logger.debug("Tap key: %s, seconds: %s", VK_KEYBOARD_MAPPING.get(vk_key), seconds)
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
    __sleep(seconds)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)


def key_down(hwnd, key: int | str, seconds: float = 0.0):
    if isinstance(key, str):
        vk_key = KEYBOARD_VK_MAPPING.get(key.upper())
    else:
        vk_key = key
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
    __sleep(seconds)


def key_up(hwnd, key: int | str, seconds: float = 0.0):
    if isinstance(key, str):
        vk_key = KEYBOARD_VK_MAPPING.get(key.upper())
    else:
        vk_key = key
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)
    __sleep(seconds)


###### Mouse ######

# noinspection PyUnresolvedReferences
def click(hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse click: (%s, %s), seconds: %s", x, y, seconds)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    __sleep(seconds)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)


# noinspection PyUnresolvedReferences
def mouse_left_down(hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse left down: %d, %d", x, y)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    __sleep(seconds)


# noinspection PyUnresolvedReferences
def mouse_left_up(hwnd, x: int, y: int, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse left up: %d, %d", x, y)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)
    __sleep(seconds)


# noinspection PyUnresolvedReferences
def right_click(hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse right click: %d, %d", x, y)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    __sleep(seconds)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)


# noinspection PyUnresolvedReferences
def mouse_right_down(hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse right down: %d, %d", x, y)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    __sleep(seconds)


# noinspection PyUnresolvedReferences
def mouse_right_up(hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse right up: %d, %d", x, y)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)
    __sleep(seconds)


# noinspection PyUnresolvedReferences
def middle_click(hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    x = int(x)
    y = int(y)
    logger.debug("Mouse middle click: %d, %d", x, y)
    l_param = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, l_param)
    __sleep(seconds)
    win32gui.PostMessage(hwnd, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON, l_param)


# noinspection PyUnresolvedReferences
def scroll_mouse(hwnd, count: int, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
    """
    鼠标滚轮滚动

    :param seconds:
    :param hwnd: 目标窗口句柄
    :param count: 一次滚动多少个单位（正数=向上滚，负数=向下滚）
    :param x: 鼠标 X 坐标
    :param y: 鼠标 Y 坐标
    """
    logger.debug("Mouse scroll: %d, %d, %d", count, x, y)
    w_param = win32api.MAKELONG(0, win32con.WHEEL_DELTA * count)
    l_param = win32api.MAKELONG(x, y) # 鼠标位置，相对于窗口
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, w_param, l_param)
    __sleep(seconds)


###### Other ######


def window_activate(hwnd, seconds: float = 0.0):
    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    __sleep(seconds)


def __sleep(seconds: float):
    if seconds == 0.0:
        return
    if seconds > 0.0:
        time.sleep(seconds)
    else:  # < 0.0
        seconds = round(random.uniform(0.04, 0.06), 4)
        time.sleep(seconds)


def tap_esc(hwnd):
    tap_key(hwnd, win32con.VK_ESCAPE)


def tap_space(hwnd):
    tap_key(hwnd, win32con.VK_SPACE)


# noinspection PyUnresolvedReferences
def get_key_state(vk_code):
    return win32api.GetAsyncKeyState(vk_code) < 0


# noinspection PyUnresolvedReferences
def get_mouse_position():
    x, y = win32api.GetCursorPos()
    logger.debug("Mouse position: %s, %s", x, y)
    return x, y


# noinspection PyUnresolvedReferences
def set_mouse_position(hwnd, x: int, y: int):
    win32api.SetCursorPos((x, y))
