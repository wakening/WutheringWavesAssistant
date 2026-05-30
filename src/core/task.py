import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Set, Dict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StatusMeta:
    """状态元数据（不可变）"""
    display_name: str  # 显示名称
    description: str  # 描述
    priority: int  # 优先级（数值越小越优先）
    color: str  # UI 颜色
    icon: str  # 图标名称
    can_transition_from: Set[str]  # 可以从哪些状态转换过来
    is_terminal: bool  # 是否为终态（完成/失败等）
    is_active: bool  # 是否为活跃状态
    weight: int = 1  # 权重（用于统计）


class TaskStatus(Enum):
    """
    任务状态枚举

    包含完整的状态元数据、状态转换规则、便捷方法
    """

    # ========== 状态定义 ==========
    # 格式: (显示名, 描述, 优先级, 颜色, 图标, 可转换来源, 是否终态, 是否活跃)

    NOT_REQUIRED = (
        "不需要做", "任务无需执行，已跳过",
        0, "gray", "⏭️", {"PENDING", "NOT_REQUIRED"},
        True, False
    )

    PENDING = (
        "待处理", "任务已创建，等待执行",
        1, "orange", "⏳", {"NOT_REQUIRED", "PENDING"},
        False, True
    )

    IN_PROGRESS = (
        "进行中", "任务正在执行",
        2, "blue", "🔄", {"PENDING"},
        False, True
    )

    WAITING = (
        "等待中", "任务等待外部条件",
        3, "purple", "⏸️", {"IN_PROGRESS"},
        False, True
    )

    FAILED = (
        "失败", "任务执行失败",
        4, "red", "❌", {"IN_PROGRESS", "WAITING"},
        True, False
    )

    COMPLETED = (
        "已完成", "任务成功完成",
        5, "green", "✅", {"IN_PROGRESS", "WAITING"},
        True, False
    )

    CANCELLED = (
        "已取消", "任务被取消",
        6, "gray", "🚫", {"PENDING", "IN_PROGRESS", "WAITING"},
        True, False
    )

    # ========== 初始化 ==========
    def __init__(self, display_name: str, description: str, priority: int,
                 color: str, icon: str, can_transition_from: Set[str],
                 is_terminal: bool, is_active: bool):
        self._meta = StatusMeta(
            display_name=display_name,
            description=description,
            priority=priority,
            color=color,
            icon=icon,
            can_transition_from=can_transition_from,
            is_terminal=is_terminal,
            is_active=is_active
        )

    # ========== 属性访问 ==========
    @property
    def display_name(self) -> str:
        return self._meta.display_name

    @property
    def description(self) -> str:
        return self._meta.description

    @property
    def priority(self) -> int:
        return self._meta.priority

    @property
    def color(self) -> str:
        return self._meta.color

    @property
    def icon(self) -> str:
        return self._meta.icon

    @property
    def is_terminal(self) -> bool:
        """是否为终态（已完成/失败/取消/不需要做）"""
        return self._meta.is_terminal

    @property
    def is_active(self) -> bool:
        """是否为活跃状态（待处理/进行中/等待中）"""
        return self._meta.is_active

    @property
    def is_finished(self) -> bool:
        """是否成功完成"""
        return self == TaskStatus.COMPLETED or self == TaskStatus.NOT_REQUIRED

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self == TaskStatus.FAILED

    @property
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self in (TaskStatus.FAILED, TaskStatus.CANCELLED)

    # ========== 状态转换 ==========
    def can_transition_to(self, target: 'TaskStatus') -> bool:
        """检查是否可以转换到目标状态"""
        return self.name in target._meta.can_transition_from

    def transition_to(self, target: 'TaskStatus', task_id: Optional[str] = None) -> 'TaskStatus':
        """
        转换到目标状态（带验证）

        Args:
            target: 目标状态
            task_id: 任务ID（用于日志）

        Returns:
            目标状态

        Raises:
            ValueError: 如果转换不合法
        """
        if not self.can_transition_to(target):
            allowed = ", ".join(target._meta.can_transition_from)
            task_info = f" [task={task_id}]" if task_id else ""
            raise ValueError(
                f"Invalid state transition{task_info}: "
                f"'{self.name}' -> '{target.name}'. "
                f"'{target.name}' only allows transitions from: {allowed}"
            )
        return target

    # ========== 类方法 ==========
    @classmethod
    # @lru_cache(maxsize=128)
    def from_name(cls, name: str) -> Optional['TaskStatus']:
        """根据名称获取状态（带缓存）"""
        try:
            return cls[name]
        except KeyError:
            return None

    @classmethod
    def get_active_statuses(cls) -> List['TaskStatus']:
        """获取所有活跃状态"""
        return [s for s in cls if s.is_active]

    @classmethod
    def get_terminal_statuses(cls) -> List['TaskStatus']:
        """获取所有终态"""
        return [s for s in cls if s.is_terminal]

    @classmethod
    def get_by_priority(cls, ascending: bool = True) -> List['TaskStatus']:
        """按优先级排序获取所有状态"""
        return sorted(cls, key=lambda s: s.priority, reverse=not ascending)

    @classmethod
    def get_transition_graph(cls) -> Dict[str, List[str]]:
        """获取完整的状态转换图"""
        graph = {}
        for target in cls:
            sources = list(target._meta.can_transition_from)
            graph[target.name] = sources
        return graph

    # ========== 特殊方法 ==========
    def __str__(self) -> str:
        return f"{self.icon} {self.display_name}"

    def __repr__(self) -> str:
        return f"<TaskStatus.{self.name}: {self.display_name}>"


class FSM(ABC):
    """状态接口"""

    @abstractmethod
    def set_enabled(self, enabled: bool):
        pass

    @abstractmethod
    def is_terminal(self) -> bool:
        pass

    @abstractmethod
    def is_active(self) -> bool:
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        pass

    @abstractmethod
    def is_failed(self) -> bool:
        pass

    def utility(self, ctx):
        # score = self.BASE_SCORE
        #
        # score += self.stamina_weight(ctx)
        # score += self.deadline_weight(ctx)
        # score += self.material_weight(ctx)
        #
        # return score
        pass


class TaskFSM(FSM):
    """任务状态机"""

    def __init__(
            self,
            name: str | None = None,
            task_id: str | None = None,
            status: TaskStatus = TaskStatus.PENDING,
    ):
        self.name = name
        self.task_id = task_id
        self.status = status
        self.history: List[TaskStatus] = [self.status]

    # ------- 状态切换 -------

    def transition(self, new_status: TaskStatus):
        """安全地转换状态"""
        if self.task_id:
            task_id = f"[{self.task_id}] "
        else:
            task_id = ""
        try:
            self.status = self.status.transition_to(new_status, self.task_id)
            self.history.append(self.status)
            # logger.info(f"[{self.task_id}] {self.name}: {self.status}")

            logger.info(f"{task_id}{self.name}: {self.status}")
        except ValueError as e:
            logger.error(f"{task_id}{self.name}: 转换失败")
            raise e

    def start(self):
        self.transition(TaskStatus.IN_PROGRESS)

    def wait(self):
        self.transition(TaskStatus.WAITING)

    def complete(self):
        self.transition(TaskStatus.COMPLETED)

    def fail(self):
        self.transition(TaskStatus.FAILED)

    def cancel(self):
        self.transition(TaskStatus.CANCELLED)

    def retry(self):
        """重试失败的任务"""
        if self.status.can_retry:
            self.transition(TaskStatus.PENDING)
        else:
            logger.info(f"无法重试: 当前状态 {self.status.name}")

    def __str__(self) -> str:
        return f"TaskFSM(name='{self.name}', status={self.status})"

    # ------- 状态 -------

    def set_enabled(self, enabled: bool):
        if enabled:
            self.status = TaskStatus.PENDING
        else:
            self.status = TaskStatus.NOT_REQUIRED

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    @property
    def is_active(self) -> bool:
        return self.status.is_active

    @property
    def is_finished(self) -> bool:
        return self.status.is_finished

    @property
    def is_failed(self) -> bool:
        return self.status.is_failed


class TaskFSMGroup(FSM):

    def __init__(
            self,
            *children: FSM,
            name: str | None = None,
            enabled: bool = True,
    ):
        """
        组合模式
        自身的状态仅用于启动前设置任务是否需要执行，是一个开关，不参与运行时状态变化和判断任务是否完成，
        任务的完成情况根据FSM接口的函数判断
        :param children: 子状态机
        :param name: 仅调试用，无实际作用
        :param enabled: 自身状态，开关，控制当前任务树是否需要运行
        :param parent: 父节点
        """
        self.children = list(children)
        self.name = name
        self.enabled = enabled

    def __str__(self) -> str:
        return f"TaskFSMGroup(name='{self.name}', enabled={self.enabled}, children={[child.name for child in self.children]})"

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    @property
    def is_terminal(self) -> bool:
        if not self.enabled:
            return True
        # return all(child.is_terminal for child in self.children)
        for child in self.children:
            if not child.is_terminal:
                logger.debug(f"❌ {self.name}.is_terminal=False")
                logger.debug(f"   └─ 因为 {child.name}.is_terminal=False")
                return False
        return True

    @property
    def is_active(self) -> bool:
        if not self.enabled:
            return False
        # return any(child.is_active for child in self.children)
        for child in self.children:
            if child.is_active:
                return True

        logger.debug(f"❌ {self.name}.is_active=False")
        logger.debug(f"   └─ 子节点都不活跃: {[c.name for c in self.children]}")
        return False

    @property
    def is_finished(self) -> bool:
        if not self.enabled:
            return True
        # return all(child.is_finished for child in self.children)
        for child in self.children:
            if not child.is_finished:
                logger.debug(f"❌ {self.name}.is_finished=False")
                logger.debug(f"   └─ 因为 {child.name}.is_finished=False")
                return False
        return True

    @property
    def is_failed(self) -> bool:
        if not self.enabled:
            return False
        # return any(child.is_failed for child in self.children)
        for child in self.children:
            if child.is_failed:
                logger.debug(f"✅ {self.name}.is_failed=True")
                logger.debug(f"   └─ 因为 {child.name}.is_failed=True")
                return True
        return False


# ========== 使用示例 ==========
def demo():
    """任务状态管理示例"""

    # 1. 基础属性访问
    status = TaskStatus.IN_PROGRESS
    logger.info(f"状态: {status}")
    logger.info(f"描述: {status.description}")
    logger.info(f"优先级: {status.priority}")
    logger.info(f"颜色: {status.color}")
    logger.info(f"是否活跃: {status.is_active}")
    logger.info(f"是否终态: {status.is_terminal}")
    logger.info("\n")

    # 2. 状态转换验证
    current = TaskStatus.PENDING
    logger.info(f"当前状态: {current}")

    # 合法转换
    try:
        next_status = current.transition_to(TaskStatus.IN_PROGRESS)
        logger.info(f"✅ 转换成功: {current.name} -> {next_status.name}")
    except ValueError as e:
        logger.error(f"❌ {e}")

    # 非法转换
    try:
        current.transition_to(TaskStatus.COMPLETED)  # PENDING 不能直接到 COMPLETED
    except ValueError as e:
        logger.error(f"❌ 非法转换: {e}")
    logger.info("\n")

    # 3. 任务状态机（完整示例）

    # 创建任务并演示完整流程
    task = TaskFSM("TacetDiscordNest", "task_001")
    task.start()  # PENDING -> IN_PROGRESS
    task.complete()  # IN_PROGRESS -> COMPLETED
    logger.info("\n")

    # 失败重试流程
    task2 = TaskFSM("ForgeryChallenge", "task_002")
    task2.start()
    task2.fail()  # IN_PROGRESS -> FAILED
    task2.retry()  # FAILED -> PENDING
    task2.start()
    task2.complete()
    logger.info("\n")

    # 4. 获取状态图的某个部分
    logger.info("=== 状态转换图（部分） ===")
    graph = TaskStatus.get_transition_graph()
    for target, sources in list(graph.items())[:3]:  # 只展示前3个
        logger.info(f"'{target}' 可以从: {sources}")
    logger.info("\n")

    # 5. 统计和过滤
    logger.info(f"活跃状态: {[s.display_name for s in TaskStatus.get_active_statuses()]}")
    logger.info(f"终态: {[s.display_name for s in TaskStatus.get_terminal_statuses()]}")
    logger.info(f"按优先级排序: {[s.display_name for s in TaskStatus.get_by_priority()]}")


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(message)s',  # 只输出消息内容，不加时间戳等
        handlers=[
            logging.StreamHandler(sys.stdout)  # 输出到 stdout/stderr
        ]
    )

    demo()
