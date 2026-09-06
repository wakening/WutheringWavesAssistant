import logging
import time

import win32con
import win32gui

from src.util import hwnd_util, keymouse_util

logger = logging.getLogger(__name__)


def test_keymouse_util():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    keymouse_util.window_activate(hwnd)

    keymouse_util.tap_key(hwnd, "A")
    time.sleep(0.5)
    keymouse_util.tap_key(hwnd, "A")
    time.sleep(1)

    keymouse_util.tap_key(hwnd, "S")
    time.sleep(0.5)
    keymouse_util.tap_key(hwnd, "S")
    time.sleep(1)

    keymouse_util.tap_key(hwnd, "D")
    time.sleep(0.5)
    keymouse_util.tap_key(hwnd, "D")
    time.sleep(1)

    keymouse_util.tap_key(hwnd, "W")
    time.sleep(0.5)
    keymouse_util.tap_key(hwnd, "W")
    time.sleep(1)

    keymouse_util.middle_click(hwnd)
    time.sleep(2)

    for i in range(5):
        keymouse_util.scroll_mouse(hwnd, -5)
        time.sleep(0.01)
    time.sleep(2)
    for i in range(5):
        keymouse_util.scroll_mouse(hwnd, 5)
        time.sleep(0.01)
    time.sleep(2)

    keymouse_util.tap_space(hwnd)
    time.sleep(2)
    keymouse_util.tap_space(hwnd)
    time.sleep(2)

    keymouse_util.tap_esc(hwnd)
    time.sleep(2)
    keymouse_util.tap_esc(hwnd)
    time.sleep(1)


def test_get_set_mouse_position():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    time.sleep(5)
    for i in range(3):
        keymouse_util.window_activate(hwnd)
        keymouse_util.get_mouse_position()
        x1, y1, x2, y2 = hwnd_util.get_client_rect_on_screen(hwnd)
        keymouse_util.set_mouse_position(x2, (y1 + y2) // 2)
        time.sleep(0.5)
        keymouse_util.get_mouse_position()
        logger.debug("\n")
        time.sleep(1)

def test_scroll2():
    # .scroll_mouse(20, x, y)
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    hwnd_util.enable_dpi_awareness()
    # hwnd_util.set_window_left_top(hwnd)
    time.sleep(0.5)
    keymouse_util.window_activate(hwnd)
    time.sleep(1)
    x, y = hwnd_util.get_client_wh(hwnd)
    x, y = x // 2, y // 2
    keymouse_util.click(hwnd, x, y)
    time.sleep(2)
    keymouse_util.scroll_mouse(hwnd, 100, x, y)
    time.sleep(2)
    keymouse_util.scroll_mouse(hwnd, -100, x, y)
    time.sleep(2)
    keymouse_util.scroll_mouse(hwnd, 30, x, y)
    time.sleep(2)


def find_child_window(parent_hwnd, class_name=None, window_title=None):
    """
    查找子窗口句柄
    :param parent_hwnd: 父窗口句柄
    :param class_name: 控件类名（如 "Edit", "RichEdit"）
    :param window_title: 窗口标题（可选）
    :return: 子窗口句柄，找不到返回 None
    """
    child = win32gui.FindWindowEx(parent_hwnd, None, class_name, window_title)
    return child

def enum_child_windows(hwnd):
    children = []
    def callback(hwnd_child, _):
        class_name = win32gui.GetClassName(hwnd_child)
        title = win32gui.GetWindowText(hwnd_child)
        children.append((hwnd_child, class_name, title))
        return True
    win32gui.EnumChildWindows(hwnd, callback, None)
    return children



def test_post_text():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    hwnd_util.enable_dpi_awareness()
    time.sleep(0.5)
    keymouse_util.window_activate(hwnd)
    time.sleep(0.5)
    keymouse_util.click(hwnd, 176, 102, 0.05)
    time.sleep(0.5)

    text = "芬莱克"
    # win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, None, text)

    for char in text:
        # 发送 WM_CHAR 消息（模拟键盘输入）
        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.03)  # 避免输入过快被游戏丢弃

    time.sleep(0.3)
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    time.sleep(0.03)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    time.sleep(0.3)


def test_print_mouse_position():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    client_rect_on_screen = hwnd_util.get_client_rect_on_screen(hwnd)
    logger.debug(f"client_rect_on_screen: {client_rect_on_screen}")
    x1, y1, x2, y2 = client_rect_on_screen
    logger.debug(f"client_center_on_screen: {((x1 + x2) // 2, (y1 + y2) // 2)}")
    try:
        while True:
            logger.debug(f"mouse_position: {keymouse_util.get_mouse_position()}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        logger.debug(f"client_rect_on_screen: {client_rect_on_screen}")
        logger.debug(f"client_center_on_screen: {((x1 + x2) // 2, (y1 + y2) // 2)}")


def test_activate():
    hwnd = hwnd_util.get_hwnd()
    win32gui.PostMessage(
        hwnd,
        win32con.WM_NCACTIVATE,
        1,
        0,
    )
    win32gui.PostMessage(
        hwnd,
        win32con.WM_ACTIVATE,
        win32con.WA_ACTIVE,
        0,
    )
    win32gui.PostMessage(
        hwnd,
        win32con.WM_SETFOCUS,
        0,
        0,
    )
    win32gui.PostMessage(
        hwnd,
        win32con.WM_MOUSEACTIVATE,
        win32con.MA_ACTIVATE,
        0,
    )