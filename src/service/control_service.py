import logging
import time

import numpy as np
import win32con

from src.core.contexts import Context
from src.core.interface import ControlService, WindowService, PlayerControlService, ExtendedControlService, \
    GameControlService
from src.util import keymouse_util

logger = logging.getLogger(__name__)


class BaseControlService:

    def __init__(self, context: Context, window_service: WindowService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__()
        self._context: Context = context
        self._window_service: WindowService = window_service

    def _get_mapping_key(self, reset_key: str, src_key: str | int):
        if self._context is None:
            return src_key
        return self._context.config.keyboard_mapping.get_mapping_key(reset_key, src_key)


class Win32GameControlServiceImpl(GameControlService, BaseControlService):
    """使用win32gui实现的后台消息"""

    def up(self, seconds: float = 0.05):
        key = self._get_mapping_key("W", "W")
        keymouse_util.tap_key(self._window_service.window, key, seconds)
        return self

    def down(self, seconds: float = 0.05):
        key = self._get_mapping_key("S", "S")
        keymouse_util.tap_key(self._window_service.window, key, seconds)
        return self

    def left(self, seconds: float = 0.05):
        key = self._get_mapping_key("A", "A")
        keymouse_util.tap_key(self._window_service.window, key, seconds)
        return self

    def right(self, seconds: float = 0.05):
        key = self._get_mapping_key("D", "D")
        keymouse_util.tap_key(self._window_service.window, key, seconds)
        return self

    def attack(self):
        keymouse_util.click(self._window_service.window, seconds=0.05)
        return self

    def click(self, x: int = 0, y: int = 0):
        keymouse_util.click(self._window_service.window, x, y, seconds=0.05)
        return self

    def right_click(self):
        keymouse_util.right_click(self._window_service.window, seconds=0.05)
        return self

    def resonance_skill(self):
        """共鸣技能"""
        key = self._get_mapping_key("E", "E")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def echo_skill(self):
        """声骸技能"""
        key = self._get_mapping_key("Q", "Q")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def resonance_liberation(self):
        """共鸣解放"""
        key = self._get_mapping_key("R", "R")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def dash_dodge(self):
        key = self._get_mapping_key("LEFT_SHIFT", win32con.VK_LSHIFT)
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def pick_up(self, seconds: float = 0.05):
        key = self._get_mapping_key("F", "F")
        keymouse_util.tap_key(self._window_service.window, key, seconds)
        return self

    def camera_reset(self):
        """重置视角"""
        keymouse_util.middle_click(self._window_service.window, seconds=0.05)
        return self

    def jump(self):
        key = self._get_mapping_key("SPACE", win32con.VK_SPACE)
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def drop(self):
        """落（攀爬时）"""
        key = self._get_mapping_key("X", "X")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def use_utility(self):
        """使用探索工具"""
        key = self._get_mapping_key("T", "T")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def map(self):
        """地图"""
        key = self._get_mapping_key("M", "M")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def events(self):
        """活动"""
        key = self._get_mapping_key("F1", win32con.VK_F1)
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def guide_book(self):
        """索拉指南"""
        key = self._get_mapping_key("F2", win32con.VK_F2)
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def esc(self):
        keymouse_util.tap_key(self._window_service.window, win32con.VK_ESCAPE, seconds=0.05)
        return self

    def team_member1(self):
        key = self._get_mapping_key("1", "1")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def team_member2(self):
        key = self._get_mapping_key("2", "2")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def team_member3(self):
        key = self._get_mapping_key("3", "3")
        keymouse_util.tap_key(self._window_service.window, key, seconds=0.05)
        return self

    def toggle_team_member(self, member: int):
        match member:
            case 1:
                self.team_member1()
            case 2:
                self.team_member2()
            case 3:
                self.team_member3()
            case _:
                logger.warning("Unknown member index")
        return self

    def sleep(self, seconds: float = 0.0):
        if seconds > 0.0:
            time.sleep(seconds)
        return self

    def activate(self):
        keymouse_util.window_activate(self._window_service.window)
        return self


class Win32PlayerControlServiceImpl(PlayerControlService, BaseControlService):

    def fight_click(self, x: int | float = 0, y: int | float = 0, seconds: float | None = None):
        if seconds is None:
            while (seconds := np.round(np.random.uniform(0, 0.01), 5)) == 0: pass
        keymouse_util.click(self._window_service.window, x, y, seconds)
        return self

    def fight_tap(self, key: str, seconds: float | None = None):
        key = self._get_mapping_key(key, key)
        if seconds is None:
            while (seconds := np.round(np.random.uniform(0, 0.01), 5)) == 0: pass
        keymouse_util.tap_key(self._window_service.window, key, seconds)


class Win32ExtendedControlServiceImpl(ExtendedControlService, BaseControlService):

    def forward_run(self, forward_run_seconds: float):
        keymouse_util.key_down(self._window_service.window, "w")
        time.sleep(0.1)
        keymouse_util.key_down(self._window_service.window, win32con.VK_LSHIFT)
        if forward_run_seconds > 1.3:
            time.sleep(1.3)
            keymouse_util.key_up(self._window_service.window, win32con.VK_LSHIFT)
            time.sleep(forward_run_seconds - 1)
        else:
            time.sleep(forward_run_seconds)
        keymouse_util.key_up(self._window_service.window, win32con.VK_LSHIFT)
        keymouse_util.key_up(self._window_service.window, "w")
        time.sleep(0.2)
        keymouse_util.key_up(self._window_service.window, win32con.VK_LSHIFT)
        keymouse_util.key_up(self._window_service.window, "w")

    def forward_walk(self, forward_walk_times: int, sleep_seconds: float = None):
        for _ in range(forward_walk_times):
            keymouse_util.tap_key(self._window_service.window, "w", 0.1)
            time.sleep(0.05 if sleep_seconds is None else sleep_seconds)

    def get_mouse_position(self):
        pos = keymouse_util.get_mouse_position()
        logger.debug("当前鼠标坐标: %s", pos)
        return pos

    def set_mouse_position(self, x: int, y: int):
        keymouse_util.set_mouse_position(self._window_service.window, x, y)

    def get_alt_key_state(self):
        key_state = keymouse_util.get_key_state(win32con.VK_MENU)
        if key_state:
            logger.debug("ALT正被按下")
        return key_state

    def set_mouse_position_to_bottom_right(self):
        x1, y1, x2, y2 = self._window_service.get_client_rect_on_screen()
        x, y = x2 - 1, y2 // 2
        keymouse_util.set_mouse_position(self._window_service.window, x, y)
        time.sleep(0.001)
        keymouse_util.set_mouse_position(self._window_service.window, x, y)
        time.sleep(0.1)

    def mouse_left_down(self, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        keymouse_util.mouse_left_down(self._window_service.window, x, y, seconds)

    def mouse_left_up(self, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        keymouse_util.mouse_left_up(self._window_service.window, x, y, seconds)

    def scroll_mouse(self, count: int, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        keymouse_util.scroll_mouse(self._window_service.window, count, x, y, seconds)


class Win32ControlServiceImpl(Win32GameControlServiceImpl,
                              Win32PlayerControlServiceImpl,
                              Win32ExtendedControlServiceImpl,
                              ControlService):

    def game(self) -> ControlService:
        return self

    def player(self) -> PlayerControlService:
        return self

    def extended(self) -> ExtendedControlService:
        return self
