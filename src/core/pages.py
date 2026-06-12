import json
import logging
import re
import time
from abc import abstractmethod, ABC
from functools import lru_cache
from re import Pattern
from typing import Callable, Dict, List, Optional, Any

import numpy as np
from pydantic import BaseModel, Field, PrivateAttr

from src.core.color import ColorRule, ColorMatch, Color, RuleMode
from src.core.exceptions import StopError
from src.core.geometry import TextBox, BBox, Scaler, AnchorBBox, AnchorPoint, Align, PointKind, Point
from src.core.i18n import I18nPage, I18nPageEchoMerge, Language
from src.core.movement import RouteExecutor, MoveStep
from src.core.regions import Position, DynamicPosition, TextPosition, Pos
from src.util import img_util, file_util

logger = logging.getLogger(__name__)


class TextMatch(BaseModel):
    name: str | None = Field(None, title="文本名称，key")
    text: str | Pattern = Field(title="文本正则",
                                description="匹配用的，默认应传字符串，方便管理，除非特殊要求，才传入正则对象")
    must: bool = Field(True, title="默认True必需匹配上；False表示没有也可以，不可单独使用",
                       description="False用于将尽可能需要的文本坐标放到入参集合中，减少后续的ocr次数，不能用于定位页面")
    position: DynamicPosition | None = Field(None, title="文本范围百分比坐标",
                                             description="非空且开启就会匹配文本框是否在此区域内")
    open_position: bool = Field(True, title="是否开启文本范围限制，默认开启",
                                description="可关闭，方便用于自定义实现")

    pattern: Pattern = Field(None, description="真正最终用来匹配的")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.text, str):  # 如果文本是字符串，则转换为正则表达式
            self.pattern = re.compile(self.text, re.I)  # 忽略大小写以支持英文
        else:
            self.pattern = self.text


class ImageMatch(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    # 需配置参数
    name: str | None = Field(None, title="名称，key")
    image: str | np.ndarray = Field(
        title="模板图片名，assets/template目录下", description="读取图片用的图片名称，不带路径有后缀的")
    position: DynamicPosition | None = Field(None, title="限定图片范围百分比坐标")
    confidence: float = Field(0.8, title="图片置信度", ge=0, le=1)
    open_roi_cache: bool = Field(False, title="是否开启热区缓存，只适用于绝对位置固定的图标，如全局UI图标")

    # 内部参数
    roi_cache: dict[tuple, tuple[float, tuple[int, int, int, int]]] = Field(default_factory=dict)
    img: np.ndarray = Field(None, description="真正最终用来匹配的")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.image, str):  # 如果图片是路径，则读取图片
            self.img = img_util.read_img(file_util.get_assets_template(self.image))
        else:
            self.img = self.image


class ConditionalAction(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    name: str = Field(None, title="条件操作名称")
    condition: Callable[[], bool] = Field(title="条件函数", description="True则执行action函数，False则跳过")
    action: Callable[[], bool] = Field(title="操作函数列表", description="condition为True时执行")

    def __call__(self) -> bool | None:
        if self.condition is None:
            raise Exception("条件函数未设置")
        if self.condition():
            return True
        else:
            return False


class Page(BaseModel):

    @staticmethod
    def error_action(positions: dict[str, Position]) -> bool:
        raise NotImplementedError("Page callback function not implemented")

    name: str = Field(None, title="页面名称")
    action: Callable[[Dict[str, Position]], bool] = Field(default=error_action, title="页面操作函数")

    targetTexts: List[TextMatch] = Field(default_factory=list, title="目标文本")
    excludeTexts: List[TextMatch] = Field(default_factory=list, title="排除目标文本")

    targetImages: List[ImageMatch] = Field(default_factory=list, title="目标图片")
    excludeImages: List[ImageMatch] = Field(default_factory=list, title="排除目标图片")

    matchPositions: Dict[str, Position] = Field(default_factory=dict, title="匹配位置")

    screenshot: dict[Language, list[str]] = Field(
        default_factory=dict,
        title="页面截图，默认1280x720",
        description="页面匹配了哪些页面，截图放到assets/screenshot，方便调试与排查问题，无任何运行时作用",
    )

    _target_texts_mapping: dict[str, TextMatch] = PrivateAttr()

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)
        if self.targetTexts or self.excludeTexts:
            check_must = False
            for targetText in self.targetTexts:
                check_must = check_must or targetText.must
            for excludeText in self.excludeTexts:
                check_must = check_must or excludeText.must
            if not check_must:
                raise Exception("至少得有一个是必需匹配文本，否则无法定位页面")
        self._target_texts_mapping = {}
        for i in self.targetTexts:
            self._target_texts_mapping[i.name] = i

    def __eq__(self, other):
        if isinstance(other, Page):
            return self.name == other.name
        return False

    # @timeit
    def is_match(self, src_img: np.ndarray, img: np.ndarray | None, ocr_results: list[TextPosition]) -> bool:
        """
        页面匹配
        :param src_img: 原图截图
        :param img: 缩放到标准尺寸的截图，仅在图片匹配中有用
        :param ocr_results: 识别结果
        :return: bool
        """
        # 清空匹配位置
        self.matchPositions = {}
        for text_match in self.excludeTexts:  # 遍历排除文本 如果匹配到排除文本则返回False
            if self.text_match(text_match, src_img, img, ocr_results):
                return False
        for text_match in self.targetTexts:  # 遍历目标文本 如果匹配到目标文本则记录位置 否则返回False
            position = self.text_match(text_match, src_img, img, ocr_results)
            if position:
                self.matchPositions[text_match.name] = position
            elif not text_match.must:  # 非必需文本，没匹配上也没关系
                continue
            else:
                return False
        for image_match in self.excludeImages:  # 遍历排除图片 如果匹配到排除图片则返回False
            time.sleep(0.001)  # 短暂释放CPU
            if self.image_match(image_match, src_img, img):
                return False
        for image_match in self.targetImages:  # 遍历目标图片 如果匹配到目标图片则记录位置 否则返回False
            time.sleep(0.001)  # 短暂释放CPU
            if position := self.image_match(image_match, src_img, img):
                self.matchPositions[image_match.name] = position
            else:
                return False
        logger.debug("当前页面：%s", self.name)
        return True

    def text_match(self, text_match: TextMatch, src_img: np.ndarray, img: np.ndarray,
                   ocr_results: list[TextPosition]) -> Position | None:
        """
        文本匹配
        :param text_match: 文本参数
        :param src_img: 原图图片，可能非常大，仅在最后映射回原图坐标时使用
        :param img: ocr/match用的缩放后图片，标准一般是 1280 px x Any px，16:9 就是1280x720
        :param ocr_results: ocr识别结果
        :return:
        """
        h, w = img.shape[:2]
        position = None
        logger.debug("page name: %s", self.name)
        for ocrResult in ocr_results:
            pre_match_text = ocrResult.text.strip()
            if not text_match.pattern.search(pre_match_text):  # 没找到就下一个
                logger.debug("Non-matching: %s, regex: \"%s\", ocr text: \"%s\"",
                             text_match.name, text_match.text, pre_match_text)
                continue
            if not text_match.open_position or text_match.position is None:  # 找到了，且没有限定文本区域，合格
                position = ocrResult
                logger.debug("Matching: %s, regex: \"%s\", ocr text: \"%s\"", text_match.name, text_match.text, pre_match_text)
                break
            target_position = text_match.position.to_position(h, w)  # 将百分比区域根据图片大小转成像素位置
            if self._is_subset(target_position, ocrResult):  # 限定了文本区域，看是否是该区域子集
                position = ocrResult
                logger.debug("Matching: %s, regex: %s, ocr text: %s", text_match.name, text_match.text, pre_match_text)
                break
        return self.get_real_position(src_img, img, position)

    @staticmethod
    def _is_subset(big_set: Position, small_set: Position) -> bool | None:
        """判断一个矩形位置是否为子集"""
        if big_set is None:
            return True
        if big_set.x1 > small_set.x1:
            return False
        if big_set.y1 > small_set.y1:
            return False
        if big_set.x2 < small_set.x2:
            return False
        if big_set.y2 < small_set.y2:
            return False
        return True

    def image_match(self, image_match: ImageMatch, src_img: np.ndarray, img: np.ndarray) -> Position | None:
        """
        图片模板匹配
        :param image_match: 模板参数
        :param src_img: 原图图片，可能非常大，仅在最后映射回原图坐标时使用
        :param img: ocr/match用的缩放后图片，标准一般是 1280 px x Any px，16:9 就是1280x720
        :return:
        """
        if image_match.position:  # 在限定范围内找图
            valid_pos = image_match.position.to_position(img.shape[0], img.shape[1])
            valid_img = img[valid_pos.y1:valid_pos.y2, valid_pos.x1:valid_pos.x2]
        else:
            valid_pos = None
            valid_img = img
        if image_match.open_roi_cache:  # 热区缓存，适用于固定位置，可变位置不要开启
            if cur_roi_cache := image_match.roi_cache.get(src_img.shape[:2]):
                roi: tuple[int, int, int, int] = cur_roi_cache[1]
                valid_h, valid_w = valid_img.shape[:2]
                logger.debug("get roi cache: %s", cur_roi_cache)
                roi_h, roi_w = roi[3] - roi[1], roi[2] - roi[0]
                roi_enlarge_pos = (
                    max(roi[0] - roi_w // 2, 0),
                    max(roi[1] - roi_h // 2, 0),
                    min(roi[2] + roi_w // 2, valid_w),
                    min(roi[3] + roi_h // 2, valid_h)
                )  # 选框向四周放大，不然跟模板差不多大小无法匹配
                roi_img = valid_img[roi_enlarge_pos[1]:roi_enlarge_pos[3], roi_enlarge_pos[0]:roi_enlarge_pos[2]]
                confidence, _ = img_util.match_template(roi_img, image_match.img)
                logger.debug("confidence a: %s", confidence)
                if confidence < image_match.confidence:
                    return None
                logger.debug("%s %s", self.name, confidence)
                pos_tuple = roi
            else:
                confidence, pos_tuple = result = img_util.match_template(valid_img, image_match.img)
                logger.debug("confidence b: %s", confidence)
                if confidence < image_match.confidence:
                    return None
                if confidence > 0.9:
                    image_match.roi_cache[src_img.shape[:2]] = result
        else:
            confidence, pos_tuple = img_util.match_template(valid_img, image_match.img)
            logger.debug("confidence c: %s", confidence)
            if confidence < image_match.confidence:
                return None

        if valid_pos:
            final_pos_tuple = (
                valid_pos.x1 + pos_tuple[0],
                valid_pos.y1 + pos_tuple[1],
                valid_pos.x1 + pos_tuple[2],
                valid_pos.y1 + pos_tuple[3],
            )
        else:
            final_pos_tuple = pos_tuple
        return self.get_real_position(src_img, img, Position.build(*final_pos_tuple))

    @staticmethod
    def get_real_position(src_img: np.ndarray, img: np.ndarray, position: Pos | None) -> Pos | None:
        """按缩小尺寸匹配出来的坐标，映射回原尺寸的坐标"""
        if position is None:
            return None
        ratio = src_img.shape[0] / img.shape[0]
        # _cls_obj = TextPosition if isinstance(position, TextPosition) else Position
        real_position = position.build(
            x1=int(position.x1 * ratio),
            y1=int(position.y1 * ratio),
            x2=int(position.x2 * ratio),
            y2=int(position.y2 * ratio),
            confidence=position.confidence,
            text=position.text if isinstance(position, TextPosition) else None,
        )
        logger.debug("real_position: %s", real_position)
        return real_position

    def get_text_match_by_name(self, name: str) -> TextMatch:
        return self._target_texts_mapping.get(name)

# ------- v2 -----------

def build_combined_regex(patterns: List[str], flags=re.I) -> Pattern:
    """将一组正则模式合并成一个正则对象，带命名分组"""
    grouped = [f"(?P<P{i}>{p})" for i, p in enumerate(patterns)]
    return re.compile("|".join(grouped), flags)


def match_with_index(
        text: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
) -> Optional[int]:
    """匹配文本：先 exclude，再 include"""
    exclude_re = build_combined_regex(exclude_patterns) if exclude_patterns else None
    include_re = build_combined_regex(include_patterns)

    # 先匹配 exclude
    if exclude_re and exclude_re.search(text):
        return None

    # 再匹配 include
    m_inc = include_re.search(text)
    if not m_inc:
        return None

    # 返回命中 include 的下标
    for name, value in m_inc.groupdict().items():
        if value is not None:
            return int(name[1:])

    raise RuntimeError("不应该出现")  # 理论上不会触发


class IMatch(ABC):

    @abstractmethod
    def match(self, *args, **kwargs) -> Optional[dict[str, TextBox]]:
        pass


class RegexPage(IMatch):

    class _Regex:
        def __init__(self):
            self.key = None
            self.regex_str = None
            self.pattern: Pattern = None
            self.limit: Optional[AnchorBBox] = None

    def __init__(self, page_key: str, page_dict: dict[str, Any]):
        self.page_key: str = page_key
        self.page_dict: dict[str, Any] = page_dict

        self.name = page_dict.get(I18nPage.Name)
        self.includes: list[RegexPage._Regex] = self._build_regex(I18nPage.Include)
        self.excludes: list[RegexPage._Regex] = self._build_regex(I18nPage.Exclude)
        self.assets = page_dict.get(I18nPage.Assets)

    def _build_regex(self, data_key: str, flags: int = re.I):
        data_dict: dict = self.page_dict.get(data_key)
        if not data_dict:
            return []
        rpr_list = []
        for i, (k, v) in enumerate(data_dict.items()):
            rpr = RegexPage._Regex()
            rpr.key = k
            rpr.regex_str = v
            if isinstance(v, dict):
                rpr.regex_str = v.get(I18nPage.Text)
                rpr.limit = AnchorBBox.from_list(v.get(I18nPage.Limit))
            rpr.pattern = re.compile(rpr.regex_str, flags=flags)
            rpr_list.append(rpr)
        return rpr_list

    def match(
            self,
            scaler: Scaler,
            textboxes: list[TextBox],
            **kwargs
    ) -> Optional[dict[str, TextBox]]:
        if not textboxes:
            return None

        text_excludes_result: dict[str, TextBox] = {}

        # excludes
        for rpr in self.excludes:
            # text
            for textbox in textboxes:
                # 文本匹配
                if not rpr.pattern.search(textbox.text):
                    continue

                # 位置匹配
                if not rpr.limit:
                    text_excludes_result[rpr.key] = textbox
                    break
                limit_bbox = scaler.as_bbox(rpr.limit)
                if limit_bbox.contains_bbox(textbox):
                    text_excludes_result[rpr.key] = textbox
                    break

            if len(text_excludes_result) > 0:
                logger.debug(f"text_excludes_result: {text_excludes_result}")
                return None

        text_matches_result: dict[str, TextBox] = {}

        # text_matches
        for rpr in self.includes:
            matched_textbox = None
            # text
            for textbox in textboxes:
                # 文本匹配
                if not rpr.pattern.search(textbox.text):
                    continue

                # 位置匹配
                if not rpr.limit:
                    matched_textbox = textbox
                    break
                limit_bbox = scaler.as_bbox(rpr.limit)
                if limit_bbox.contains_bbox(textbox):
                    matched_textbox = textbox
                    break

            if matched_textbox is not None:
                text_matches_result[rpr.key] = matched_textbox

        if len(text_matches_result) != len(self.includes):
            # logger.debug(f"text_matches_result: {text_matches_result}, result: False")
            return None
        logger.debug(f"text_matches_result: {text_matches_result}, result: True")

        return text_matches_result

    @staticmethod
    def error_action(positions: dict[str, Position], **kwargs) -> bool:
        raise NotImplementedError("Page callback function not implemented")


class I18nPageX:

    def __init__(self, data: dict | str):
        self.data: dict = json.loads(data) if isinstance(data, str) else data
        self.i18n_regex_pages: dict[Language, dict[str, RegexPage]] = {}
        for page_key, k_lang_v_page in self.data.items():
            for k_lang, v_page in k_lang_v_page.items():
                self.i18n_regex_pages.setdefault(k_lang, {})[page_key] = RegexPage(page_key, v_page)


@lru_cache(maxsize=2000)
def _cached_compile_regex(regex_str: str, flags=re.I) -> Pattern:
    return re.compile(regex_str, flags)


class OcrResult:

    def __init__(self, results: list[TextBox]):
        self.results: list[TextBox] = results

    def has_results(self) -> bool:
        return self.results is not None and len(self.results) > 0

    def search(
            self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I
    ) -> Optional[list[TextBox]]:
        """ 在结果中搜索符合正则的文本 """
        return self.__search(regex_str, roi, flags, False)

    def search_with_index(
            self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I
    ) -> Optional[list[tuple[int, TextBox]]]:
        """ 在结果中搜索符合正则的文本 带索引 """
        return self.__search(regex_str, roi, flags, True)

    def __search(
            self,
            regex_str: str | list[str],
            roi: Optional[BBox] = None,
            flags=re.I,
            with_index: bool = False,
    ):
        """
        搜索文本
        :param regex_str: 支持正则
        :param roi: 支持框定文本位置范围
        :param flags: 默认忽略大小写
        :param with_index: 是否带下标索引，下标为regex_str的下标
        :return:
        """
        if not regex_str:
            raise ValueError("Text cannot be empty")
        if not self.has_results():
            return None
        found_boxes = []
        regex_str = [regex_str] if isinstance(regex_str, str) else regex_str
        patterns = [_cached_compile_regex(i, flags) for i in regex_str]
        for text_box in self.results:
            for index, pattern in enumerate(patterns):
                if roi and not roi.contains_bbox(text_box):
                    continue
                match = pattern.search(text_box.text)
                if not match:
                    continue
                if with_index:
                    found_boxes.append((index, text_box))
                else:
                    found_boxes.append(text_box)
        return found_boxes

    def search_group(
            self, regex_str: str | list[str], roi: Optional[TextBox] = None, flags=re.I
    ) -> Optional[list[TextBox]]:
        """ 合并搜索 """
        if not regex_str:
            raise ValueError()
        if not self.has_results():
            return None
        match_list = []
        if isinstance(regex_str, str):
            pattern = _cached_compile_regex(regex_str, flags)
        else:
            # 输入正则内有括号下标会加一错位
            pattern = build_combined_regex(regex_str, flags)
        for text_box in self.results:
            m_inc = pattern.search(text_box.text)
            if not m_inc:
                continue
            if not roi or roi.contains_bbox(text_box):
                match_list.append(text_box)
        return match_list


class Wait:

    def __init__(self, timeout: float, interval: float, event = None):
        self.timeout = timeout  # 单位都是秒
        self.interval = interval
        self.event = event

    def until(self, fn: Callable, *, predicate=bool):
        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            if self.event and not self.event.is_set():
                raise StopError()
            res = fn()
            if predicate(res):
                return res
            time.sleep(self.interval)

        return None


class OcrQuery:
    """ 整合一些常用的Ocr操作，减少重复代码 """

    def __init__(self, ctx):
        self.ctx = ctx
        self.img = None
        self.results: OcrResult = None
        # 保证每张图只查一次，及时抛出异常提醒
        self._is_query = False

    def grab(self, roi: Optional[BBox | AnchorBBox] = None, img: Optional[np.ndarray] = None) -> "OcrQuery":
        if img is None:
            img = self.ctx.img_service.screenshot()
        if roi and img is not None:
            if isinstance(roi, AnchorBBox):
                roi = self.ctx.scaler.as_bbox(roi)
            img = img[roi.as_slice()]
        self.img = img
        self._is_query = False
        return self

    def query(self, roi: BBox | None = None, resize: bool = True) -> "OcrQuery":
        if self._is_query:
            raise Exception("OcrQuery is already query")
        if not self.ctx.runtime.stop_event.is_set():
            raise StopError()
        self.results = self.ctx.ocr_service.query(self.img, roi=roi, resize=resize)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"ocr result: {self.results.results}")
        self._is_query = True
        if not self.ctx.runtime.stop_event.is_set():
            raise StopError()
        return self

    def snapshot(self, roi: Optional[BBox | AnchorBBox] = None, img: Optional[np.ndarray] = None, resize: bool = True) -> "OcrQuery":
        self.grab(img=img).query(roi=roi, resize=resize)
        return self

    def has_results(self) -> bool:
        return bool(self.results) and self.results.has_results()

    def search(self, regex_str: str | list[str], roi: Optional[BBox | AnchorBBox] = None, flags=re.I) -> Optional[list[TextBox]]:
        if not self.results:
            return None
        if roi and isinstance(roi, AnchorBBox):
            roi = self.ctx.scaler.as_bbox(roi)
        return self.results.search(regex_str, roi, flags)

    def search_with_index(self, regex_str: str | list[str], roi: Optional[BBox | AnchorBBox] = None, flags=re.I) -> Optional[list[tuple[int, TextBox]]]:
        if not self.results:
            return None
        if roi and isinstance(roi, AnchorBBox):
            roi = self.ctx.scaler.as_bbox(roi)
        return self.results.search_with_index(regex_str, roi, flags)

    def poll(self, func, timeout: float = 3.0, interval: float = 0.1):
        start = time.monotonic()
        end = start + timeout
        while True:
            result = func()
            if result:
                return result
            if time.monotonic() >= end:
                return None
            time.sleep(interval)

    def wait(self, timeout: float = 5.0, interval: float = 0.3):
        return Wait(timeout, interval, self.ctx.runtime.stop_event)


class UIOp:
    """
    UI Operation
    整合一些常用的ui操作，减少重复代码
    """

    HOME_COLOR_POINT = [
        # 任务
        AnchorPoint(14, 153, Align.Top | Align.Left), AnchorPoint(26, 153, Align.Top | Align.Left),
        # 背包
        AnchorPoint(212, 44, Align.Top | Align.Left), AnchorPoint(222, 44, Align.Top | Align.Left),
        # # 飞讯
        # AnchorPoint(274, 31, Align.Top | Align.Left), AnchorPoint(280, 38, Align.Top | Align.Left),
        # # 先约电台
        # AnchorPoint(1114, 24, Align.Top | Align.Right),
        # 共鸣者
        AnchorPoint(1156, 28, Align.Top | Align.Right), AnchorPoint(1160, 30, Align.Top | Align.Right),
        # 终端
        AnchorPoint(1221, 34, Align.Top | Align.Right), AnchorPoint(1222, 35, Align.Top | Align.Right),
    ]

    def __init__(self, ctx, page_service=None):
        self.ctx = ctx
        self.oq: OcrQuery = OcrQuery(self.ctx)
        # 绑定页面，在指定页面内搜索，默认为全局公共页面
        self.page_service = page_service if page_service else self.ctx.page_service

        # runtime

        # 主页（大世界）
        self.__home_color_match = None
        self._route_executor = RouteExecutor(self.ctx)

    # --------- ocr相关 ---------

    @property
    def lang(self):
        return self.ctx.window_service.get_lang()

    @property
    def img(self):
        return self.oq.img

    @property
    def bbox_result(self):
        return self.oq.results.results

    @property
    def ocr_result(self):
        return self.oq.results

    def grap(self) -> np.ndarray:
        """截图"""
        return self.ctx.img_service.screenshot()

    def snapshot(self, roi: Optional[BBox | AnchorBBox] = None, img: Optional[np.ndarray] = None, resize: bool = True):
        """
        截图并查询
        :param img: 指定图片，默认重新截图
        :param roi: 裁剪出图片指定区域
        :param resize: 1280x720以上分辨率图片是否缩小，默认开启，牺牲精度提升识别速度，若需要识别小字，必须关闭，用原图识别以保证精度
        :return:
        """
        self.oq = OcrQuery(self.ctx).snapshot(roi, img, resize)
        return self

    def match_page(self, page: str):
        """
        根据页面key匹配页面是否命中
        :param page: 如：I18nPage.Terminal.PAGE
        :return:
        """
        return self.page_service.is_match(self.ocr_result, page)

    def match_key(self, key: str, text: str):
        """
        根据文本key匹配文本
        :param key: 如：I18nText.Terminal
        :param text:
        :return:
        """
        match = self.__compile_pattern(self.ctx.tr(key), re.I).match(text)
        # logger.debug(f"match: {match}")
        return match

    @staticmethod
    @lru_cache(maxsize=666)
    def __compile_pattern(pattern: str, flags: int):
        return re.compile(pattern, flags)

    def search(self, regex_str: str | list[str], roi: Optional[BBox | AnchorBBox] = None, flags=re.I) -> Optional[list[TextBox]]:
        """
        在页面内查询文本
        :param regex_str: 文本正则
        :param roi: 文本所在区域，可选。用于过滤结果，不会裁剪图片
        :param flags: 默认忽略大小写，0为区分大小写
        :return:
        """
        return self.oq.search(regex_str, roi, flags)

    # def search_by_key(
    #         self, i18n_text: str | list[str], roi: Optional[BBox | AnchorBBox] = None, flags=re.I) -> Optional[list[TextBox]]:
    #     """跟据文本标识查询页面内查询文本"""
    #     return self.search(self.ctx.tr(i18n_text), roi, flags)
    #
    # def search_with_index(
    #         self, regex_str: str | list[str], roi: Optional[BBox | AnchorBBox] = None, flags=re.I
    # ) -> Optional[list[tuple[int, TextBox]]]:
    #     return self.oq.search_with_index(regex_str, roi, flags)

    # --------- 点击页面相关 ---------

    def click(self, x: int, y: int, times: int = 1, interval: float = 0.0):
        """点击点"""
        if times < 1 or interval < 0:
            raise ValueError(f"Invalid value: {times} / {interval}")
        logger.debug(f"click: ({x}, {y}), {times}")
        for i in range(times):
            self.ctx.control_service.click(x, y)
            if times > 1:
                self.sleep(interval)
        return self

    def click_point(self, point: Point, times: int = 1, interval: float = 0.0):
        """点击点/逻辑点"""
        if isinstance(point, AnchorPoint):
            point = self.ctx.scaler.as_point(point)
        self.click(point.x, point.y, times, interval)
        return self

    def click_bbox(self, bbox: BBox | AnchorBBox, pk: PointKind = PointKind.CENTER, times: int = 1, interval: float = 0.0):
        """点击指定框内的点"""
        if isinstance(bbox, AnchorBBox):
            bbox = self.ctx.scaler.as_bbox(bbox)
        if pk == PointKind.CENTER:
            point = bbox.center
        elif pk == PointKind.NEAR:
            point = bbox.near
        elif pk == PointKind.RANDOM:
            point = bbox.random
        else:
            raise ValueError("Unsupported PointKind")
        self.click(point[0], point[1], times, interval)
        return self

    def click_key(self, match: dict[str, BBox], key: str, pk: PointKind = PointKind.CENTER):
        """根据页面中的文本key，点击key对应文本框内的点"""
        bbox = match.get(key)
        if not bbox:
            raise ValueError(f"Invalid key: {key}")
        self.click_bbox(bbox, pk)
        return self

    def click_text(
        self,
        regex_str: str | list[str],
        roi: Optional[BBox | AnchorBBox] = None,
        pk: PointKind = PointKind.CENTER,
        delay: float = 0.0,
        times: int = 1,
        interval: float = 0.0,
    ) -> bool:
        """
        点击页面内某个文本，有这个文本才点击
        :param regex_str: 文本正则
        :param roi: 文本所在区域，可选。避免有相同文本时点错
        :param pk: 取文本框内的哪个点，默认中心点。增加随机性，避免固定点击同一个点
        :param delay: 找到文本后延迟多少秒开始点击。用于解决已识别到，但游戏弹窗动画还未播完无法点击，等一会再点即可
        :param times: 点击文本几次，默认一次。用于解决延迟等原因导致有时只点一次不一定成功，多点几次保证覆盖
        :param interval: 每次点击后间隔多少秒再点下一次
        :return: 返回是否找到文本
        """
        res = self.search(regex_str, roi)
        if not res:
            return False
        if delay > 0:
            self.sleep(delay)
        logger.debug(f"click: {regex_str}")
        self.click_bbox(res[0], pk, times, interval)
        return True

    # --------- 等待相关 ---------

    def sleep(self, seconds: float):
        """等待"""
        t = 0.1
        while seconds > t:
            if not self.ctx.runtime.stop_event.is_set():
                raise StopError()
            time.sleep(t)
            seconds -= t
        if not self.ctx.runtime.stop_event.is_set():
            raise StopError()
        if seconds > 0:
            time.sleep(seconds)
        return self

    def wait(self, timeout: float = 5.0, interval: float = 0.3):
        """条件等待"""
        return self.oq.wait(timeout, interval)

    def __init_home_color_match(self):
        rule = ColorRule().points(self.HOME_COLOR_POINT).colors(Color.bgr(255, 255, 255), 12, RuleMode.ALL)
        self.__home_color_match = ColorMatch(self.ctx.scaler).rules(rule)

    def is_on_homepage(self, img: Optional[np.ndarray] = None) -> bool:
        """是否在主界面"""
        if not self.__home_color_match:
            self.__init_home_color_match()
        return self.__home_color_match.match(img if img is not None else self.grap())

    def wait_back_home(self, timeout: int = 60, interval: float = 1.0):
        """循环等待回到主界面"""
        if not self.__home_color_match:
            self.__init_home_color_match()

        self.activate()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_on_homepage():
                self.activate()
                return self
            self.sleep(interval)
        # 卡在加载，强制关闭
        self.ctx.control_service.close_window()
        raise Exception("等待回到主界面超时")

    # --------- 按键相关 ---------

    def activate(self):
        """窗口激活"""
        self.ctx.control_service.activate()
        return self

    def esc(self):
        """按esc"""
        self.ctx.control_service.esc()
        return self

    def pick_up(self, times: int = 1, interval: float = 0.0):
        """拾取"""
        for _ in range(times):
            self.ctx.control_service.pick_up()
            self.sleep(interval)
        return self

    def camera_reset(self):
        """重置"""
        self.ctx.control_service.camera_reset()
        return self

    def move(self, route: list[MoveStep]):
        """执行人物移动路线"""
        self._route_executor.execute(route)
        return self


if __name__ == '__main__':
    # patterns = [
    #     r"cat",
    #     r"dog",
    #     r"\d+"
    # ]
    #
    # regex = build_combined_regex(patterns)
    #
    # print(match_with_index(regex, "hello dog world"))
    # # (True, 1)
    #
    # print(match_with_index(regex, "abc 123"))
    # # (True, 2)
    #
    # print(match_with_index(regex, "nothing"))
    # # (False, None)
    print(I18nPageEchoMerge.StandardMerge_SelectAll.__name__)