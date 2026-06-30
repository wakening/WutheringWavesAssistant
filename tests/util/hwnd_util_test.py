import logging
import subprocess
import time

from src.util import hwnd_util, img_util, screenshot_util

logger = logging.getLogger(__name__)


def test_hwnd_util():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    get_window_info(hwnd)
    hwnd_util.enable_dpi_awareness()
    get_window_info(hwnd)


def test_login_hwnd_official():
    logger.debug("\n")
    hwnd_util.enable_dpi_awareness()
    hwnd_list_all, hwnd_list_visible = hwnd_util.get_login_hwnd_official()
    # logger.debug("遍历所有登录窗口")
    # if hwnd_list_all is not None and len(hwnd_list_all) > 0:
    #     for login_hwnd in hwnd_list_all:
    #         get_window_info(login_hwnd)
    #         screenshot_util.screenshot(login_hwnd)
    if hwnd_list_visible is not None and len(hwnd_list_visible) > 0:
        logger.debug("遍历所有登录可见窗口")
        for login_hwnd in hwnd_list_visible:
            get_window_info(login_hwnd)
            img = screenshot_util.screenshot(login_hwnd)
            img = img.copy()
            img = img_util.hide_uid(img)
            img_util.save_img_in_temp(img)
            img_util.show_img(img)
    else:
        logger.debug("未找到登录窗口")


def get_window_info(hwnd):
    hwnd_util.get_sys_dpi()
    hwnd_util.get_window_dpi(hwnd)
    hwnd_util.get_window_wh(hwnd)
    hwnd_util.get_client_wh(hwnd)


def test_get_login_hwnd_official():
    logger.debug("\n")
    hwnd_util.enable_dpi_awareness()
    hwnds, hwnds_visible = hwnd_util.get_login_hwnd_official()
    hwnds_hex = [f"{hwnd:08X}" for hwnd in hwnds]
    logger.debug(hwnds_hex)
    logger.debug(hwnds_hex.index("00BE0AD6"))


def test_pid():
    pid = hwnd_util.get_hwnd_by_exe_name(hwnd_util.CLIENT_WIN64_SHIPPING_EXE)
    logger.debug(pid)


def test_hung():
    import ctypes
    hwnd_util.enable_dpi_awareness()
    hwnd = hwnd_util.get_hwnd()

    def is_window_hung(hwnd):
        return ctypes.windll.user32.IsHungAppWindow(hwnd) != 0  # 非 0 代表卡死

    import psutil

    def is_process_hung(process_name):
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['cpu_percent'] < 0.5  # CPU 长时间接近 0 说明卡死
        return False  # 进程未找到

    for i in range(10):
        if is_window_hung(hwnd):
            print("窗口卡死")
        else:
            print("窗口正常运行")

        if is_process_hung(hwnd_util.CLIENT_WIN64_SHIPPING_EXE):  # 进程名可用 task manager 查
            print("游戏可能卡死")
        else:
            print("游戏正常运行")
        time.sleep(2)


def test_hwnd16_to_int():
    hwnd = int("003B09D6", 16)
    logger.debug("\n")
    logger.debug(f"hwnd: {hwnd}")
    logger.debug("\n")


def test_get_exe_path_from_hwnd():
    # hwnd = hwnd_util.get_hwnd()
    hwnd = int("01500A42", 16)
    logger.debug(hwnd)
    exe_path = hwnd_util.get_exe_path_from_hwnd(hwnd)
    logger.debug(exe_path)


def test_get_hwnd_filter_start_game_by_shipping_exe_path_official():
    # exe_path = r"D:\Program Files\Wuthering Waves\Wuthering Waves Game\Client\Binaries\Win64\Client-Win64-Shipping.exe"
    exe_path = r"D:\Program Files\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe"
    logger.debug(exe_path)
    subprocess.Popen(exe_path, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    time.sleep(5)


def test_get_hwnd_filter_start_game_by_shipping_exe_path_oversea():
    # exe_path = r"D:\Program Files\Wuthering Waves Oversea\Wuthering Waves\Wuthering Waves Game\Client\Binaries\Win64\Client-Win64-Shipping.exe"
    exe_path = r"D:\Program Files\Wuthering Waves Oversea\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe"
    logger.debug(exe_path)
    subprocess.Popen(exe_path, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    time.sleep(5)


def test_get_hwnd_filter_path_official():
    filter_path = r"D:\Program Files\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe"
    hwnd = hwnd_util.get_hwnd(filter_path)
    logger.debug(hwnd)


def test_get_hwnd_filter_path_oversea():
    filter_path = r"D:\Program Files\Wuthering Waves Oversea\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe"
    hwnd = hwnd_util.get_hwnd(filter_path)
    logger.debug(hwnd)

def test_get_wwg_path():
    client_exe = r"D:\Program Files\Wuthering Waves Oversea\Wuthering Waves\Wuthering Waves Game\Client\Binaries\Win64\Client-Win64-Shipping.exe"
    client_wwg_path = hwnd_util.get_wwg_path(client_exe)
    logger.debug(client_wwg_path)
    ww_exe = r"D:\Program Files\Wuthering Waves Oversea\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe"
    ww_wwg_path = hwnd_util.get_wwg_path(ww_exe)
    logger.debug(ww_wwg_path)
    logger.debug(client_wwg_path.resolve() == ww_wwg_path.resolve())


def test_get_hwnds():
    hwnds = hwnd_util.get_hwnds()
    logger.debug(hwnds)


def test_listen_click():
    import win32api
    import win32con
    import win32gui
    import ctypes
    from ctypes import wintypes

    # 目标窗口句柄
    TARGET_HWND = hwnd_util.get_hwnd()

    last_state = False

    while True:
        # 鼠标左键状态（按下瞬间）
        state = win32api.GetAsyncKeyState(0x01)

        # 高位为1表示当前按下
        pressed = (state & 0x8000) != 0

        # 只在“按下瞬间”触发一次
        if pressed and not last_state:

            x, y = win32api.GetCursorPos()

            if TARGET_HWND:
                cx, cy = win32gui.ScreenToClient(TARGET_HWND, (x, y))
            else:
                cx, cy = -1, -1

            print(f"screen=({x},{y}) client=({cx},{cy})")

        last_state = pressed

        time.sleep(0.005)  # 5ms 足够实时了
