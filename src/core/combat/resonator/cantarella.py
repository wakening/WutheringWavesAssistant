import logging
import random
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, LogicEnum, \
    Morph, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseCantarella(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁紫圈
        self._concerto_energy_checker = ColorChecker.concerto_havoc()

        # # 能量1 血条上方的4格能量
        # self._energy1_point = [(547, 668), (548, 668), (552, 668)]
        # self._energy1_color = [(107, 97, 250)]  # BGR
        # self._energy1_checker = ColorChecker(self._energy1_point, self._energy1_color)
        #
        # # 能量2 血条上方的4格能量
        # self._energy2_point = [(595, 668), (604, 668), (614, 668)]
        # self._energy2_color = self._energy1_color
        # self._energy2_checker = ColorChecker(self._energy2_point, self._energy2_color)
        #
        # # 能量3 血条上方的4格能量
        # self._energy3_point = [(649, 668), (659, 668), (668, 668)]
        # self._energy3_color = self._energy1_color
        # self._energy3_checker = ColorChecker(self._energy3_point, self._energy3_color)
        #
        # # 能量4 血条上方的4格能量
        # self._energy4_point = [(692, 668), (701, 668), (711, 668)]
        # self._energy4_color = self._energy1_color
        # self._energy4_checker = ColorChecker(self._energy4_point, self._energy4_color)
        #
        # # 共鸣技能
        # self._resonance_skill_point = [(1071, 634), (1093, 631), (1082, 662)]
        # self._resonance_skill_color = [(255, 255, 255)]  # BGR
        # self._resonance_skill_checker = ColorChecker(self._resonance_skill_point, self._resonance_skill_color)
        #
        # # 声骸技能
        # self._echo_skill_point = [(1146, 632), (1141, 652), (1160, 656)]
        # self._echo_skill_color = [(255, 255, 255)]  # BGR
        # self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)
        #
        # # 共鸣解放
        # self._resonance_liberation_point = [(1207, 653), (1213, 652)]
        # self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        # self._resonance_liberation_checker = ColorChecker(
        #     self._resonance_liberation_point, self._resonance_liberation_color)


    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.cantarella

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Support]

    # def energy_count(self, img: np.ndarray) -> int:
    #     energy_count = 0
    #     if self._energy1_checker.check(img):
    #         energy_count = 1
    #     if self._energy2_checker.check(img):
    #         energy_count = 2
    #     if self._energy3_checker.check(img):
    #         energy_count = 3
    #     if self._energy4_checker.check(img):
    #         energy_count = 4
    #     logger.debug(f"{self.resonator_name().value}-能量: {energy_count}格")
    #     return energy_count
    #
    # def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
    #     is_ready = self._concerto_energy_checker.check(img)
    #     logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
    #     return is_ready
    #
    # def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
    #     is_ready = self._resonance_skill_checker.check(img)
    #     logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}")
    #     return is_ready
    #
    # def is_echo_skill_ready(self, img: np.ndarray) -> bool:
    #     is_ready = self._echo_skill_checker.check(img)
    #     logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
    #     return is_ready
    #
    # def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
    #     is_ready = self._resonance_liberation_checker.check(img)
    #     logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
    #     return is_ready


class Cantarella(BaseCantarella):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    COMBO_SEQ = [
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],

        ["z", 0.50, 0.50],
        ["R", 0.05, 0.50],
        ["Q", 0.05, 0.50],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a2(self):
        return [
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def a3(self):
        return [
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def a4(self):
        return [
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def Eaa(self):
        return [
            ["E", 0.05, 0.50],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def E(self):
        return [
            # 共鸣技能 E
            ["E", 0.05, 0.50],
        ]

    @combat_cache
    def z(self):
        return [
            ["z", 0.50, 0.50],
        ]

    @combat_cache
    def Q(self):
        return [
            ["Q", 0.05, 0.50],
        ]

    @combat_cache
    def R(self):
        return [
            ["R", 0.05, 0.50],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):
        self.combo_action(self.a3(), True)
        self.combo_action(self.R(), False)
        if self.random_float() < 0.66:
            self.combo_action(self.z(), True)
            if self.random_float() < 0.66:
                self.combo_action(self.z(), False)
            self.combo_action(self.E(), False)
            if self.random_float() < 0.66:
                self.combo_action(self.a3(), True)
            else:
                self.combo_action(self.a4(), True)
        else:
            self.combo_action(self.a3(), True)
        self.combo_action(self.E(), False)
        self.combo_action(self.Q(), False)
