import logging
import math
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from multiprocessing import Process, Event
from typing import Iterable, Any, TypeVar, Callable, Mapping

import win32gui
from pydantic import BaseModel, Field
from pynput.mouse import Controller

from src.config import logging_config
from src.core.contexts import Context
from src.core.injector import Container
from src.core.interface import ImgService, OCRService, ControlService, PageEventService, WindowService
from src.util import hwnd_util, keymouse_util

logger = logging.getLogger(__name__)

Task = TypeVar('Task', bound='ProcessTask')


class ProcessTask(BaseModel, ABC):
    model_config = {"arbitrary_types_allowed": True}
    name: str | None = Field(None)
    args: Iterable[Any] | None = Field(None)
    kwargs: Mapping[str, Any] = Field(None)
    daemon: bool | None = Field(None)
    start_time: datetime | None = Field(None)
    end_time: datetime | None = Field(None)
    process: Process | None = Field(None)

    @abstractmethod
    def get_task(self, *args) -> Callable[..., None] | None:
        pass

    @classmethod
    def build(cls: type[Task],
              args: Iterable[Any] = (),
              kwargs: Mapping[str, Any] = None,
              name: str | None = None,
              daemon: bool | None = None) -> Task:
        name = name if name is not None else cls.__qualname__
        task = cls(args=args, name=name, daemon=daemon)
        task.process = Process(target=task.get_task(), args=args, kwargs=kwargs, name=task.name, daemon=task.daemon)
        return task

    def start(self):
        self.start_time = datetime.now()
        self.process.start()
        return self

    def stop(self, timeout=5):
        self.end_time = datetime.now()
        logger.info(f"[{self.name}]任务结束，耗时: {(self.end_time - self.start_time).total_seconds():.2f}s")
        try:
            if not self.process.is_alive():
                return self
            self.process.terminate()
            self.process.join(timeout)
        except Exception:
            logger.error(f"任务[{self.name}]结束失败", exc_info=True)
        return self

    def join(self):
        self.process.join()


class MouseResetProcessTask(ProcessTask):
    def get_task(self, *args) -> Callable[[...], None] | None:
        return mouse_reset_task_run


class AutoBossProcessTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return auto_boss_task_run


class AutoPickupProcessTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return auto_pickup_task_run


class AutoStoryProcessTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return auto_story_task_run


class DailyActivityProcessTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return daily_activity_task_run


class ClockAction:
    """定时执行函数"""

    def __init__(self, _callable: Callable[[], None], seconds: float):
        self.callable = _callable
        self.seconds = seconds
        self.start_time = datetime.now()
        self.monotonic = None

    def action(self):
        if self.monotonic is None or time.monotonic() - self.monotonic > self.seconds:
            self.monotonic = time.monotonic()
            self.callable()


def mouse_reset_task_run(event: Event, **kwargs):
    logging_config.setup_logging()
    logger.info("鼠标重置进程启动成功")
    mouse = Controller()
    last_position = mouse.position
    hwnd = None
    try:
        while event is None or not event.is_set():
            time.sleep(0.2)
            if not hwnd or not win32gui.IsWindow(hwnd):
                time.sleep(0.5)
                try:
                    hwnd = hwnd_util.get_hwnd()
                except Exception:
                    logger.warning("MouseReset: 获取窗口句柄时异常")
                continue
            current_position = mouse.position
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            center_position = (left + right) / 2, (top + bottom) / 2
            cur_pos_to_center_distance = math.sqrt(
                (current_position[0] - center_position[0]) ** 2
                + (current_position[1] - center_position[1]) ** 2
            )
            cur_pos_to_last_pos_distance = math.sqrt(
                (current_position[0] - last_position[0]) ** 2
                + (current_position[1] - last_position[1]) ** 2
            )
            if cur_pos_to_last_pos_distance > 200 and cur_pos_to_center_distance < 50:
                mouse.position = last_position
            else:
                last_position = current_position
    except KeyboardInterrupt:
        logger.info("鼠标重置进程结束")


def auto_boss_task_run(event: Event, **kwargs):
    logging_config.setup_logging()
    logger.info("刷boss任务进程开始运行")
    hwnd_util.set_hwnd_left_top()

    context = Context()
    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    img_service: ImgService = container.img_service()
    ocr_service: OCRService = container.ocr_service()
    control_service: ControlService = container.control_service()
    page_event_service: PageEventService = container.auto_boss_service()

    logger.debug("-------- run ----------")
    count = 0
    clock_action = ClockAction(control_service.activate, 3.0)
    try:
        while not event.is_set():
            count += 1
            # logger.info("count %s", count)
            clock_action.action()

            src_img = img_service.screenshot()
            img = img_service.resize(src_img)
            result = ocr_service.ocr(img)
            page_event_service.execute(src_img=src_img, img=img, ocr_results=result)
    except KeyboardInterrupt:
        logger.info("刷boss任务进程结束")
    finally:
        try:
            keymouse_util.key_up(window_service.window, "W")
            keymouse_util.key_up(window_service.window, "LSHIFT")
        except Exception:
            pass


def auto_pickup_task_run(event: Event, **kwargs):
    logging_config.setup_logging()
    logger.info("自动拾取任务进程开始运行")
    context = Context()
    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    control_service: ControlService = container.control_service()
    page_event_service: PageEventService = container.auto_pickup_service()
    clock_action = ClockAction(control_service.activate, 3.0)
    try:
        while not event.is_set():
            clock_action.action()
            page_event_service.execute()
    except KeyboardInterrupt:
        logger.info("自动拾取任务进程结束")
    finally:
        try:
            keymouse_util.key_up(window_service.window, "W")
            keymouse_util.key_up(window_service.window, "LSHIFT")
        except Exception:
            pass


def auto_story_task_run(event: Event, **kwargs):
    logging_config.setup_logging()
    logger.info("自动剧情任务进程开始运行")

    for k,v in kwargs.items():
        os.environ[k] = v

    context = Context()
    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    control_service: ControlService = container.control_service()
    page_event_service: PageEventService = container.auto_story_service()
    clock_action = ClockAction(control_service.activate, 3.0)
    try:
        while not event.is_set():
            clock_action.action()
            page_event_service.execute()
    except KeyboardInterrupt:
        logger.info("自动剧情任务进程结束")
    finally:
        try:
            keymouse_util.key_up(window_service.window, "W")
            keymouse_util.key_up(window_service.window, "LSHIFT")
        except Exception:
            pass


def daily_activity_task_run(event: Event):
    logging_config.setup_logging()
    logger.info("每日任务进程开始运行")
    hwnd_util.set_hwnd_left_top()
    context = Context()
    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    control_service: ControlService = container.control_service()
    page_event_service: PageEventService = container.daily_activity_service()
    # clock_action = ClockAction(control_service.activate, 3.0)
    try:
        # while not event.is_set():
        #     clock_action.action()
        page_event_service.execute()
    except KeyboardInterrupt:
        logger.info("每日任务进程结束")
    finally:
        try:
            keymouse_util.key_up(window_service.window, "W")
            keymouse_util.key_up(window_service.window, "LSHIFT")
        except Exception:
            pass


if __name__ == '__main__':
    _stop_event = Event()
    # AutoBossProcessTask.build(args=(_stop_event,), daemon=True).start()
    MouseResetProcessTask.build(args=(_stop_event,), daemon=True).start().join()
