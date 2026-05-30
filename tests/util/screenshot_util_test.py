import logging
import time

import win32gui

from src.util import file_util, hwnd_util, img_util, screenshot_util

logger = logging.getLogger(__name__)


def test_screenshot_util():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    hwnd_util.get_sys_dpi()
    hwnd_util.get_window_dpi(hwnd)
    hwnd_util.get_window_wh(hwnd)
    hwnd_util.get_client_wh(hwnd)

    hwnd_util.enable_dpi_awareness()

    hwnd_util.get_sys_dpi()
    hwnd_util.get_window_dpi(hwnd)
    hwnd_util.get_window_wh(hwnd)
    hwnd_util.get_client_wh(hwnd)

    # # 获取窗口的Placement信息以确定正常状态的尺寸
    # import win32con
    # placement = win32gui.GetWindowPlacement(hwnd)
    # if placement[1] == win32con.SW_SHOWMINIMIZED:
    #     # 使用正常状态下的窗口尺寸
    #     rect = placement[4]
    #     width = rect[2] - rect[0]
    #     height = rect[3] - rect[1]

    # 获取当前客户区尺寸
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    width = right - left
    height = bot - top

    logger.debug("width: %s, height: %s", width, height)

    img = screenshot_util.screenshot(hwnd)
    img = img.copy()
    img = img_util.hide_uid(img)
    img_util.save_img_in_temp(img)
    img_util.show_img(img)


def test_screenshot_util_all():
    logger.debug("\n")
    hwnd_util.enable_dpi_awareness()
    hwnds = hwnd_util.get_hwnds()
    for hwnd in hwnds:
        img = screenshot_util.screenshot(hwnd)
        img = img.copy()
        img = img_util.hide_uid(img)
        img_util.save_img_in_temp(img)
        img_util.show_img(img)


def test_screenshot_util_bitblt():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    hwnd_util.enable_dpi_awareness()

    hwnd_util.get_sys_dpi()
    hwnd_util.get_window_dpi(hwnd)
    hwnd_util.get_window_wh(hwnd)
    hwnd_util.get_client_wh(hwnd)

    # 获取当前客户区尺寸
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    width = right - left
    height = bot - top

    logger.debug("width: %s, height: %s", width, height)

    img = screenshot_util.screenshot_bitblt(hwnd)
    img = img.copy()
    img = img_util.hide_uid(img)
    img_util.save_img_in_temp(img)
    img_util.show_img(img)


def test_hide_uid():
    logger.debug("\n")
    img = img_util.read_img(file_util.get_assets_screenshot("Revival_001.png"))
    # img = img.copy()
    img = img_util.hide_uid(img)
    img_util.save_img_in_temp(img)
    img_util.show_img(img)


# def test_dump_screenshot():
#     logger.debug("\n")
#     hwnd = hwnd_util.get_hwnd()
#     hwnd_util.enable_dpi_awareness()
#     for i in range(100000):
#         img = screenshot_util.screenshot(hwnd)
#         img = img.copy()
#         img = img_util.hide_uid(img)
#         img_util.save_img_in_temp(img)
#         time.sleep(0.1)


def test_listener():
    from pynput.mouse import Listener, Button
    import threading
    import winsound
    print("监听鼠标第二个侧键，按 Ctrl+C 退出...")

    hwnd = hwnd_util.get_hwnd()
    hwnd_util.enable_dpi_awareness()

    def on_side_button():
        # 播放系统提示音（像相机快门）
        winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)

        """鼠标第二个侧键触发执行的函数"""
        img = screenshot_util.screenshot(hwnd)
        img = img.copy()
        img = img_util.hide_uid(img)
        img_util.save_img_in_temp(img)
        print("截图已保存")

    def on_click(x, y, button, pressed):
        """鼠标点击事件回调"""
        if pressed and button == Button.x2:  # Button.x2 是第二个侧键
            # 使用线程避免阻塞监听器
            threading.Thread(target=on_side_button).start()

    # 创建并启动监听器
    with Listener(on_click=on_click) as listener:
        try:
            listener.join()  # 等待监听器运行
        except KeyboardInterrupt:
            print("\n程序已退出")