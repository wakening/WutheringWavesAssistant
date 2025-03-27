from abc import ABC, abstractmethod
from asyncio import Task
from enum import Enum

import numpy as np

from src.core.pages import Page, ConditionalAction
from src.core.regions import Position, TextPosition, DynamicPosition


class WindowService(ABC):
    """窗口控制"""

    @property
    @abstractmethod
    def window(self):
        pass

    @abstractmethod
    def refresh(self) -> bool:
        pass

    @abstractmethod
    def get_client_wh(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def get_ratio(self):
        pass

    @abstractmethod
    def get_client_rect_on_screen(self) -> tuple[int, int, int, int]:
        pass

    @abstractmethod
    def get_window_rect(self) -> tuple[int, int, int, int]:
        pass

    @abstractmethod
    def get_focus_rect_on_screen(self, region: tuple[float, float, float, float] | None = None) -> tuple[
        int, int, int, int]:
        pass

    @abstractmethod
    def is_foreground_window(self) -> bool:
        pass

    @abstractmethod
    def close_window(self):
        pass


class ImgService(ABC):
    """图片处理"""

    class CaptureEnum(Enum):
        FG = "foreground"
        BG = "background"

    @abstractmethod
    def screenshot(self, region: tuple[float, float, float, float] | DynamicPosition | None = None) -> np.ndarray:
        pass

    @abstractmethod
    def set_capture_mode(self, capture_mode: CaptureEnum):
        pass

    @abstractmethod
    def match_template(self,
                       img: np.ndarray | None,
                       template_img: np.ndarray | str,
                       region: tuple[int, int, int, int] | None = None,
                       threshold: float = 0.8) -> None | Position:
        pass

    def resize(self, img: np.ndarray) -> np.ndarray:
        return self.resize_by_weight(img)

    @abstractmethod
    def resize_by_dsize(self, img: np.ndarray, dsize: tuple[int, int]) -> np.ndarray:
        pass

    @abstractmethod
    def resize_by_weight(self, img: np.ndarray, target_weight: int = 1280) -> np.ndarray:
        """
        图片等比缩放，将宽度缩小到期望宽度（1280px），不会拉伸图片
        :param img:
        :param target_weight: 期望宽度px
        :return:
        """
        pass

    @abstractmethod
    def resize_by_ratio(self, img: np.ndarray, ratio: float | None = None) -> np.ndarray:
        pass


class ODService(ABC):
    """Object Detection（目标检测）"""

    @abstractmethod
    def search_echo(self, img: np.ndarray | None = None) -> list[int, int, int, int] | None:
        pass

    # @abstractmethod
    # def async_search_echo(self, img: np.ndarray | None = None) -> Task:
    #     pass

    @abstractmethod
    def search_reward(self, img: np.ndarray | None = None) -> tuple[int, int, int, int] | None:
        pass


class OCRService(ABC):
    """Optical Character Recognition（文字识别）"""

    @abstractmethod
    def search_text(self, results: list[TextPosition], target: str) -> TextPosition | None:
        pass

    @abstractmethod
    def search_texts(self, results: list[TextPosition], target: str) -> list[TextPosition]:
        pass

    @abstractmethod
    def find_text(self, targets: str | list[str], img: np.ndarray | None = None,
                  position: Position | DynamicPosition | None = None) -> TextPosition | None:
        pass

    # @abstractmethod
    # def async_find_text(self, targets: str | list[str], img: np.ndarray | None = None,
    #                     position: Position | DynamicPosition | None = None) -> Task:
    #     pass

    @abstractmethod
    def wait_text(self, targets: str | list[str], timeout: int = 3,
                  position: Position | DynamicPosition | None = None, wait_time: float = 0.1) -> TextPosition | None:
        pass

    @abstractmethod
    def ocr(self, img: np.ndarray, position: Position | DynamicPosition | None = None,
            det=True, rec=True, cls=False) -> list[TextPosition]:
        pass

    @abstractmethod
    def print_ocr_result(self, ocr_results: list[TextPosition] | None):
        pass


class PageEventService(ABC):

    @abstractmethod
    def execute(self, **kwargs):
        pass

    @abstractmethod
    def get_pages(self) -> list[Page]:
        pass

    @abstractmethod
    def get_conditional_actions(self) -> list[ConditionalAction]:
        pass


class GameControlService(ABC):
    """游戏基础按键控制，包含常用按键，简化调用，不做精细控制"""

    @abstractmethod
    def up(self, seconds: float = 0.0):
        pass

    @abstractmethod
    def down(self, seconds: float = 0.0):
        pass

    @abstractmethod
    def left(self, seconds: float = 0.0):
        pass

    @abstractmethod
    def right(self, seconds: float = 0.0):
        pass

    @abstractmethod
    def attack(self):
        pass

    @abstractmethod
    def click(self, x: int = 0, y: int = 0):
        pass

    @abstractmethod
    def right_click(self):
        """跑/闪避"""
        pass

    @abstractmethod
    def resonance_skill(self):
        """共鸣技能"""
        pass

    @abstractmethod
    def echo_skill(self):
        """声骸技能"""
        pass

    @abstractmethod
    def resonance_liberation(self):
        """共鸣解放"""
        pass

    @abstractmethod
    def dash_dodge(self):
        """跑/闪避"""
        pass

    @abstractmethod
    def pick_up(self, seconds: float = 0.05):
        """拾取"""
        pass

    @abstractmethod
    def camera_reset(self):
        """重置视角"""
        pass

    @abstractmethod
    def jump(self):
        pass

    @abstractmethod
    def drop(self):
        """落（攀爬时）"""
        pass

    @abstractmethod
    def use_utility(self):
        """使用探索工具"""
        pass

    @abstractmethod
    def map(self):
        """地图"""
        pass

    @abstractmethod
    def events(self):
        """活动"""
        pass

    @abstractmethod
    def guide_book(self):
        """索拉指南"""
        pass

    @abstractmethod
    def esc(self):
        pass

    @abstractmethod
    def team_member1(self):
        """选择队员1"""
        pass

    @abstractmethod
    def team_member2(self):
        pass

    @abstractmethod
    def team_member3(self):
        pass

    @abstractmethod
    def toggle_team_member(self, member: int):
        pass

    @abstractmethod
    def sleep(self, seconds: float = 0.0):
        pass

    @abstractmethod
    def activate(self):
        pass


class PlayerControlService(ABC):
    """玩家键鼠控制，用于战斗，精细控制"""

    @abstractmethod
    def fight_click(self, x: int | float = 0, y: int | float = 0, seconds: float | None = None):
        pass

    @abstractmethod
    def fight_tap(self, key: str, seconds: float | None = None):
        pass


class ExtendedControlService(ABC):
    """拓展操作"""

    @abstractmethod
    def forward_run(self, forward_run_seconds: float):
        pass

    @abstractmethod
    def forward_walk(self, forward_walk_times: int, sleep_seconds: float = None):
        pass

    @abstractmethod
    def get_mouse_position(self):
        pass

    @abstractmethod
    def set_mouse_position(self, x: int, y: int):
        pass

    @abstractmethod
    def get_alt_key_state(self):
        pass

    @abstractmethod
    def set_mouse_position_to_bottom_right(self):
        pass

    @abstractmethod
    def mouse_left_down(self, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        pass

    @abstractmethod
    def mouse_left_up(self, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        pass

    @abstractmethod
    def scroll_mouse(self, count: int, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        pass


class ControlService(GameControlService, PlayerControlService, ExtendedControlService, ABC):
    """键鼠全功能"""

    # 函数太多，控制可见性，对象本身不变
    @abstractmethod
    def game(self) -> GameControlService:
        pass

    @abstractmethod
    def player(self) -> PlayerControlService:
        pass

    @abstractmethod
    def extended(self) -> ExtendedControlService:
        pass
