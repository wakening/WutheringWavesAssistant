from dataclasses import dataclass
from enum import Enum
from typing import List


class Direction(Enum):
    """方向"""
    RIGHT = "right"
    LEFT = "left"
    FORWARD = "forward"
    BACKWARD = "backward"

    def get_key(self):
        if self == Direction.LEFT:
            return "a"
        elif self == Direction.RIGHT:
            return "d"
        elif self == Direction.BACKWARD:
            return "s"
        return "w"


class MoveStep:
    """移动基类"""
    pass


@dataclass
class Walk(MoveStep):
    direction: Direction
    steps: int

    @classmethod
    def right(cls, steps: int):
        return cls(Direction.RIGHT, steps)

    @classmethod
    def left(cls, steps: int):
        return cls(Direction.LEFT, steps)

    @classmethod
    def forward(cls, steps: int):
        return cls(Direction.FORWARD, steps)

    @classmethod
    def backward(cls, steps: int):
        return cls(Direction.BACKWARD, steps)


@dataclass
class Run(MoveStep):
    direction: Direction
    duration: float

    @classmethod
    def right(cls, duration: float):
        return cls(Direction.RIGHT, duration)

    @classmethod
    def left(cls, duration: float):
        return cls(Direction.LEFT, duration)

    @classmethod
    def forward(cls, duration: float):
        return cls(Direction.FORWARD, duration)

    @classmethod
    def backward(cls, duration: float):
        return cls(Direction.BACKWARD, duration)


class RouteExecutor:
    """路线执行器"""

    def __init__(self, ctx):
        self.ctx = ctx

    def execute(self, route: List[MoveStep]):
        if not route:
            return
        for step in route:
            self._dispatch(step)

    def _dispatch(self, step: MoveStep):
        if isinstance(step, Walk):
            self._walk(step)
        elif isinstance(step, Run):
            self._run(step)
        else:
            raise TypeError(f"Unsupported step type: {type(step)}")

    def _walk(self, step: Walk):
        if step.steps <= 0:
            return
        self.ctx.control_service.forward_walk(
            step.steps,
            step.direction.get_key()
        )

    def _run(self, step: Run):
        if step.duration <= 0:
            return

        self.ctx.control_service.forward_run(
            step.duration,
            step.direction.get_key()
        )
