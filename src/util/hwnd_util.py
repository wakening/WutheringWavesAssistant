"""
window窗口工具

@software: PyCharm
@file: hwnd_util.py
@time: 2024/7/06 下午1:00
@author wakening
"""
import ctypes
import logging
import re
import time
import traceback
from ctypes import windll

import psutil
import win32api
import win32con
import win32gui
import win32process

logger = logging.getLogger(__name__)

# wuwa相关进程
CLIENT_WIN64_SHIPPING_EXE = "Client-Win64-Shipping.exe"  # 登录客户端
WUTHERING_WAVES_EXE = "Wuthering Waves.exe"  # 游戏主程序
LAUNCHER_EXE = "launcher.exe"  # 启动器

# wuwa窗口相关属性
WUWA_HWND_CLASS_NAME = "UnrealWindow"
WUWA_HWND_TITLE = ["鸣潮  ", "Wuthering Waves  "]
# 国服登录窗口
OFFICIAL_LOGIN_HWND_CLASS_NAME = "#32770"
OFFICIAL_LOGIN_HWND_TITLE = ""
# b服登录窗口
BILIBILI_LOGIN_HWND_CLASS_NAME = "CLoginDlg_P_8340_\\d{10}"  # CLoginDlg_P_8340_1720374432
BILIBILI_LOGIN_HWND_TITLE = "bilibili游戏 登录_弹框"
# UE4-Client崩溃窗口
UE4_CLIENT_HWND_CLASS_NAME = "#32770"
UE4_CLIENT_HWND_TITLE = "UE4-Client Game已崩溃，即将关闭"

# dpi
STANDARD_DPI = 96  # 96 是标准 DPI


def get_pid_by_exe_name(exe_name: str):
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] == exe_name:
            pro_pid = proc.info['pid']
            # print(f"pid: {pro_pid}")
            return pro_pid
    return None


# 获取当前系统所有窗口句柄
def get_all_hwnd() -> list:
    def get_hwnd_callback(cb_hwnd, cb_window_list):
        # _, found_pid = win32process.GetWindowThreadProcessId(cb_hwnd)
        # print(f"found_pid: {found_pid}")
        cb_window_list.append(cb_hwnd)

    window_list: list = []
    win32gui.EnumWindows(get_hwnd_callback, window_list)
    return window_list


def get_hwnd_by_exe_name(exe_name: str) -> list | None:
    ge_pid = get_pid_by_exe_name(exe_name)
    if ge_pid is None:
        return None
    ge_hwnd_list: list = get_all_hwnd()
    rt_hwnd_list: list = []
    for ge_hwnd in ge_hwnd_list:
        _, found_pid = win32process.GetWindowThreadProcessId(ge_hwnd)
        if found_pid == ge_pid:
            rt_hwnd_list.append(ge_hwnd)
    return rt_hwnd_list


def get_hwnd_by_class_and_title(class_name: str, titles: list[str] | str):
    if isinstance(titles, str):
        titles = [titles]
    window = None
    for title in titles:
        logger.debug("window class: %s, title: %s", class_name, title)
        window = win32gui.FindWindow(class_name, title)
        logger.debug("window: %s", window)
        if window is not None and window != 0:
            break
    return window


# 获取游戏窗口句柄
def get_hwnd():
    return get_hwnd_by_class_and_title(WUWA_HWND_CLASS_NAME, WUWA_HWND_TITLE)


# 官服 获取账号登录界面窗口句柄 by wakening
def get_login_hwnd_official() -> tuple[list | None, list | None]:
    hwnd_list_all = get_hwnd_by_exe_name(CLIENT_WIN64_SHIPPING_EXE)
    if hwnd_list_all is None or len(hwnd_list_all) == 0:
        return None, None
    hwnd_list_visible = []
    for hwnd in hwnd_list_all:
        logger.debug("win32gui.IsWindow(hwnd): %s", win32gui.IsWindow(hwnd))
        logger.debug("win32gui.IsWindowEnabled(hwnd): %s", win32gui.IsWindowEnabled(hwnd))
        logger.debug("win32gui.IsWindowVisible(hwnd): %s", win32gui.IsWindowVisible(hwnd))
        window_class = win32gui.GetClassName(hwnd)
        logger.debug(f"window: {hwnd}, window class: {window_class}, title: {win32gui.GetWindowText(hwnd)}")
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            # window class: UnrealWindow, title: 鸣潮
            # window class: #32770, title:
            # 目前游戏v1.1版本有游戏本体窗口，账号登录窗口等
            # 账号登录窗口没有标题，类名#32770不确定是否会变，无法准确定位
            # 考虑到后续窗口可能变多，返回数组 by wakening
            if window_class != WUWA_HWND_CLASS_NAME:
                hwnd_list_visible.append(hwnd)
    return hwnd_list_all, hwnd_list_visible


# b服 获取账号登录界面窗口句柄 by wakening
def get_login_hwnd_bilibili():
    windows_list: list = get_all_hwnd()
    for wd_hwnd in windows_list:
        window_class = win32gui.GetClassName(wd_hwnd)
        pattern = re.compile(rf"^{BILIBILI_LOGIN_HWND_CLASS_NAME}$")
        match = pattern.match(window_class)
        if match:
            logger.debug("window class: %s, title: %s", window_class, win32gui.GetWindowText(wd_hwnd))
            return wd_hwnd
    return None


# 国际服 获取账号登录界面窗口句柄 by wakening
def get_login_hwnd_oversea():
    windows_list: list = get_all_hwnd()
    for hwnd in windows_list:
        pass
    return None


# UE4-Client Game已崩溃窗口句柄 by wakening
def get_ue4_client_crash_hwnd():
    windows_list: list = get_all_hwnd()
    for hwnd in windows_list:
        title = win32gui.GetWindowText(hwnd)
        if title is not None and title == UE4_CLIENT_HWND_TITLE:
            return hwnd
    return None


# 强制关闭进程
# noinspection PyUnresolvedReferences
def force_close_process(hwnd):
    # 卡死时发送窗口消息无效
    # win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    # 根据窗口句柄获取进程ID
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    # 获取进程句柄
    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
    win32api.TerminateProcess(handle, -1)
    win32api.CloseHandle(handle)


def window_activate(hwnd):
    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    time.sleep(0.05)


PROCESS_DPI_UNAWARE = 0
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2


def enable_dpi_awareness():
    """
    启用全局DPI感知，支持每显示器DPI感知
    """
    logger.debug("Enable global DPI awareness")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    except Exception:
        logger.error("Failed to enable DPI awareness: %s", traceback.format_exc())


# 窗口的大小和位置在不同的缩放设置下可能会分为“实际大小”和“逻辑大小”：
#
# 实际大小（Physical Size）：
# 实际大小是根据显示器的物理像素来度量的尺寸。它考虑了系统的 DPI 设置（例如 100%, 150%, 200% 等）。在缩放较高的情况下，实际大小会相应变大，以适应更高的像素密度。
# 逻辑大小（Logical Size）：
#
# 逻辑大小是应用程序内部使用的坐标系统，通常不受 DPI 缩放影响。它是按照设计时的标准像素（通常是 96 DPI）来计算的，不考虑显示器的缩放因子。
# 在高 DPI 设置下，应用程序会将逻辑像素映射到实际的物理像素上。因此，逻辑像素看起来会更小，实际物理像素则会更大。
# 获取窗口物理矩形
def get_window_rect(hwnd) -> tuple[int, int, int, int]:
    """获取特定窗口的绝对坐标，左上右下，（包括标题栏、边框等非客户区"""
    return win32gui.GetWindowRect(hwnd)


def get_client_rect(hwnd) -> tuple[int, int, int, int]:
    """获取特定窗口客户区的相对坐标，即内容区域（如编辑框、绘图区等），不包含非客户区（标题栏、边框等）"""
    return win32gui.GetClientRect(hwnd)


def get_window_wh(hwnd) -> (int, int):
    """获取特定窗口的宽高px"""
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    logger.debug("window rect: (%s, %s, %s, %s)", left, top, right, bot)
    width = right - left
    height = bot - top
    logger.debug("window w, h: %d, %d", width, height)
    return width, height


def get_client_wh(hwnd):
    """获取特定窗口客户区的宽高px"""
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    logger.debug("client rect: (%s, %s, %s, %s)", left, top, right, bot)
    width = right - left
    height = bot - top
    logger.debug("client w, h: %d, %d", width, height)
    return width, height


def get_screen_wh():
    """电脑屏幕的宽高px（分辨率）"""
    # noinspection PyUnresolvedReferences
    width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    # noinspection PyUnresolvedReferences
    height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    logger.debug("screen w, h: %d, %d", width, height)
    return width, height


def get_client_rect_on_screen(hwnd) -> tuple[int, int, int, int]:
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    # 将客户区左上角 (0, 0) 转换为屏幕坐标
    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
    client_left, client_top = client_point
    # 计算客户区右下的屏幕坐标
    client_right = client_point[0] + (right - left)
    client_bottom = client_point[1] + (bottom - top)
    return client_left, client_top, client_right, client_bottom


def get_focus_rect_on_screen(hwnd, region: tuple[float, float, float, float] | None = None) -> tuple[
    int, int, int, int]:
    """获取窗口 相对区域 的 绝对屏幕坐标"""
    client_rect_on_screen = get_client_rect_on_screen(hwnd)
    if region is None:
        return client_rect_on_screen
    w = client_rect_on_screen[2] - client_rect_on_screen[0]
    h = client_rect_on_screen[3] - client_rect_on_screen[1]
    return (
        int(client_rect_on_screen[0] + w * region[0]),
        int(client_rect_on_screen[1] + h * region[1]),
        int(client_rect_on_screen[0] + w * region[2]),
        int(client_rect_on_screen[1] + h * region[3]),
    )


def get_sys_dpi():
    dpi = windll.user32.GetDpiForSystem()
    logger.debug(f"System DPI: {dpi}")
    return dpi


def get_window_dpi(hwnd):
    dpi = windll.user32.GetDpiForWindow(hwnd)
    logger.debug(f"Window DPI: {dpi}")
    return dpi


def set_hwnd_left_top(hwnd=None):
    logger.debug("将窗口移动至左上角")
    if hwnd is None:
        hwnd = get_hwnd()
    win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW)


def set_hwnd_center(hwnd=None):
    logger.debug("将窗口居中")
    if hwnd is None:
        hwnd = get_hwnd()
    # 获取屏幕工作区的宽度和高度（排除任务栏）
    # noinspection PyUnresolvedReferences
    screen_rect = win32api.GetMonitorInfo(win32api.EnumDisplayMonitors()[0][0])['Work']
    work_width = screen_rect[2] - screen_rect[0]  # 工作区宽度
    work_height = screen_rect[3] - screen_rect[1]  # 工作区高度

    # 获取窗口的宽度和高度
    window_rect = win32gui.GetWindowRect(hwnd)  # 获取窗口的矩形框
    window_width = window_rect[2] - window_rect[0]  # 右边界 - 左边界 = 宽度
    window_height = window_rect[3] - window_rect[1]  # 下边界 - 上边界 = 高度

    # 计算窗口的新位置，使其居中（在工作区范围内）
    x = (work_width - window_width) // 2 + screen_rect[0]
    y = (work_height - window_height) // 2 + screen_rect[1]

    # 设置窗口位置（保持原来的大小，不改变层级，显示窗口）
    win32gui.SetWindowPos(hwnd, 0, x, y, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW)


def is_foreground_window(hwnd):
    """判断窗口是否为前台窗口"""
    if hwnd is None:
        return False
    # 获取当前前台窗口的句柄
    foreground_hwnd = win32gui.GetForegroundWindow()
    # 判断目标窗口句柄是否与前台窗口句柄相同
    return hwnd == foreground_hwnd
