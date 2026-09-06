import logging
import re
import time
from threading import RLock

import numpy as np

from src.core.contexts import Context
from src.core.geometry import Detection
from src.core.interface import ODService, ImgService, WindowService
from src.core.runtime import Device
from src.util import yolo_util
from src.util.wrap_util import timeit
from src.util.yolo_util import Model

logger = logging.getLogger(__name__)


class YoloServiceImpl(ODService):

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__()
        self._rlock: RLock = RLock()
        self._context: Context = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service

        # try:
        #     self._device = context.runtime.cfg.game.device
        # except Exception:
        #     self._device = Device.Auto
        self._device = Device.CPU
        logger.debug(f"device: {self._device}")

        # self._provider: list[str] = yolo_util.get_ort_providers()
        self._default_model: Model = yolo_util.MODEL_BOSS_DEFAULT
        self._current_model: Model = self._default_model
        self._session = self._create_session(self._current_model.path)
        # self._executor = ThreadPoolExecutor(max_workers=2)
        self._reward_model: Model = yolo_util.MODEL_REWARD
        self._reward_session = self._create_session(self._reward_model.path)

    # def __del__(self):
    #     self._executor.shutdown(wait=False)

    def _create_session(self, model_path: str):
        return yolo_util.create_ort_session(
            model_path=model_path,
            providers=yolo_util.get_ort_providers() if self._device.is_gpu() else yolo_util.get_ort_providers_cpu(),
            sess_options=yolo_util.create_ort_session_options()
        )

    @timeit(ignore=3)
    def search_echo(
            self,
            img: np.ndarray | None = None,
            confidence: float| None = None,
            boss_name: str | None = None,
    ) -> tuple[int, int, int, int] | None:
        if not boss_name:
            boss_name = self._context.boss_task_ctx.lastBossName
        if img is None:
            img = self._img_service.screenshot()
        # with self._rlock:
        model = self.get_model_by_boss_name(boss_name)
        if self._current_model != model:
            self._current_model = model
            logger.debug("Switch model: %s", model.name)
            timestamp = time.time()
            self._session = self._create_session(self._current_model.path)
            logger.debug("Session creation time: %s seconds", int(time.time() - timestamp))
        if confidence is None or confidence <= 0:
            confidence = model.confidence_thres
        results = yolo_util.search_echo(self._session, img, confidence, model.iou_thres, model.half)
        if results is None:
            return None
        box, score, class_id = results
        logger.debug("box: %s, scores: %s, class_id: %s", box, score, class_id)
        # x1, y1, w, h = box
        return box

    @timeit(ignore=3)
    def search_echo_2(
            self,
            img: np.ndarray | None = None,
            confidence: float | None = None,
            boss_name: str | None = None,
    ) -> Detection | None:
        if not boss_name:
            boss_name = self._context.boss_task_ctx.lastBossName
        boss_name = re.sub(r"[·_-]", "", boss_name)
        if img is None:
            img = self._img_service.screenshot()
        # with self._rlock:
        model = self.get_model_by_boss_name(boss_name)
        if self._current_model != model:
            self._current_model = model
            logger.debug("Switch model: %s", model.name)
            timestamp = time.time()
            self._session = self._create_session(self._current_model.path)
            logger.debug("Session creation time: %s seconds", int(time.time() - timestamp))
        if confidence is None or confidence <= 0:
            confidence = model.confidence_thres
        results = yolo_util.search_echo(self._session, img, confidence, model.iou_thres, model.half)
        if results is None:
            return None
        box, score, class_id = results
        logger.debug("box: %s, scores: %s, class_id: %s", box, score, class_id)
        # x1, y1, w, h = box
        return Detection.from_xywh(*box, score=score, class_id=class_id)

    @staticmethod
    def get_model_by_boss_name(boss_name: str):
        for model in yolo_util.MODEL_BOSS_ALL:
            if boss_name in model.boss:
                return model
        return yolo_util.MODEL_BOSS_UNKNOWN

    @timeit(ignore=3)
    def search_reward(self, img: np.ndarray | None = None) -> Detection | None:
        if img is None:
            img = self._img_service.screenshot()
        model = self._reward_model
        results = yolo_util.search_echo(self._reward_session, img, model.confidence_thres, model.iou_thres, model.half)
        if results is None:
            return None
        box, score, class_id = results
        logger.debug("box: %s, scores: %s, class_id: %s", box, score, class_id)
        # x1, y1, w, h = box
        return Detection.from_xywh(*box, score=score, class_id=class_id)
