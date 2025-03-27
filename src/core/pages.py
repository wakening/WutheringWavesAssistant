import logging
import re
import time
from re import Pattern
from typing import Callable, Dict, List

import numpy as np
from pydantic import BaseModel, Field, PrivateAttr

from src.core.languages import Languages
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

    screenshot: dict[Languages, list[str]] = Field(
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

# def aatest(position: Pos) -> Pos:
#     ratio = 2
#     real_position = position.build(
#         x1=int(position.x1 * ratio),
#         y1=int(position.y1 * ratio),
#         x2=int(position.x2 * ratio),
#         y2=int(position.y2 * ratio),
#         confidence=position.confidence,
#         text=position.text if isinstance(position, TextPosition) else None,
#     )
#     # if isinstance(position, TextPosition):
#     #     real_position.text = position.text
#     print("real_position: %s", real_position)
#     return real_position
#
# if __name__ == '__main__':
#     from src.core.regions import RapidocrPosition
#     p1 = Position.build(1,11,1,1)
#     p2 = RapidocrPosition.build(2,33,55,77, text="asdf")
#     aatest(p1)
#     aatest(p2)
#     print("ok")
