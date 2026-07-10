import importlib.util
import logging
import re
import time
from abc import ABC

import cv2
import numpy as np

from src.core.contexts import Context
from src.core.geometry import TextBox, BBox, RapidocrTextBox, PaddleocrTextBox, RapidocrRecTextBox
from src.core.interface import OCRService, ImgService, WindowService
from src.core.pages import OcrResult
from src.core.regions import Position, RapidocrPosition, TextPosition, DynamicPosition, PaddleocrPosition
from src.core.runtime import Device
from src.util import rapidocr_util
from src.util.wrap_util import timeit

logger = logging.getLogger(__name__)


class ImageTransform:
    """OCR图片预处理及坐标恢复"""

    def __init__(self) -> None:
        self.scale: float = 1.0

        # 原图尺寸
        self.src_w: int = 0
        self.src_h: int = 0

        # ROI 左上角（原图坐标）
        self.roi_x: int = 0
        self.roi_y: int = 0

    @staticmethod
    def _scale(img: np.ndarray) -> float:
        """
        ocr图片统一缩放，仅需在合理范围内缩放，适配1280x720 1600x900 2560x1440等常见分辨率，压缩到高720
        太离谱的会触发ocr引擎参数自动缩放
        :param img:
        :return:
        """
        h, w = img.shape[:2]
        if h > 720 and w > 1280:
            # 压缩太小会导致小字识别错误
            # base_h = 540
            # base_h = 640
            base_h = 720
            return base_h / h
        return 1.0

    @staticmethod
    def _align_up(value: int, align: int = 32) -> int:
        """向上对齐到 align 的整数倍。"""
        return (value + align - 1) // align * align

    @staticmethod
    def _clip(value: int, low: int, high: int) -> int:
        return max(low, min(value, high))

    @staticmethod
    def _pad(
        img: np.ndarray,
        target_w: int,
        target_h: int,
        value: int = 255,
    ) -> np.ndarray:
        """将图片放到左上角并Padding"""

        h, w = img.shape[:2]

        if h == target_h and w == target_w:
            return img

        if img.ndim == 2:
            canvas = np.full((target_h, target_w), value, dtype=img.dtype)
        else:
            canvas = np.full( (target_h, target_w, img.shape[2]), value, dtype=img.dtype)

        canvas[:h, :w] = img
        return canvas

    def prepare(
        self,
        img: np.ndarray,
        roi: BBox | None = None,
        *,
        scale: float | None = None,
    ) -> np.ndarray:
        """
        OCR前图片处理，缩小，截取roi
        :param img:
        :param roi:
        :param scale:
        :return:
        """
        if scale is None:
            scale = self._scale(img)
        self.scale = scale
        # logger.debug(f"img shape: {img.shape}, roi: {roi}, scale: {self.scale}")

        self.src_h, self.src_w = img.shape[:2]

        self.roi_x = 0
        self.roi_y = 0

        # 整图缩放
        if scale != 1.0:
            scaled_w = max(1, round(self.src_w * scale))
            scaled_h = max(1, round(self.src_h * scale))

            interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
            img = cv2.resize(img, (scaled_w, scaled_h), interpolation=interpolation)
        else:
            scaled_h, scaled_w = img.shape[:2]

        if roi is None:
            # 整图只缩放，不做Padding
            return img

        # ROI（原图坐标）
        x1 = self._clip(roi.x1, 0, self.src_w)
        y1 = self._clip(roi.y1, 0, self.src_h)
        x2 = self._clip(roi.x2, 0, self.src_w)
        y2 = self._clip(roi.y2, 0, self.src_h)

        small_w = self._align_up(max(1, scaled_w // 4))
        small_h = self._align_up(max(1, scaled_h // 4))

        medium_w = self._align_up(max(1, scaled_w // 2))
        medium_h = scaled_h

        large_w = scaled_w
        large_h = scaled_h

        if x2 <= x1 or y2 <= y1:
            if img.ndim == 2:
                return np.full((small_h, small_w), 255, dtype=img.dtype)
            return np.full((small_h, small_w, img.shape[2]), 255, dtype=img.dtype)

        # 保存原图 ROI 偏移
        self.roi_x = x1
        self.roi_y = y1

        # ROI 同步缩放
        sx1 = round(x1 * scale)
        sy1 = round(y1 * scale)
        sx2 = round(x2 * scale)
        sy2 = round(y2 * scale)

        crop = img[sy1:sy2, sx1:sx2]

        crop_h, crop_w = crop.shape[:2]

        if crop_w <= small_w and crop_h <= small_h:
            target_w = small_w
            target_h = small_h

        elif crop_w <= medium_w and crop_h <= medium_h:
            target_w = medium_w
            target_h = medium_h

        else:
            target_w = large_w
            target_h = large_h

        return self._pad(crop, target_w, target_h)

    def restore_bbox(self, bbox: TextBox) -> TextBox:
        """恢复到原图坐标"""

        x1 = round(bbox.x1 / self.scale) + self.roi_x
        y1 = round(bbox.y1 / self.scale) + self.roi_y
        x2 = round(bbox.x2 / self.scale) + self.roi_x
        y2 = round(bbox.y2 / self.scale) + self.roi_y

        return TextBox(
            x1=self._clip(x1, 0, self.src_w),
            y1=self._clip(y1, 0, self.src_h),
            x2=self._clip(x2, 0, self.src_w),
            y2=self._clip(y2, 0, self.src_h),
            text=bbox.text,
            score=bbox.score,
        )

    def restore_boxes(self, boxes: list[TextBox]) -> list[TextBox]:
        """批量恢复到原图坐标。"""
        return [self.restore_bbox(box) for box in boxes]


class AbstractOcrService(OCRService, ABC):

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService):
        super().__init__()
        self._context: Context = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service

        try:
            self._device = context.runtime.cfg.game.device
        except Exception:
            self._device = Device.Auto
        logger.debug(f"device: {self._device}")

        self._device: Device = self.resolve_device()
        self.ocr_use_gpu = self._device.is_gpu()

    def resolve_device(self) -> Device:
        ocr_use_gpu = None
        is_fall_back = False
        if self._context.spec and self._context.spec.ocr_use_gpu is True:
            if importlib.util.find_spec("paddle") and importlib.util.find_spec("onnxruntime"):
                import paddle
                import onnxruntime
                if paddle.is_compiled_with_cuda() and "CUDAExecutionProvider" in onnxruntime.get_available_providers():
                    ocr_use_gpu = True
                    # logger.info("OCR is running on GPU ✅")
            if ocr_use_gpu is None:
                ocr_use_gpu = False
                is_fall_back = True
                # logger.warning("OCR expected GPU, falling back to CPU ⚠️")
        if ocr_use_gpu is None:
            ocr_use_gpu = False
            # logger.info("OCR is running on CPU ✅")

        final_device = Device.CUDA if ocr_use_gpu else Device.CPU
        if self._device.is_gpu():
            if ocr_use_gpu:
                logger.info("OCR using GPU ✅")
            elif is_fall_back:
                logger.warning("OCR expected GPU, falling back to CPU ⚠️")
        elif self._device == Device.CPU:
            if ocr_use_gpu:
                logger.info("OCR expected GPU, CPU selected")
                final_device = Device.CPU
        else:
            raise NotImplementedError()
        return final_device


class RapidOcrServiceImpl(AbstractOcrService):

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(context, window_service, img_service)

        self._engine = rapidocr_util.create_ocr(use_gpu=self.ocr_use_gpu)
        self._last_time = time.time()

    def search_text(self, results: list[TextPosition], target: str) -> TextPosition | None:
        for result in results:
            if re.search(target, result.text, re.I):  # 使用正则匹配
                return result
        return None

    def search_texts(self, results: list[TextPosition], target: str) -> list[TextPosition]:
        filter_list = []
        for result in results:
            if re.search(target, result.text, re.I):  # 使用正则匹配
                filter_list.append(result)
        return filter_list

    def find_text(self, targets: str | list[str], img: np.ndarray | None = None,
                  position: Position | DynamicPosition | None = None) -> TextPosition | None:
        if isinstance(targets, str):
            targets = [targets]
        if img is None:
            img = self._img_service.screenshot()
        result = self.ocr(img, position)
        for target in targets:
            if text_info := self.search_text(result, target):
                return text_info
        return None

    def wait_text(self, targets: str | list[str], timeout: float = 3.0,
                  position: Position | DynamicPosition | None = None, wait_time: float = 0.1) -> TextPosition | None:
        if isinstance(targets, str):
            targets = [targets]
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            result = self.find_text(targets, img=None, position=position)
            if result is not None:
                return result
            time.sleep(wait_time)  # 每次截图和 OCR 处理之间增加一个短暂的暂停时间
        return None

    @timeit(ignore=3)
    def ocr(self, img: np.ndarray, position: Position | DynamicPosition | None = None,
            det=True, rec=True, cls=False) -> list[TextPosition]:
        self._ocr_wait()
        if position is not None:
            if isinstance(position, DynamicPosition):
                w, h = self._window_service.get_client_wh()
                position = position.to_position(h, w)
            img = img[position.y1:position.y2, position.x1:position.x2]
        if det is True and rec is True and cls is False:
            return self._ocr_det_rec(img)
        elif det is False and rec is True and cls is False:
            return self._ocr_det_rec(img)
        raise NotImplementedError("不支持的识别方式")

    def _ocr_det_rec(self, img: np.ndarray) -> list[TextPosition]:
        output = self._engine(img, use_det=True, use_rec=True, use_cls=False)
        positions = RapidocrPosition.format(output)
        return positions

    def _ocr_wait(self):
        """限制OCR调用频率，默认不限制OcrInterval=0"""
        config = self._context.config.app
        if config.OcrInterval > 0 and time.time() - self._last_time < config.OcrInterval:
            if wait_time := config.OcrInterval - (time.time() - self._last_time) > 0:
                time.sleep(wait_time)
        self._last_time = time.time()

    def print_ocr_result(self, ocr_results: list[TextPosition] | None):
        if ocr_results is None:
            logger.debug("ocr_results is None")
            return
        for result in ocr_results:
            logger.debug(result)

    @timeit(ignore=3)
    def query(
            self,
            img: np.ndarray,
            roi: BBox | None = None,
            det=True,
            rec=True,
            cls=False,
            resize=True,
    ) -> OcrResult:
        # logger.debug(f"img shape1: {img.shape}")
        itf = ImageTransform()
        img = itf.prepare(img, roi=roi)
        # logger.debug(f"img shape2: {img.shape}")
        if det is True and rec is True and cls is False:
            output = self._engine(img, use_det=True, use_rec=True, use_cls=False)
            result = RapidocrTextBox.format(output)
        elif det is False and rec is True and cls is False:
            output = self._engine(img, use_det=False, use_rec=True, use_cls=False)
            result = RapidocrRecTextBox.format(output)
        else:
            raise NotImplementedError("不支持的识别方式")
        ocr_result = OcrResult(itf.restore_boxes(result))
        # logger.debug(f"ocr_result: {ocr_result}")
        return ocr_result
        # finally:
        #     if self.ocr_use_gpu:
        #         import gc, paddle
        #         gc.collect()
        #         # if paddle.device.is_compiled_with_cuda():
        #         paddle.device.cuda.empty_cache()
        #         logger.warning("最终清空 CUDA 缓存。")


class PaddleOcrServiceImpl(AbstractOcrService):

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(context, window_service, img_service)

        from src.util import paddleocr_util
        self._engine = paddleocr_util.create_paddleocr(use_gpu=self.ocr_use_gpu)
        self._last_time = time.time()

    def search_text(self, results: list[TextPosition], target: str) -> TextPosition | None:
        for result in results:
            if re.search(target, result.text, re.I):  # 使用正则匹配
                return result
        return None

    def search_texts(self, results: list[TextPosition], target: str) -> list[TextPosition]:
        filter_list = []
        for result in results:
            if re.search(target, result.text, re.I):  # 使用正则匹配
                filter_list.append(result)
        return filter_list

    def find_text(self, targets: str | list[str], img: np.ndarray | None = None,
                  position: Position | DynamicPosition | None = None) -> TextPosition | None:
        if isinstance(targets, str):
            targets = [targets]
        if img is None:
            img = self._img_service.screenshot()
        result = self.ocr(img, position)
        for target in targets:
            if text_info := self.search_text(result, target):
                return text_info
        return None

    def wait_text(self, targets: str | list[str], timeout: float = 3.0,
                  position: Position | DynamicPosition | None = None, wait_time: float = 0.1) -> TextPosition | None:
        if isinstance(targets, str):
            targets = [targets]
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            result = self.find_text(targets, img=None, position=position)
            if result is not None:
                return result
            time.sleep(wait_time)  # 每次截图和 OCR 处理之间增加一个短暂的暂停时间
        return None

    # @timeit(ignore=3)
    def ocr(self, img: np.ndarray, position: Position | DynamicPosition | None = None,
            det=True, rec=True, cls=False) -> list[TextPosition]:
        self._ocr_wait()
        if position is not None:
            if isinstance(position, DynamicPosition):
                w, h = self._window_service.get_client_wh()
                position = position.to_position(h, w)
            img = img[position.y1:position.y2, position.x1:position.x2]
        if det is True and rec is True and cls is False:
            return self._ocr_det_rec(img)
        elif det is False and rec is True and cls is False:
            return self._ocr_det_rec(img)
        raise NotImplementedError("不支持的识别方式")

    def _ocr_det_rec(self, img: np.ndarray) -> list[TextPosition]:
        output = self._engine.ocr(img, det=True, rec=True, cls=False)
        positions = PaddleocrPosition.format(output)
        return positions

    def _ocr_wait(self):
        """限制OCR调用频率，默认不限制OcrInterval=0"""
        config = self._context.config.app
        if config.OcrInterval > 0 and time.time() - self._last_time < config.OcrInterval:
            if wait_time := config.OcrInterval - (time.time() - self._last_time) > 0:
                time.sleep(wait_time)
        self._last_time = time.time()

    def print_ocr_result(self, ocr_results: list[TextPosition] | None):
        if ocr_results is None:
            logger.debug("ocr_results is None")
            return
        for result in ocr_results:
            logger.debug(result)

    @timeit(ignore=3)
    def query(
            self,
            img: np.ndarray,
            roi: BBox | None = None,
            det=True,
            rec=True,
            cls=False,
            resize=True,
    ) -> OcrResult:
        # logger.debug(f"img shape1: {img.shape}")
        itf = ImageTransform()
        img = itf.prepare(img, roi=roi)
        # logger.debug(f"img shape2: {img.shape}")
        if det is True and rec is True and cls is False:
            output = self._engine(img, use_det=True, use_rec=True, use_cls=False)
            result = PaddleocrTextBox.format(output, roi)
        elif det is False and rec is True and cls is False:
            output = self._engine(img, use_det=False, use_rec=True, use_cls=False)
            result = PaddleocrTextBox.format(output, roi)
        else:
            raise NotImplementedError("不支持的识别方式")
        ocr_result = OcrResult(itf.restore_boxes(result))
        # logger.debug(f"ocr_result: {ocr_result}")
        return ocr_result

# SVTR
# class SVTROcrServiceImpl(OCRService):
#     pass
