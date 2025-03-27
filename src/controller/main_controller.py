import logging
import time
from enum import Enum
from multiprocessing import Event, Lock

logger = logging.getLogger(__name__)


class TaskOpsEnum(Enum):
    START = "START"
    STOP = "STOP"


class MainController:

    def __init__(self):
        from src.core.tasks import MouseResetProcessTask, AutoBossProcessTask, AutoPickupProcessTask, \
            AutoStoryProcessTask, DailyActivityProcessTask, ProcessTask

        self.tasks = {
            "MouseResetProcessTask": MouseResetProcessTask,
            "AutoBossProcessTask": AutoBossProcessTask,
            "AutoPickupProcessTask": AutoPickupProcessTask,
            "AutoStorySkipProcessTask": AutoStoryProcessTask,
            "AutoStoryEnjoyProcessTask": AutoStoryProcessTask,
            "DailyActivityProcessTask": DailyActivityProcessTask,
        }
        self.running_tasks: dict[str, tuple[ProcessTask, Event]] = {}
        self._lock: Lock = Lock()

    def execute(self, task_name: str, task_ops: str):
        logger.debug("task_name: %s, task_ops: %s", task_name, task_ops)
        with self._lock:
            if task_ops == TaskOpsEnum.START.value:
                logger.info("准备开启任务: %s", task_name)
                if self.running_tasks.get(task_name):
                    logger.warning("任务已存在，请勿重复提交")
                    return False, "任务已存在，请勿重复提交"
                stop_event = Event()
                task_builder = self.tasks.get(task_name)

                kwargs = {}
                if task_name == "AutoStorySkipProcessTask":
                    kwargs["SKIP_IS_OPEN"] = "True"
                task = task_builder.build(args=(stop_event,), kwargs=kwargs, daemon=True).start()
                self.running_tasks[task_name] = (task, stop_event)
                if task_name in ["AutoBossProcessTask", "DailyActivityProcessTask"]:
                    from src.core.tasks import MouseResetProcessTask
                    mouse_reset_process_task = MouseResetProcessTask.build(args=(stop_event,), kwargs=kwargs, daemon=True).start()
                    self.running_tasks["MouseResetProcessTask"] = (mouse_reset_process_task, stop_event)
                logger.info("任务已提交: %s", task_name)
                return True, "任务已提交"
            elif task_ops == TaskOpsEnum.STOP.value:
                logger.info("准备关闭任务: %s", task_name)
                if not self.running_tasks.get(task_name):
                    logger.warning("任务不存在，无需关闭")
                    return True, "任务不存在，无需关闭"
                task, stop_event = self.running_tasks[task_name]
                stop_event.set()
                time.sleep(1)
                task.stop()
                self.running_tasks.pop(task_name)
                if self.running_tasks.get("MouseResetProcessTask"):
                    task, stop_event = self.running_tasks["MouseResetProcessTask"]
                    # stop_event.set()
                    task.stop()
                    self.running_tasks.pop("MouseResetProcessTask")
                logger.info("任务已停止: %s", task_name)
                return True, "任务已停止"
            else:
                raise NotImplementedError(f"不支持的类型{task_ops}")


if __name__ == '__main__':
    from src.config import logging_config

    logging_config.setup_logging_test()
    main_controller = MainController()

    # main_controller.execute("MouseResetController", TaskOpsEnum.START.value)
    main_controller.execute("AutoBossController", TaskOpsEnum.START.value)
    # main_controller.execute("AutoPickupController", TaskOpsEnum.START.value)
    # main_controller.execute("AutoStoryController", TaskOpsEnum.START.value)
    # main_controller.execute("DailyActivityController", TaskOpsEnum.START.value)
    time.sleep(10000000)
