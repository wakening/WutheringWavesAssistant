from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import cv2
import numpy as np

from src.core.geometry import Scaler, AnchorPoint, Point


class RuleMode(Enum):
    ANY = "any"
    ALL = "all"


class Space(Enum):
    BGR = "bgr"  # 屏幕发光值，设备依赖颜色空间
    HSV = "hsv"  # 颜色类型 + 浓度 + 亮度
    LAB = "lab"  # 人眼看到的颜色差异


@dataclass(frozen=True)
class Color:
    c1: int
    c2: int
    c3: int
    space: Space = Space.BGR

    @classmethod
    def bgr(cls, *args: int):
        """
        bgr
        :param args: 示例：Color.bgr(255, 255, 255) or Color.bgr((255, 255, 255), (111, 111, 111))
        :return:
        """
        if len(args) == 3 and all(isinstance(x, int) for x in args):
            return cls(*args, Space.BGR)
        return [cls(*c, Space.BGR) for c in args]

    @classmethod
    def hsv(cls, *args: int):
        if len(args) == 3 and all(isinstance(x, int) for x in args):
            return cls(*args, Space.HSV)
        return [cls(*c, Space.HSV) for c in args]

    @classmethod
    def lab(cls, *args: int):
        if len(args) == 3 and all(isinstance(x, int) for x in args):
            return cls(*args, Space.LAB)
        return [cls(*c, Space.LAB) for c in args]


class ColorRule:
    def __init__(self):
        self._points: Sequence[AnchorPoint | Point] | Sequence[tuple[int, int]] = []
        self._groups = []  # (compiled_colors, mode)

    def points(self, pts):
        self._points = pts if isinstance(pts, Sequence) else [pts]
        return self

    def colors(
            self, colors: Color | list[Color],
            tol: int | tuple[Optional[int], Optional[int], Optional[int]] = 30,
            mode: RuleMode = RuleMode.ANY,
    ):
        if isinstance(colors, Color):
            colors = [colors]

        if isinstance(tol, int):
            tol = (tol, tol, tol)
        elif isinstance(tol, tuple) and len(tol) == 3 and all(isinstance(t, int) or t is None for t in tol):
            pass
        else:
            raise ValueError("tol must be an int or a tuple of 3 Optional[int] values.")

        compiled = []

        for c in colors:
            compiled.append((
                c.space,
                np.array([c.c1, c.c2, c.c3], dtype=np.int16),
                tol
            ))

        self._groups.append((compiled, mode))
        return self

    @staticmethod
    def _match_vec(px, target, tol):
        for i in range(3):
            t = tol[i]
            if t is None:
                continue
            if abs(px[i] - target[i]) > t:
                return False
        return True

    def _match_pixel(self, pixel, compiled):
        px = pixel.astype(np.int16)

        hsv = None
        lab = None

        for space, target, tol in compiled:
            if space == Space.BGR:
                if self._match_vec(px, target, tol):
                    return True

            elif space == Space.HSV:
                if hsv is None:
                    hsv = cv2.cvtColor(
                        np.array([[pixel]], np.uint8),
                        cv2.COLOR_BGR2HSV
                    )[0, 0].astype(np.int16)

                # hue 特殊处理
                if tol[0] is None:
                    h_ok = True
                else:
                    hd = abs(hsv[0] - target[0])
                    h_ok = min(hd, 180 - hd) <= tol[0]

                if (
                        h_ok
                        and (tol[1] is None or abs(hsv[1] - target[1]) <= tol[1])
                        and (tol[2] is None or abs(hsv[2] - target[2]) <= tol[2])
                ):
                    return True

            elif space == Space.LAB:
                if lab is None:
                    lab = cv2.cvtColor(
                        np.array([[pixel]], np.uint8),
                        cv2.COLOR_BGR2LAB
                    )[0, 0].astype(np.int16)

                if self._match_vec(lab, target, tol):
                    return True

        return False

    def _check_group(self, img, compiled, mode, scaler):
        h, w = img.shape[:2]

        def valid(pts):
            if isinstance(pts, AnchorPoint):
                if not scaler:
                    raise ValueError("Scaler cannot be None")
                pts = scaler.as_point(pts)
            x, y = pts
            return 0 <= x < w and 0 <= y < h and self._match_pixel(img[y, x], compiled)

        if mode == RuleMode.ANY:
            return any(valid(p) for p in self._points)
        elif mode == RuleMode.ALL:
            return all(valid(p) for p in self._points)
        raise ValueError(f"Unsupported Mode: {mode}")

    def match(self, img, scaler: Scaler = None):
        for compiled, mode in self._groups:
            if self._check_group(img, compiled, mode, scaler):
                continue
            return False
        return True


class ColorMatch:
    def __init__(self, scaler: Scaler = None):
        self._rules: list[ColorRule] = []
        self._scaler = scaler  # 支持动态缩放

    def rules(self, *rules: ColorRule):
        for r in rules:
            self._rules.append(r)
        return self

    def match(self, img: np.ndarray, scaler: Scaler = None, rules: ColorRule | list[ColorRule] = None) -> bool:
        if not rules:
            rules = self._rules
        elif isinstance(rules, ColorRule):
            rules = [rules]
        if not scaler:
            scaler = self._scaler
        return all(r.match(img, scaler) for r in rules)



