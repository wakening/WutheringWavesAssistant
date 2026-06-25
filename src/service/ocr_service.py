import importlib.util
import logging
import re
import time
from abc import ABC

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

    def _resize_bboxes(self, bboxes: list[TextBox], factor: float):
        if bboxes is None:
            return None
        return [bbox.resize(factor) for bbox in bboxes]

    def _resize_img(self, img: np.ndarray) -> tuple[np.ndarray, float]:
        """
        ocr图片统一缩放，仅需在合理范围内缩放，适配1280x720 1600x900 2560x1440等常见分辨率，压缩到高720
        太离谱的会触发ocr引擎参数自动缩放
        :param img:
        :return:
        """
        h, w = img.shape[:2]
        if h > 720 and w > 1280:
            # 压缩会导致小字识别错误
            # base_h = 540
            # base_h = 640
            base_h = 720
            new_img = self._img_service.resize_by_ratio(img, base_h / h)
            return new_img, h / base_h
        return img, 1.0


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
        if roi:
            img = img[roi.as_slice()]
        ratio = None
        if resize:
            img, ratio = self._resize_img(img)
        if det is True and rec is True and cls is False:
            output = self._engine(img, use_det=True, use_rec=True, use_cls=False)
            result = RapidocrTextBox.format(output)
        elif det is False and rec is True and cls is False:
            output = self._engine(img, use_det=False, use_rec=True, use_cls=False)
            result = RapidocrRecTextBox.format(output)
        else:
            raise NotImplementedError("不支持的识别方式")
        if resize:
            result = self._resize_bboxes(result, ratio)
        return OcrResult(result)


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
        if roi:
            img = img[roi.as_slice()]
        ratio = None
        if resize:
            img, ratio = self._resize_img(img)
        if det is True and rec is True and cls is False:
            output = self._engine(img, use_det=True, use_rec=True, use_cls=False)
            result = PaddleocrTextBox.format(output, roi)
        elif det is False and rec is True and cls is False:
            output = self._engine(img, use_det=False, use_rec=True, use_cls=False)
            result = PaddleocrTextBox.format(output, roi)
        else:
            raise NotImplementedError("不支持的识别方式")
        if resize:
            result = self._resize_bboxes(result, ratio)
        return OcrResult(result)

# SVTR
# class SVTROcrServiceImpl(OCRService):
#     pass
