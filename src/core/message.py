import logging
import multiprocessing
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MsgType(Enum):
    LOG = auto()
    TASK_STATUS = auto()
    ERROR = auto()
    STATS = auto()
    EVENT = auto()


class MsgTaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()


class MsgSource(Enum):
    SCREENSHOT = auto()
    WINDOW = auto()
    INPUT = auto()
    TASK = auto()
    SYSTEM = auto()
    WORKFLOW = auto()

    DAILY_TASK = auto()


@dataclass
class Message:
    type: MsgType
    source: MsgSource
    data: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=time.time)


class MessageBus:
    """ 消息总线 """

    def __init__(self):
        self._handlers = []
        self._lock = threading.Lock()

    def subscribe(
            self,
            handler: Callable,
            msg_type: Optional[MsgType] = None,
            source: Optional[MsgSource] = None,
    ):
        """ 注册订阅 """
        with self._lock:
            self._handlers.append((handler, msg_type, source))

    def publish(self, msg: Message):
        with self._lock:
            handlers = list(self._handlers)

        for handler, mtype, src in handlers:
            if mtype and msg.type != mtype:
                continue
            if src and msg.source != src:
                continue

            try:
                handler(msg)
            except Exception:
                logger.exception("[MessageBus] handler error")


class ProcessBridge:
    """ 跨进程桥接 """

    def __init__(self, bus: MessageBus):
        self.queue = multiprocessing.Queue()
        self.bus = bus
        self._running = False

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self._running:
            try:
                msg = self.queue.get()
                self.bus.publish(msg)
            except Exception:
                logger.exception("[ProcessBridge] handler error")


def make_sender(queue_or_bus, source: MsgSource, task_id: str):
    """ 构建任务消息发送器 """

    def send(msg_type: MsgType, **data):
        msg = Message(
            type=msg_type,
            source=source,
            data=data,
            task_id=task_id,
        )

        # 自动适配 queue 或 bus
        if hasattr(queue_or_bus, "put"):
            queue_or_bus.put(msg)
        else:
            queue_or_bus.publish(msg)

    return send


######## demo
#
# def worker_main(queue, task_id: str):
#     send = make_sender(queue, MsgSource.WINDOW, task_id)
#
#     send(MsgType.TASK_STATUS, status=MsgTaskStatus.RUNNING)
#
#     for i in range(5):
#         time.sleep(1)
#         send(MsgType.STATS, step=i)
#
#     send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
#
#
# def run_small_task(bus: MessageBus, task_id: str):
#     send = make_sender(bus, MsgSource.TASK, task_id)
#
#     send(MsgType.TASK_STATUS, status=MsgTaskStatus.RUNNING)
#
#     # do something...
#
#     send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
#
#
# class Server:
#     def __init__(self):
#         self.bus = MessageBus()
#
#         # 跨进程桥
#         self.proc_bridge = ProcessBridge(self.bus)
#         self.proc_bridge.start()
#
#         # 注册订阅
#         self.bus.subscribe(self._handle_log, MsgType.LOG)
#         self.bus.subscribe(self._handle_task, MsgType.TASK_STATUS)
#
#     def start_process_task(self):
#         task_id = "task_" + str(int(time.time()))
#
#         p = multiprocessing.Process(
#             target=worker_main,
#             args=(self.proc_bridge.queue, task_id),
#         )
#         p.start()
#
#     def start_thread_task(self):
#         task_id = "task_" + str(int(time.time()))
#
#         t = threading.Thread(
#             target=run_small_task,
#             args=(self.bus, task_id),
#         )
#         t.start()
#
#     def _handle_log(self, msg: Message):
#         logger.info(f"[LOG][{msg.source.name}] {msg.data}")
#
#     def _handle_task(self, msg: Message):
#         logger.info(f"[TASK][{msg.task_id}] {msg.data.get('status')}")

# from PySide6.QtCore import QObject, Signal
#
#
# class QtBridge(QObject):
#     message_signal = Signal(object)
#
#     def handle(self, msg: Message):
#         self.message_signal.emit(msg)
#
#
#
# @dataclass
# class TaskInfo:
#     task_id: str
#     status: MsgTaskStatus
#     source: MsgSource
#
#     progress: float = 0.0
#     error: Optional[str] = None
#
#     start_time: float = field(default_factory=time.time)
#     end_time: Optional[float] = None
#
#
# import threading
#
#
# class TaskManager:
#     def __init__(self, bus: MessageBus):
#         self._tasks = {}
#         self._lock = threading.Lock()
#
#         # 订阅任务状态
#         bus.subscribe(self._handle_task, MsgType.TASK_STATUS)
#
#     def _handle_task(self, msg: Message):
#         task_id = msg.task_id
#         status = msg.data.get("status")
#
#         with self._lock:
#             if task_id not in self._tasks:
#                 self._tasks[task_id] = TaskInfo(
#                     task_id=task_id,
#                     status=status,
#                     source=msg.source
#                 )
#
#             task = self._tasks[task_id]
#
#             # 更新状态
#             task.status = status
#
#             if status == MsgTaskStatus.RUNNING:
#                 task.start_time = msg.ts
#
#             elif status in (MsgTaskStatus.SUCCESS, MsgTaskStatus.FAILED):
#                 task.end_time = msg.ts
#
#             # 可选字段
#             if "progress" in msg.data:
#                 task.progress = msg.data["progress"]
#
#             if "error" in msg.data:
#                 task.error = msg.data["error"]
#
#     # ========= 对外接口 =========
#
#     def get(self, task_id: str) -> Optional[TaskInfo]:
#         with self._lock:
#             return self._tasks.get(task_id)
#
#     def list_all(self):
#         with self._lock:
#             return list(self._tasks.values())
#
#     def is_running(self, task_id: str) -> bool:
#         t = self.get(task_id)
#         return t and t.status == MsgTaskStatus.RUNNING
#
#
# class Server:
#     def __init__(self):
#         self.bus = MessageBus()
#
#         self.proc_bridge = ProcessBridge(self.bus)
#         self.proc_bridge.start()
#
#         # 加这一行
#         self.task_manager = TaskManager(self.bus)
