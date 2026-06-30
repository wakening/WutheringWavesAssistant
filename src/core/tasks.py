import json
import logging
import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Process
from typing import Iterable, Any, TypeVar, Callable, Mapping, Optional

import psutil
import win32gui

from src.config import logging_config
from src.core import message
from src.core.contexts import Context
from src.core.exceptions import ScreenshotError
from src.core.geometry import AnchorPoint, Align
from src.core.interface import ImgService, OCRService, ControlService, PageEventService, WindowService
from src.core.message import MsgSource, MsgTaskStatus, MsgType
from src.core.runtime import RuntimeConfig
from src.core.workflow import TaskSpec, IPCManager, NodeContext
from src.util import hwnd_util, keymouse_util, file_util

logger = logging.getLogger(__name__)

Task = TypeVar('Task', bound='ProcessTask')


class ProcessTask(ABC):

    def __init__(self, name: str | None, args: Iterable[Any] | None, kwargs: Mapping[str, Any], daemon: bool | None):
        self.name: str | None = name
        self.args: Iterable[Any] | None = args
        self.kwargs: Mapping[str, Any] = kwargs
        self.daemon: bool | None = daemon

        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._restart_time_list: list[datetime] = []
        self._process: Process | threading.Thread | None = None

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
        task = cls(args=args, kwargs=kwargs, name=name, daemon=daemon)
        # task._process = Process(target=task.get_task(), args=args, kwargs=kwargs, name=task.name, daemon=task.daemon)
        return task

    def start(self):
        self._process = Process(
            target=self.get_task(), args=self.args, kwargs=self.kwargs, name=self.name, daemon=self.daemon)
        self._start_time = datetime.now()
        self._process.start()
        return self

    def stop(self, timeout=3):
        self._end_time = datetime.now()
        elapsed_time = (self._end_time - self._start_time).total_seconds()
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.info(f"[{self.name}] 任务结束，已运行: {int(hours)}h {int(minutes)}m {seconds:.2f}s")
        self._stop(timeout=timeout)
        return self

    def _stop(self, timeout=3):
        if self._process is None:
            return
        try:
            if not self._process.is_alive():
                return
            self._process.terminate()
            if timeout > 0:
                self._process.join(timeout)
        except Exception:
            logger.exception(f"任务[{self.name}]结束失败")

    def join(self):
        self._process.join()

    def is_alive(self):
        return self._process.is_alive()

    def restart(self, timeout=3):
        self._stop(timeout=timeout)
        if len(self._restart_time_list) > 0:
            start_time_last = self._restart_time_list[-1]
        else:
            start_time_last = self._start_time
        restart_time = datetime.now()
        logger.warning(f"[{self.name}] 任务重启，上次重启时间: {start_time_last.strftime("%Y-%m-%d %H:%M:%S")}")
        self._restart_time_list.append(restart_time)
        self._process = Process(
            target=self.get_task(), args=self.args, kwargs=self.kwargs, name=self.name, daemon=self.daemon)
        self._process.start()


class ThreadTask(ProcessTask):

    def start(self):
        self._process = threading.Thread(
            target=self.get_task(), args=self.args, kwargs=self.kwargs, name=self.name, daemon=self.daemon)
        self._start_time = datetime.now()
        self._process.start()
        return self

    def _stop(self, timeout=3):
        if self._process is None:
            return
        try:
            if not self._process.is_alive():
                return
            # self._process.terminate()
            if timeout > 0:
                self._process.join(timeout)
        except Exception:
            logger.exception(f"任务[{self.name}]结束失败")

    def restart(self, timeout=3):
        self._stop(timeout=timeout)
        if len(self._restart_time_list) > 0:
            start_time_last = self._restart_time_list[-1]
        else:
            start_time_last = self._start_time
        restart_time = datetime.now()
        logger.warning(f"[{self.name}] 任务重启，上次重启时间: {start_time_last.strftime("%Y-%m-%d %H:%M:%S")}")
        self._restart_time_list.append(restart_time)
        # self._process = Process(
        #     target=self.get_task(), args=self.args, kwargs=self.kwargs, name=self.name, daemon=self.daemon)
        self._process = threading.Thread(
            target=self.get_task(), args=self.args, kwargs=self.kwargs, name=self.name, daemon=self.daemon)
        self._process.start()


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


class EchoMergeProcessTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return echo_merge_task_run


class SoarToTheBeatMacroReplayTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return soar_to_the_beat_macro_replay_task


class SoarToTheBeatMacroRecordTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None] | None:
        return soar_to_the_beat_macro_record_task


class DailyTask(ProcessTask):
    def get_task(self, *args) -> Callable[..., None]:
        return daily_task


@dataclass
class TaskMsg:
    task_name: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    position: Optional[str] = None
    duration: Optional[int] = None
    parent: Optional[str] = None


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
            try:
                self.callable()
            except Exception:
                pass


def create_parent_monitor(event, pid: int):
    def run():
        try:
            # 获取父进程
            parent_process = psutil.Process(pid)
        except Exception as e:
            logger.error(e)
            return
        while event.is_set():
            try:
                if not parent_process.is_running():
                    event.clear()
                    logger.info("检测到父进程结束，退出任务")
                    break  # 父进程退出后，子进程退出
            except Exception as e:
                logger.exception(e)
                return
            time.sleep(5)
        logger.info("父进程监控结束")

    monitor_thread = threading.Thread(target=run, name="ParentPidMonitorThread")
    monitor_thread.daemon = True
    monitor_thread.start()
    return monitor_thread


def create_mouse_reset_monitor(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    def run(**run_kwargs):
        # mouse_reset_task_run(event, spec, ipc, **run_kwargs)
        from src.util import cursor_guard_util
        return cursor_guard_util.run(event, spec=spec, ipc=ipc, **run_kwargs)

    monitor_thread = threading.Thread(target=run, kwargs=kwargs, name="MouseResetMonitorThread")
    monitor_thread.daemon = True
    monitor_thread.start()
    return monitor_thread


def mouse_reset_task_run(event, spec, ipc, **kwargs):
    logging_config.setup_logging(ipc.log_queue)
    logger.info("鼠标重置任务开始运行")
    from pynput.mouse import Controller
    mouse = Controller()
    last_position = mouse.position
    hwnd = None
    hwnd_util.enable_dpi_awareness()
    try:
        while event.is_set():
            time.sleep(0.02)
            try:
                if not hwnd or not win32gui.IsWindow(hwnd):
                    time.sleep(0.5)
                    hwnd = hwnd_util.get_hwnd()
                    continue
            except Exception:
                logger.warning("MouseReset: 获取窗口句柄时异常")
                time.sleep(5)
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
        pass
    finally:
        logger.info("鼠标重置任务结束")


def auto_boss_task_run(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    try:
        from src.core.injector import Container

        logging_config.setup_logging(ipc.log_queue)
        # logger.debug(f"spec: {json.dumps(spec.__dict__)}")
        logger.info("刷boss任务进程开始运行")

        context = Context()
        context.spec = spec
        # 从快照还原配置
        context.param_config = spec.param_config
        # 新旧配置兼容
        context.app_config.TargetBoss = context.param_config.get_boss_name_list()
        logger.info("Boss Rush: %s", context.app_config.TargetBoss)
        context.app_config.DungeonWeeklyBossLevel = context.param_config.get_boss_level_int()

        container = Container.build(context)
        logger.debug("Create application context")
        window_service: WindowService = container.window_service()
        img_service: ImgService = container.img_service()
        ocr_service: OCRService = container.ocr_service()
        control_service: ControlService = container.control_service()

        # 1. 先获取当前鼠标位置
        original_x, original_y = keymouse_util.get_mouse_position()
        # 2. 释放鼠标限制（如果有）
        keymouse_util.set_mouse_unlocked()
        # # 3. 取消游戏窗口的置顶状态
        # hwnd_util.set_window_not_topmost(window_service.window)
        # # 4. 移动窗口
        gui_win_id = spec.gui_win_id
        # hwnd_util.set_window_left_top_and_below_another(window_service.window, gui_win_id)
        hwnd_util.set_window_left_top(window_service.window)
        # 5. 将鼠标移回原位
        keymouse_util.set_mouse_position(original_x, original_y)

        context.boss_task_ctx.gui_win_id = gui_win_id

        time.sleep(0.2)
        logger.debug(spec.game_path)
        create_parent_monitor(event, spec.leader_pid)
        create_mouse_reset_monitor(event, spec, ipc, **kwargs)
        clock_action = ClockAction(control_service.activate, 3.0)

        logger.debug("-------- run ----------")
        count = 0

        page_event_service: PageEventService = container.auto_boss_service()

        try:
            while event.is_set():
                try:
                    count += 1
                    # logger.info("count %s", count)
                    clock_action.action()

                    src_img = img_service.screenshot()
                    img = img_service.resize(src_img)
                    result = ocr_service.ocr(img)
                    page_event_service.execute(src_img=src_img, img=img, ocr_results=result)
                except ScreenshotError:
                    try:
                        logger.warning("截图异常，关闭游戏")
                        hwnd_util.force_close_process(window_service.window)
                    except Exception:
                        logger.error("关闭游戏时异常")
                    raise
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt")
        except Exception as e:
            logger.exception(e)
        finally:
            try:
                keymouse_util.mouse_left_up(window_service.window, 0, 0)
                keymouse_util.mouse_right_up(window_service.window, 0, 0)
                keymouse_util.key_up(window_service.window, "W")
            except Exception:
                pass
            logger.info("刷boss任务进程结束")
    except Exception as e:
        logger.exception(e)


def auto_pickup_task_run(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    from src.core.injector import Container

    logging_config.setup_logging(ipc.log_queue)
    # logger.debug(f"spec: {json.dumps(spec.__dict__)}")
    logger.info("自动拾取任务进程开始运行")

    context = Context()
    context.spec = spec
    # 从快照还原配置
    context.param_config = spec.param_config
    # 新旧配置兼容
    context.app_config.TargetBoss = context.param_config.get_boss_name_list()
    logger.debug("TargetBoss: %s", context.app_config.TargetBoss)
    context.app_config.DungeonWeeklyBossLevel = context.param_config.get_boss_level_int()

    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    # img_service: ImgService = container.img_service()
    # ocr_service: OCRService = container.ocr_service()
    control_service: ControlService = container.control_service()

    # hwnd_util.set_window_left_top(window_service.window)
    # time.sleep(0.2)
    logger.debug(spec.game_path)
    create_parent_monitor(event, spec.leader_pid)
    # create_mouse_reset_monitor(event, spec, ipc, **kwargs)
    clock_action = ClockAction(control_service.activate, 3.0)

    page_event_service: PageEventService = container.auto_pickup_service()

    try:
        while event.is_set():
            clock_action.action()
            try:
                page_event_service.execute()
            except ScreenshotError:
                logger.exception("截图失败")
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("自动拾取任务进程结束")
    except Exception as e:
        logger.exception(e)
    finally:
        try:
            keymouse_util.mouse_left_up(window_service.window, 0, 0)
            keymouse_util.mouse_right_up(window_service.window, 0, 0)
            keymouse_util.key_up(window_service.window, "W")
        except Exception:
            pass


def auto_story_task_run(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    from src.core.injector import Container

    logging_config.setup_logging(ipc.log_queue)
    # logger.debug(f"spec: {json.dumps(spec.__dict__)}")
    logger.info("自动剧情任务进程开始运行")

    context = Context()
    context.spec = spec
    # 从快照还原配置
    context.param_config = spec.param_config
    # 新旧配置兼容
    context.app_config.TargetBoss = context.param_config.get_boss_name_list()
    logger.debug("TargetBoss: %s", context.app_config.TargetBoss)
    context.app_config.DungeonWeeklyBossLevel = context.param_config.get_boss_level_int()

    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    # img_service: ImgService = container.img_service()
    # ocr_service: OCRService = container.ocr_service()
    control_service: ControlService = container.control_service()

    # hwnd_util.set_window_left_top(window_service.window)
    # time.sleep(0.2)
    logger.debug(spec.game_path)
    create_parent_monitor(event, spec.leader_pid)
    # create_mouse_reset_monitor(event, spec, ipc, **kwargs)
    clock_action = ClockAction(control_service.activate, 3.0)

    page_event_service: PageEventService = container.auto_story_service()
    count = 0

    try:
        while event.is_set():
            logger.debug("count: %s", count)
            count += 1
            clock_action.action()
            try:
                page_event_service.execute()
            except ScreenshotError as e:
                logger.exception("截图失败")
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("自动剧情任务进程结束")
    except Exception as e:
        logger.exception(e)
    finally:
        try:
            keymouse_util.mouse_left_up(window_service.window, 0, 0)
            keymouse_util.mouse_right_up(window_service.window, 0, 0)
            keymouse_util.key_up(window_service.window, "W")
        except Exception:
            pass


def task_init(event, spec: TaskSpec, ipc: IPCManager, is_thread=False, source=None, **kwargs):
    """ 初始化任务运行环境，加载日志、上下文 """

    from src.core.injector import Container

    if not is_thread:
        logging_config.setup_logging(ipc.log_queue)
    # logger.debug(f"spec: {json.dumps(spec.__dict__)}")
    hwnd_util.enable_dpi_awareness()

    ctx = NodeContext()
    ctx.spec = spec
    ctx.ipc = ipc
    ctx.runtime.stop_event = event
    ctx.runtime.cfg = RuntimeConfig(spec.user_config)
    ctx.runtime.send = message.make_sender(ipc.proc_queue, source, spec.task_id)

    container = Container.build(ctx)
    logger.debug("Create application context")
    logger.debug(spec.game_path)

    if ctx.runtime.cfg and ctx.runtime.cfg.game:
        ctx.window_service.set_lang(ctx.runtime.cfg.game.gameLanguage)

    return ctx, container


def release_press_key(ctx):
    try:
        keymouse_util.mouse_left_up(ctx.window_service.window, 0, 0)
        keymouse_util.mouse_right_up(ctx.window_service.window, 0, 0)
        keymouse_util.key_up(ctx.window_service.window, "W")
        keymouse_util.key_up(ctx.window_service.window, "A")
        keymouse_util.key_up(ctx.window_service.window, "S")
        keymouse_util.key_up(ctx.window_service.window, "D")
    except Exception:
        pass


def echo_merge_task_run(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    try:
        ctx, container = task_init(event, spec, ipc, **kwargs)
        logger.info("声骸融合任务进程开始运行")

        time.sleep(0.2)
        logger.debug(spec.game_path)
        create_parent_monitor(event, spec.leader_pid)
        create_mouse_reset_monitor(event, spec, ipc, **kwargs)
        clock_action = ClockAction(ctx.control_service.activate, 3.0)

        logger.debug("-------- run ----------")
        count = 0

        from src.service.echo_merge_workflow import EchoMergeWorkflow
        workflow = EchoMergeWorkflow(ctx)

        try:
            try:
                count += 1
                clock_action.action()

                workflow.execute()
            except ScreenshotError:
                try:
                    logger.warning("截图异常，关闭游戏")
                    hwnd_util.force_close_process(ctx.window_service.window)
                except Exception:
                    logger.error("关闭游戏时异常")
                raise
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt")
        except Exception as e:
            logger.exception(e)

            ctx.ipc.event_queue.put({
                "task": {"SoarToTheBeatMacroReplayTask": ["failed"]}
            }, block=True)
        finally:
            release_press_key(ctx)
            logger.info("声骸融合任务进程结束")
    except Exception as e:
        logger.exception(e)


def soar_to_the_beat_macro_replay_task(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    try:
        ctx, container = task_init(event, spec, ipc, is_thread=True, **kwargs)
        logger.info("自动音游任务线程开始运行")
        logger.debug(spec.game_path)
        time.sleep(0.1)

        config = ctx.spec.param_config

        # 用户模板
        if config.useUserTemplate:
            if not config.userTemplate:
                logger.error("勾选使用自定义，但未选择自定义模板")
                ctx.ipc.event_queue.put({
                    "task": {"SoarToTheBeatMacroReplayTask": ["failed", "勾选使用自定义，但未选择自定义模板"]}
                }, block=True)
                time.sleep(0.1)
                return
            file_name = file_util.get_assets_macro_SoarToTheBeat(config.userTemplate)
        else:
            # 预设模板
            if not config.defaultTemplate:
                logger.error("未选择模板文件")
                ctx.ipc.event_queue.put({
                    "task": {"SoarToTheBeatMacroReplayTask": ["failed", "未选择模板文件"]}
                }, block=True)
                time.sleep(0.1)
                return
            file_name = file_util.get_assets_macro_SoarToTheBeat_template(config.defaultTemplate)
        logger.debug(f"load: {file_name}")

        try:
            from src.util import macro_replay_util
            macro_replay_util.run(file_name, ctx.window_service.window, macro_point_scaler(ctx))

            ctx.ipc.event_queue.put({
                "task": {"SoarToTheBeatMacroReplayTask": ["finished"]}
            }, block=True)
            time.sleep(0.1)
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt")
        except Exception as e:
            logger.exception(e)

            ctx.ipc.event_queue.put({
                "task": {"SoarToTheBeatMacroReplayTask": ["failed"]}
            }, block=True)
            time.sleep(0.1)
        finally:
            release_press_key(ctx)
            logger.info("自动音游任务线程结束")
    except Exception as e:
        logger.exception(e)


def soar_to_the_beat_macro_record_task(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    try:
        ctx, container = task_init(event, spec, ipc, is_thread=True, **kwargs)
        logger.info("按键宏录制任务线程开始运行")

        time.sleep(0.2)
        logger.debug(spec.game_path)

        filename = f"Record_{datetime.now().strftime('%Y%m%d%H%M%S_%f')[:19]}.txt"
        filename = str(file_util.get_assets_macro_SoarToTheBeat().joinpath(filename))
        logger.debug(f"filename: {filename}")

        try:
            from src.util import macro_record_util
            is_saved = macro_record_util.run(filename, ctx.window_service.window, macro_point_scaler(ctx))

            ctx.ipc.event_queue.put({
                "task": {"SoarToTheBeatMacroRecordTask": ["finished", filename] if is_saved else ["finished"]}
            }, block=True)
            time.sleep(0.2)
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt")
        except Exception as e:
            logger.exception(e)

            ctx.ipc.event_queue.put({
                "task": {"SoarToTheBeatMacroRecordTask": ["failed"]}
            }, block=True)
            time.sleep(0.2)
        finally:
            release_press_key(ctx)
            logger.info("按键宏录制任务线程结束")
    except Exception as e:
        logger.exception(e)


def macro_point_scaler(ctx):
    from src.util import macro_replay_util
    points_1280_720 = macro_replay_util.TriggerController.POINTS_1280_720
    points = [ctx.scaler.as_point(AnchorPoint(p[0], p[1], Align.Top | Align.Right)).as_tuple() for p in points_1280_720]
    return points


def daily_task(event, spec: TaskSpec, ipc: IPCManager, **kwargs):
    try:

        ctx, container = task_init(event, spec, ipc, source=MsgSource.DAILY_TASK, **kwargs)
        logger.info(f"每日任务开始运行, task_id: {spec.task_id}")
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.RUNNING)

        # 1. 先获取当前鼠标位置
        original_x, original_y = keymouse_util.get_mouse_position()

        ctx.control_service.activate()
        time.sleep(0.05)

        if spec.gui_win_id is not None:
            # 3. 取消游戏窗口的置顶状态
            hwnd_util.set_window_not_topmost(ctx.window_service.window)
            # 2. 释放鼠标限制（如果有）
            keymouse_util.set_mouse_unlocked()
            # 4. 移动窗口
            hwnd_util.set_window_below_another(ctx.window_service.window, spec.gui_win_id)
            # 5. 将鼠标移回原位
            keymouse_util.set_mouse_position(original_x, original_y)

        time.sleep(0.2)
        logger.debug(spec.game_path)
        create_parent_monitor(event, spec.leader_pid)
        create_mouse_reset_monitor(event, spec, ipc, **kwargs)

        try:
            from src.service.daily_workflow import DailyWorkflow

            wf = DailyWorkflow(ctx)
            wf.execute()

        except KeyboardInterrupt as e:
            logger.warning(f"KeyboardInterrupt: {e}")
        except Exception as e:
            logger.exception(e)
            ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.FAILED)

            ctx.ipc.event_queue.put({
                "task": {"DailyTask": ["failed"]}
            }, block=True)
            time.sleep(0.1)
        finally:
            logger.info(f"每日任务结束, task_id: {spec.task_id}")
            release_press_key(ctx)

    except Exception as e:
        logger.exception(e)

# if __name__ == '__main__':
#     _stop_event = Event()
#     _stop_event.set()
#     # AutoBossProcessTask.build(args=(_stop_event,), daemon=True).start()
#     MouseResetProcessTask.build(args=(_stop_event,), daemon=True).start().join()
