import base64
import logging
import multiprocessing
import queue
import random
import secrets
import sys
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from functools import singledispatchmethod
from typing import Callable, Dict, Optional, Any, List, Tuple

from src.config.gui_config import ParamConfig
from src.core.exceptions import StopError
from src.core.geometry import Scaler
from src.core.i18n import I18nTr
from src.core.interface import WindowService, ImgService, OCRService, ControlService, ODService, BossInfoService, \
    CombatService, PageEventService
from src.core.runtime import RuntimeConfig
from src.core.task import TaskFSM

logger = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    start_time: float = field(default_factory=time.time)
    # 由workflow engine实时存入
    current_node: Optional[Tuple[str, str]] = None
    last_node: Optional[Tuple[str, str]] = None
    # 由task启动后存入，type: threading.Event / multiprocessing.Event
    stop_event: Optional[Any] = None
    # 由task启动后存入， message.make_sender
    send: Optional[Callable[..., Any]] = None
    # 配置文件
    cfg: Optional[RuntimeConfig] = None
    # 由workflow启动后存入
    taskFSM: Optional[TaskFSM] = None


@dataclass
class StatsContext:
    node_runs: Dict[str, Dict[str, int]] = field(default_factory=dict)
    node_time: Dict[str, Dict[str, float]] = field(default_factory=dict)
    retries: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class SharedContext:
    fight_count: int = 0
    boss_name: Optional[str] = None
    last_result: Optional[Any] = None
    # 角色编队
    team_members: Optional[list[str | None]] = None
    # 是否有角色失去意识
    is_resonator_downed: bool = field(default=False)
    # 登录时是否移动窗口
    login_mv_window: bool = field(default=False)


class Services:
    def __init__(self, container):
        self._c = container

    # ===== 基础能力 =====

    @property
    def window_service(self) -> WindowService:
        return self._c.window_service()

    @property
    def img_service(self) -> ImgService:
        return self._c.img_service()

    @property
    def ocr_service(self) -> OCRService:
        return self._c.ocr_service()

    @property
    def control_service(self) -> ControlService:
        return self._c.control_service()

    @property
    def od_service(self) -> ODService:
        return self._c.od_service()

    # ===== 页面 =====

    @property
    def page_event_service(self) -> PageEventService:
        return self._c.page_event_service()

    # ===== 其他 =====

    @property
    def boss_info_service(self) -> BossInfoService:
        return self._c.boss_info_service()

    @property
    def combat_service(self) -> CombatService:
        return self._c.combat_service()


# @dataclass(frozen=True)
@dataclass
class TaskSpec:
    """ Task Specification """

    # 节点唯一id
    task_id: str = field(default_factory=lambda: TaskSpec.create_task_id())
    task_name: Optional[str] = None
    trace_id: Optional[str] = field(default_factory=lambda: TaskSpec.create_trace_id())
    # 主进程id
    leader_pid: Optional[int] = None
    # gui窗口id
    gui_win_id: Optional[int] = None
    # 启动参数
    cli_args: Optional[List[Any]] = None
    # 系统
    platform: str = sys.platform
    device: Optional[str] = None
    # 游戏路径，用于重启游戏
    game_path: Optional[str] = None
    # 游戏文本语言
    game_lang: Optional[str] = None
    # 配置文件
    param_config_path: Optional[str] = None
    param_config_snapshot: Optional[str] = None
    param_config: Optional[ParamConfig] = None
    user_config: dict = field(default_factory=dict)
    # 是否开启自动跳过
    skip_is_open: Optional[bool] = None
    # ocr是否使用gpu
    ocr_use_gpu: Optional[bool] = None

    @staticmethod
    def create_task_id():
        # task_id = uuid.uuid4().hex
        task_id = f"{datetime.now().strftime('%y%m%d%H%M%S')}{random.randint(0, 9999):04d}"
        logger.debug(f"task_id: {task_id}")
        return task_id

    @staticmethod
    def create_trace_id():
        trace_id = base64.urlsafe_b64encode(secrets.token_bytes(12)).decode()
        logger.debug(f"trace_id: {trace_id}")
        return trace_id


@dataclass
class IPCManager:
    log_queue: Optional[multiprocessing.Queue] = None
    event_queue: Optional[multiprocessing.Queue] | Optional[queue.Queue] = None
    proc_queue: Optional[multiprocessing.Queue] = None


@dataclass
class NodeContext:
    runtime: RuntimeContext = field(default_factory=RuntimeContext)
    stats: StatsContext = field(default_factory=StatsContext)
    shared: SharedContext = field(default_factory=SharedContext)

    spec: TaskSpec = field(default_factory=TaskSpec)
    ipc: Optional[IPCManager] = field(default=None)

    _container: Optional[Any] = field(default=None, repr=False)
    _services: Optional[Services] = field(default=None, init=False, repr=False)

    @property
    def services(self) -> Services:
        """ 延迟初始化 Services """
        if self._services is None:
            self._services = Services(self._container)
        return self._services

    @property
    def window_service(self) -> WindowService:
        return self._container.window_service()

    @property
    def img_service(self) -> ImgService:
        return self._container.img_service()

    @property
    def ocr_service(self) -> OCRService:
        return self._container.ocr_service()

    @property
    def control_service(self) -> ControlService:
        return self._container.control_service()

    @property
    def od_service(self) -> ODService:
        return self._container.od_service()

    @property
    def page_event_service(self) -> PageEventService:
        return self._container.page_event_service()

    @property
    def boss_info_service(self) -> BossInfoService:
        return self._container.boss_info_service()

    @property
    def combat_service(self) -> CombatService:
        return self._container.combat_service()

    # --------------- runtime ------------------


    # --------------- Shortcut ------------------

    @property
    def scaler(self) -> Scaler:
        return self.window_service.scaler

    @property
    def tr(self) -> I18nTr:
        return self.window_service.tr


@dataclass
class Transition:
    condition: Callable[[NodeContext], bool]
    dst: Optional[str]
    name: str = ""


# Node 注册器
NODE_REGISTRY: Dict[str, Dict[str, "Node"]] = {}


class Node:

    def __init__(
            self,
            func: Callable,
            name: str,
            namespace: str,
            retry: int = 0,
            timeout: Optional[int] = None,
    ):
        self.func = func
        self.name = name
        self.namespace = namespace
        self.retry = retry
        self.timeout = timeout

    def run(self, ctx: NodeContext, **kwargs):
        attempts = 0
        while True:
            attempts += 1
            start = time.monotonic()
            try:
                if self.timeout and self.timeout > 0:
                    result = self._wait_until(ctx, lambda: self.func(ctx, **kwargs), timeout=self.timeout)
                else:
                    result = self.func(ctx, **kwargs)
                duration = time.monotonic() - start
                node_time = ctx.stats.node_time.setdefault(self.namespace, {}).get(self.name, 0)
                ctx.stats.node_time[self.namespace][self.name] = node_time + duration
                return result
            except Exception as e:
                retries = ctx.stats.retries.setdefault(self.namespace, {}).get(self.name, 0)
                ctx.stats.retries[self.namespace][self.name] = retries + 1
                if attempts > self.retry:
                    raise e
                logger.info(f"[NODE] retry {self.namespace}.{self.name} ({attempts}/{self.retry})")

    def _wait_until(
            self,
            ctx: NodeContext,
            condition: Callable,
            timeout: float,
            interval: float = 0.1,
    ) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if ctx.runtime.stop_event.is_set():
                return False
            if condition():
                return True
            time.sleep(interval)
        return False


def node(name: Optional[str] = None, namespace: Optional[str] = None, retry: int = 0, timeout: Optional[int] = None):
    """
    Node 注册器，无参用 @node() 标记，必须加括号
    :param name: 节点名，默认是函数名
    :param namespace: 命名空间，默认是模块名
    :param retry:
    :param timeout:
    :return:
    """

    if callable(name):
        raise ValueError("You must use @node()")

    def decorator(func):
        _name = name or func.__name__
        _namespace = namespace or func.__module__
        _node_map = NODE_REGISTRY.setdefault(_namespace, {})
        if _name in _node_map:
            raise KeyError(f"Node already registered: {(_namespace, _name)}")
        _node_map[_name] = Node(
            func,
            _name,
            _namespace,
            retry=retry,
            timeout=timeout,
        )
        logger.debug(f"register node: {(_namespace, _name)}")
        return func

    return decorator


class IWorkflow(ABC):

    @abstractmethod
    def execute(self, **kwargs):
        pass


class AbstractWorkflow(IWorkflow, ABC):

    def __init__(self, ctx: NodeContext, **kwargs):
        self.ctx = ctx
        self.start_node: Optional[str] = None
        # 是否作为子工作流嵌入，此为开关，具体需要子类根据开关适配
        self.embedding: bool = False


class WorkflowEngine:
    """
    Workflow Engine
    """

    def __init__(self):
        self.transitions = {}
        self.start_node = None
        self.history = deque(maxlen=666)
        self.error = None

    def source(self, src: str, is_start: bool = False):
        if not src:
            raise ValueError("node name cannot be empty")
        if is_start:
            if self.start_node:
                raise ValueError(f"start node already exists: '{self.start_node}'")
            self.start_node = src

        return TransitionBuilder(self, src)

    def exception(self, src: str):
        """抑制异常，转到指定节点，不包括(KeyboardInterrupt, StopError)"""
        if not src:
            raise ValueError("node name cannot be empty")
        self.error = src

    def add_transition(self, src, condition, dst, name=""):
        self.transitions.setdefault(src, []).append(
            Transition(condition, dst, name)
        )

    @singledispatchmethod
    def run(self, x):
        raise NotImplementedError()

    @run.register
    def _(self, ctx: NodeContext, namespace: str, start_node: Optional[str] = None, **kwargs):
        current = start_node if start_node else self.start_node
        if not namespace:
            raise ValueError("namespace cannot be empty")
        if not current:
            raise ValueError("start node does not exist")
        while current:
            if not ctx.runtime.stop_event.is_set():
                logger.debug("[ENGINE] stopped")
                break
            node = NODE_REGISTRY[namespace][current]
            ctx.runtime.last_node = ctx.runtime.current_node
            ctx.runtime.current_node = (namespace, current)
            node_runs = ctx.stats.node_runs.setdefault(namespace, {}).get(current, 0)
            ctx.stats.node_runs[namespace][current] = node_runs + 1
            self.history.append(ctx.runtime.current_node)
            logger.debug(f"[ENGINE] run: {ctx.runtime.current_node}")

            try:
                result = node.run(ctx, **kwargs)
            except (KeyboardInterrupt, StopError) as e:
                raise e
            except Exception as e:
                ctx.shared.last_result = None
                if self.error:
                    logger.exception(f"[ENGINE] run error: {ctx.runtime.current_node}")
                    current = self.error
                    continue
                logger.error(f"[ENGINE] run error: {ctx.runtime.current_node}")
                raise e

            ctx.shared.last_result = result
            logger.debug(f"[ENGINE] result: {result}")
            next_node = None
            for trans in self.transitions.get(current, []):
                if trans.condition(ctx):
                    logger.debug(f"[ENGINE] hit: {trans.name}")
                    next_node = trans.dst
                    break
            if not next_node:
                logger.debug("[ENGINE] workflow end")
                break
            current = next_node

    @run.register
    def _(self, flow: AbstractWorkflow, **kwargs):
        self.run(flow.ctx, flow.__class__.__module__, start_node=flow.start_node, **kwargs)


class TransitionBuilder:
    """
    DSL Builder
    """

    def __init__(self, wf, src):
        self.wf = wf
        self.src = src
        self._condition = None
        self._name = None

    def on(self, result, name: Optional[str] = None):
        """匹配特定结果"""
        self._condition = lambda ctx: ctx.shared.last_result == result
        self._name = name or f"on({result})"
        return self

    def always(self, name: Optional[str] = None):
        """无条件转移"""
        self._condition = lambda ctx: True
        self._name = name or "always"
        return self

    def when(self, condition: Callable[[NodeContext], bool], name: Optional[str] = None):
        """自定义条件函数"""
        self._condition = condition
        self._name = name or "when()"
        return self

    def to(self, dst: str):
        """目标状态"""
        if dst is None:
            raise ValueError("dst cannot be None")
        self.wf.add_transition(self.src, self._condition, dst, self._name)
        return self

    def emit(self, dst: str):
        """目标状态"""
        self.wf.add_transition(self.src, self._condition, None, self._name)
        return self



# # =========================
# # 示例节点
# # =========================
#
# @node(retry=2)
# def detect(ctx: NodeContext):
#     logger.info("detect boss...")
#     if ctx.shared.fight_count < 3:
#         ctx.shared.boss_name = "Hecate"
#         return "found"
#     return "none"
#
#
# @node()
# def enter(ctx: NodeContext):
#     logger.info("enter instance")
#     return "ok"
#
#
# @node(timeout=5)
# def fight(ctx: NodeContext):
#     logger.info("fight boss")
#     ctx.shared.fight_count += 1
#     if ctx.shared.fight_count >= 3:
#         return "finish"
#     return "win"
#
#
# @node()
# def leave(ctx: NodeContext):
#     logger.info("leave instance")
#     return "done"
#
#
# if __name__ == '__main__':
#     # =========================
#     # 构建 Workflow
#     # =========================
#
#     wf = WorkflowEngine()
#
#     wf.source("detect").on("found").to("enter")
#     wf.source("detect").on("none").to("leave")
#
#     wf.source("enter").on("ok").to("fight")
#
#     wf.source("fight").on("win").to("detect")
#     wf.source("fight").on("finish").to("leave")
#
#     wf.source("leave").on("done").to(None)
#
#     (
#         wf.source("fight")
#         .when(lambda ctx: ctx.shared.fight_count >= 3).to(None)
#         .when(lambda ctx: ctx.shared.last_result == "win").to("wait")
#         .otherwise("start")
#     )
#
#     # =========================
#     # 运行
#     # =========================
#
#     ctx = NodeContext()
#
#     wf.run(ctx, "detect")
#
#     # =========================
#     # 统计输出
#     # =========================
#
#     logger.info("\n=== STATS ===")
#
#     logger.info("fight_count:", ctx.shared.fight_count)
#     logger.info("node_runs:", ctx.stats.node_runs)
#     logger.info("node_time:", ctx.stats.node_time)
#     logger.info("retries:", ctx.stats.retries)
#     logger.info("total_runtime:", time.time() - ctx.runtime.start_time)
