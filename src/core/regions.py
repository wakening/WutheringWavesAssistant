import logging
from abc import ABC, abstractmethod
from typing import Tuple, Sequence, TypeVar, Type

import numpy as np
from pydantic import BaseModel, Field
from rapidocr.utils import RapidOCROutput

logger = logging.getLogger(__name__)

Pos = TypeVar('Pos', bound='Position')


class Position(BaseModel):
    """目标矩形框坐标，如文本框"""

    x1: int = Field(..., title="x1")
    y1: int = Field(..., title="y1")
    x2: int = Field(..., title="x2")
    y2: int = Field(..., title="y2")
    confidence: float = Field(0, title="识别置信度")

    def __str__(self):
        return self.model_dump_json()
        # return f"({self.x1}, {self.y1}, {self.x2}, {self.y2}, {int(self.confidence * 10000) / 10000})"

    @property
    def center(self, x_range: int = 3, y_range: int = 3) -> Tuple[int, int]:
        """中心坐标周围3格内随机"""
        middle_x = int((self.x1 + self.x2) / 2)
        middle_y = int((self.y1 + self.y2 + 2 * y_range) / 2)
        return self.point_random(middle_x, middle_y, x_range, y_range)

    @property
    def random(self) -> Tuple[int, int]:
        """当前矩形范围内随机"""
        x = int(np.random.uniform(self.x1, self.x2))
        y = int(np.random.uniform(self.y1, self.y2))
        return x, y

    @staticmethod
    def point_random(x: int, y: int, x_range: int = 3, y_range: int = 3) -> Tuple[int, int]:
        """指定的坐标周围3格内随机"""
        random_x = x + int(np.random.uniform(-x_range, x_range))
        random_y = y + int(np.random.uniform(-y_range, y_range))
        return random_x, random_y

    @classmethod
    def build(cls: Type[Pos], x1: int, y1: int, x2: int, y2: int, **kwargs) -> Pos:
        return cls(x1=x1, y1=y1, x2=x2, y2=y2, confidence=kwargs.get("confidence", 0.0))

    @classmethod
    def of(cls: Type[Pos], position: "Position") -> Pos | None:
        if position is None:
            return None
        if not isinstance(position, cls):
            raise TypeError("不是TextPosition类或子类")
        return position

    @classmethod
    def get(cls: Type[Pos], positions: dict[str, "Position"], key: str) -> Pos:
        return cls.of(positions.get(key))


class DynamicPosition(BaseModel):
    rate: tuple[float, float, float, float] | None = Field(
        None, title="百分比矩形区域，16:9", description="左上右下两点")

    def to_position(self, height: int, width: int) -> Position:
        """百分比区域转成实际像素位置"""
        return Position.build(
            *self.to_tuple(height, width)
        )

    def to_tuple(self, height: int, width: int) -> tuple[int, int, int, int]:
        return (
            int(width * self.rate[0]),
            int(height * self.rate[1]),
            int(width * self.rate[2]),
            int(height * self.rate[3]),
        )


class TextPosition(Position, ABC):
    text: str = Field(..., title="文本")

    def __eq__(self, other):
        if isinstance(other, TextPosition):
            return (self.x1 == other.x1
                    and self.y1 == other.y1
                    and self.x2 == other.x2
                    and self.y2 == other.y2
                    # and self.confidence == other.confidence
                    and self.text == other.text)
        return False

    def __str__(self):
        return self.model_dump_json()

    @classmethod
    def build(cls: Type[Pos], x1: int, y1: int, x2: int, y2: int, **kwargs) -> Pos:
        return cls(x1=x1, y1=y1, x2=x2, y2=y2, confidence=kwargs.get("confidence", 0.0), text=kwargs.get("text"))

    @classmethod
    @abstractmethod
    def format(cls: Type[Pos], **kwargs) -> list[Pos]:
        pass


class PaddleocrPosition(TextPosition):

    @classmethod
    def format(cls: Type[Pos], output: Sequence) -> list[Pos]:
        results = output[0]
        _positions = []
        if not results:
            return _positions
        for result in results:
            text = result[1][0]
            pos = result[0]
            x1, y1, x2, y2 = pos[0][0], pos[0][1], pos[2][0], pos[2][1]
            confidence = result[1][1]
            _position = cls.build(x1=x1, y1=y1, x2=x2, y2=y2, confidence=confidence, text=text)
            _positions.append(_position)
        return _positions


class RapidocrPosition(TextPosition):

    @classmethod
    def format(cls: Type[Pos], output: RapidOCROutput) -> list[Pos]:
        boxes, scores, texts = output.boxes, output.scores, output.txts
        _positions = []
        if boxes is None or len(boxes) == 0:
            return _positions
        for i in range(len(boxes)):
            box, score, text = boxes[i], scores[i], texts[i]
            _position = cls.build(x1=int(box[0][0]), y1=int(box[0][1]), x2=int(box[2][0]), y2=int(box[2][1]),
                                  confidence=score, text=text)
            _positions.append(_position)
        return _positions
