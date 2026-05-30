from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, overload

import numpy as np

from src.core.boss import RouteStep, RestartParam
from src.core.geometry import BBox, Scaler, TextBox, Detection
from src.core.i18n import I18nTr, Language
from src.core.pages import Page, ConditionalAction, OcrResult
from src.core.regions import Position, TextPosition, DynamicPosition


class WindowService(ABC):
    """窗口控制"""

    @property
    @abstractmethod
    def window(self):
        pass

    @property
    @abstractmethod
    def handle(self):
        pass

    @property
    @abstractmethod
    def scaler(self) -> Scaler:
        pass

    @property
    @abstractmethod
    def tr(self) -> I18nTr:
        pass

    @abstractmethod
    def refresh(self) -> bool:
        pass

    @abstractmethod
    def get_lang(self) -> Language:
        pass

    @abstractmethod
    def set_lang(self, lang: Language):
        pass

    @abstractmethod
    def get_client_wh(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def window_bbox(self) -> BBox:
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
    def screenshot_window(self, window) -> np.ndarray:
        """
        从指定窗口截图
        :param window: 窗口句柄
        :return:
        """
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
    def search_echo(self, img: np.ndarray | None = None, confidence: float = None) -> tuple[int, int, int, int] | None:
        pass

    @abstractmethod
    def search_reward(self, img: np.ndarray | None = None) -> Detection | None:
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

    @abstractmethod
    def wait_text(self, targets: str | list[str], timeout: float = 3.0,
                  position: Position | DynamicPosition | None = None, wait_time: float = 0.1) -> TextPosition | None:
        pass

    @abstractmethod
    def ocr(self, img: np.ndarray, position: Position | DynamicPosition | None = None,
            det=True, rec=True, cls=False) -> list[TextPosition]:
        pass

    @abstractmethod
    def query(
            self,
            img: np.ndarray,
            roi: BBox | None = None,
            det=True,
            rec=True,
            cls=False,
            resize=True,
    ) -> OcrResult:
        """
        找出图片指定区域内的所有文本
        :param img:
        :param roi:
        :param det:
        :param rec:
        :param cls:
        :param resize: 1280x720以上分辨率图片是否缩小，默认开启，牺牲精度提升识别速度，若需要识别小字，必须关闭，用原图识别以保证精度
        :return:
        """
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


class PageService(ABC):

    @abstractmethod
    def matches(self, ocr_result: OcrResult) -> dict[str, dict[str, TextBox]]:
        pass

    @abstractmethod
    def match(self, ocr_result: OcrResult) -> Optional[tuple[str, dict[str, TextBox]]]:
        pass

    @abstractmethod
    def is_match(self, ocr_result: OcrResult, page_key: str) -> Optional[dict[str, TextBox]]:
        pass


class GlobalPageService(PageService):

    @abstractmethod
    def global_page_action(self, ocr_result: OcrResult, **kwargs) -> bool:
        pass


class EchoMergeService(PageService, ABC):

    pass


class GuidebookService(PageService, ABC):

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

    @overload
    def click(self, x: int, y: int): ...

    @overload
    def click(self, point: tuple[int, int]): ...

    @abstractmethod
    def click(self, *args):
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
        """重置视角/锁定"""
        pass

    @abstractmethod
    def jump(self):
        pass

    @abstractmethod
    def drop(self):
        """下落（攀爬时）"""
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
    def guidebook(self):
        """索拉指南"""
        pass

    @abstractmethod
    def mail(self):
        """邮件"""
        pass

    @abstractmethod
    def resonator(self):
        """共鸣者"""
        pass

    @abstractmethod
    def quests(self):
        """任务"""
        pass

    @abstractmethod
    def esc(self):
        pass

    @abstractmethod
    def team(self):
        """编队"""
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
    def enter(self):
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
    def fight_right_click(self, x: int | float = 0, y: int | float = 0, seconds: float | None = None):
        pass

    @abstractmethod
    def fight_tap(self, key: str, seconds: float | None = None):
        pass

    @abstractmethod
    def key_down(self, key: str, seconds: float | None = None):
        pass

    @abstractmethod
    def key_up(self, key: str, seconds: float | None = None):
        pass


class ExtendedControlService(ABC):
    """拓展操作键鼠控制"""

    @abstractmethod
    def forward_run(self, forward_run_seconds: float, key: str | None = None):
        pass

    @abstractmethod
    def forward_walk(self, forward_walk_times: int, key: str | None = None, sleep_seconds: float = None):
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
    def mouse_right_down(self, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        pass

    @abstractmethod
    def mouse_right_up(self, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        pass

    @abstractmethod
    def scroll_mouse(self, count: int, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        pass

    @abstractmethod
    def click_window(self, window, x: int = 0, y: int = 0):
        """在指定窗口内点击"""
        pass

    @abstractmethod
    def input_text(self, text: str, seconds: float = 0.0):
        """输入文本"""
        pass

    @abstractmethod
    def activate_window(self, window):
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


class BossInfoService(ABC):

    @abstractmethod
    def get_boss_name_zh_en(self, boss_name_zh: str) -> str:
        pass

    @abstractmethod
    def is_nightmare(self, boss_name: str) -> bool:
        pass

    @abstractmethod
    def is_auto_pickup(self, boss_name: str) -> bool:
        pass

    @abstractmethod
    def get_fast_travel_routes(self) -> dict[str, list[RouteStep]]:
        pass

    @abstractmethod
    def get_restart_params(self) -> dict[str, RestartParam]:
        pass

    @abstractmethod
    def get_after_restart_routes(self) -> dict[str, list[RouteStep]]:
        pass


class CombatService(ABC):

    @abstractmethod
    def combat_system(self):
        pass
