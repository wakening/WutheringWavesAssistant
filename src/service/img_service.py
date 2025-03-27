import logging
from enum import Enum

import numpy as np

from src.core.contexts import Context
from src.core.interface import ImgService, WindowService
from src.core.regions import Position, DynamicPosition
from src.util import screenshot_util, img_util, file_util, mss_util
from src.util.wrap_util import timeit

logger = logging.getLogger(__name__)


class ImgServiceImpl(ImgService):

    def __init__(self, context: Context, window_service: WindowService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__()
        self._context: Context = context
        self._window_service: WindowService = window_service
        self._template_img_cache: dict[str, np.ndarray] = {}
        self._mss_camera = mss_util.create_mss()
        # self._dx_camera = dxcam_util.create_camera()
        self._capture_mode: Enum = ImgService.CaptureEnum.BG

    @timeit(ignore=3)
    def screenshot(self, region: tuple[float, float, float, float] | DynamicPosition | None = None) -> np.ndarray:
        if isinstance(region, DynamicPosition):
            region = region.rate
        focus_rect_on_screen = self._window_service.get_focus_rect_on_screen(region)
        if self._capture_mode == ImgService.CaptureEnum.FG:
            return self._foreground_screenshot(focus_rect_on_screen)
        else:
            return self._background_screenshot(focus_rect_on_screen)

    def set_capture_mode(self, capture_mode: ImgService.CaptureEnum):
        self._capture_mode = capture_mode

    def _foreground_screenshot(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
        # return dxcam_util.screenshot(self._dx_camera, region)
        # return screenshot_util.screenshot_bitblt(self._window_service.window, region)
        return mss_util.screenshot(self._mss_camera, region)

    def _background_screenshot(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
        return screenshot_util.screenshot(self._window_service.window)

    def match_template(self,
                       img: np.ndarray | None,
                       template_img: np.ndarray | str,
                       region: tuple[int, int, int, int] | None = None,
                       threshold: float = 0.8
                       ) -> None | Position:
        """
        使用 opencv matchTemplate 方法在指定区域内进行模板匹配并返回匹配结果
        :param img:  大图片
        :param template_img: 小图片，若是字符串，必需是模板目录内的文件名（无路径的含后缀的纯文件名）
        :param region: 搜索区域（x1, y1, x2, y2），默认为 None 表示全图搜索
        :param threshold:  阈值
        :return: Position 或 None
        """
        if img is None:
            img = self.resize(self.screenshot())
        if isinstance(template_img, str):
            if template_img not in self._template_img_cache:
                self._template_img_cache[template_img] = img_util.read_img(file_util.get_assets_template(template_img))
            template_img = self._template_img_cache[template_img]
        # 如果提供了region参数，则裁剪出指定区域，否则使用整幅图像
        if region:
            cropped_img = img[region[1]:region[3], region[0]:region[2]]
        else:
            cropped_img = img
        confidence, position = img_util.match_template(cropped_img, template_img)
        if confidence < threshold:
            return None
        return Position.build(position[0], position[1], position[2], position[3], confidence=confidence)

    def resize_by_dsize(self, img: np.ndarray, dsize: tuple[int, int]) -> np.ndarray:
        return img_util.resize(img, dsize)

    def resize_by_weight(self, img: np.ndarray, target_weight: int = 1280) -> np.ndarray:
        return img_util.resize_by_weight(img, target_weight)

    def resize_by_ratio(self, img: np.ndarray, ratio: float | None = None) -> np.ndarray:
        if ratio is None:
            ratio = self._window_service.get_ratio()
        return img_util.resize_by_ratio(img, ratio)
