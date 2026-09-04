import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseVerina(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁红圈
        self._concerto_energy_checker = ColorChecker.concerto_spectro()

        # 能量1 血条上方的4格能量
        self._energy1_point = [(547, 668), (548, 668), (552, 668)]
        self._energy1_color = [(114, 241, 255)]  # BGR
        self._energy1_checker = ColorChecker(self._energy1_point, self._energy1_color)

        # 能量2 血条上方的4格能量
        self._energy2_point = [(595, 668), (604, 668), (614, 668)]
        self._energy2_color = self._energy1_color
        self._energy2_checker = ColorChecker(self._energy2_point, self._energy2_color)

        # 能量3 血条上方的4格能量
        self._energy3_point = [(649, 668), (659, 668), (668, 668)]
        self._energy3_color = self._energy1_color
        self._energy3_checker = ColorChecker(self._energy3_point, self._energy3_color)

        # 能量4 血条上方的4格能量
        self._energy4_point = [(692, 668), (701, 668), (711, 668)]
        self._energy4_color = self._energy1_color
        self._energy4_checker = ColorChecker(self._energy4_point, self._energy4_color)

        # 共鸣技能
        self._resonance_skill_point = [(1089, 655)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(self._resonance_skill_point, self._resonance_skill_color)

        # 声骸技能
        self._echo_skill_point = [(1135, 652), (1156, 652)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1208, 658), (1210, 631), (1211, 631)]
        self._resonance_liberation_color = [(253, 253, 253), (219, 218, 215)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.verina

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Healer]

    def energy_count(self, img: np.ndarray) -> int:
        energy_count = 0
        if self._energy1_checker.check(img):
            energy_count = 1
        if self._energy2_checker.check(img):
            energy_count = 2
        if self._energy3_checker.check(img):
            energy_count = 3
        if self._energy4_checker.check(img):
            energy_count = 4
        logger.debug(f"{self.resonator_name().value}-能量: {energy_count}格")
        return energy_count

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready


class Verina(BaseVerina):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 普攻5a
        ["a", 0.05, 0.40],
        ["a", 0.05, 0.40],
        ["a", 0.05, 0.70],
        ["a", 0.05, 0.55],
        ["a", 0.05, 0.90],
        ["j", 0.05, 1.20],

        # (切人) aa EQ 跳aaa
        ["a", 0.05, 0.35],
        ["a", 0.05, 0.32],
        ["E", 0.05, 0.10],
        ["Q", 0.05, 0.10],
        ["j", 0.05, 0.10],
        ["a", 0.05, 0.20],
        ["a", 0.05, 0.20],
        ["a", 0.05, 1.17],
        ["j", 0.05, 1.20],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a3EQ(self):
        return [
            ["a", 0.05, 0.35],
            ["a", 0.05, 0.32],
            ["a", 0.05, 0.32],
            ["a", 0.05, 0.20],  # 多打一个a，若EQ没cd还可以出普攻
            ["E", 0.05, 0.10],
            ["Q", 0.05, 0.10],
        ]

    @combat_cache
    def ja3(self):
        return [
            ["j", 0.05, 0.10],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 1.17],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.80],
        ]

    # @combat_cache
    # def a5(self):
    #     return [
    #         # 普攻5a
    #         ["a", 0.05, 0.40],
    #         ["a", 0.05, 0.40],
    #         # ["a", 0.05, 0.70],  # 拆分长等待
    #         # ["a", 0.05, 0.55],
    #         ["a", 0.05, 0.20],
    #         ["a", 0.05, 0.20],
    #         ["a", 0.05, 0.15],
    #         ["a", 0.05, 0.25],
    #         ["a", 0.05, 0.25],
    #
    #         ["a", 0.05, 0.90],
    #     ]

    @combat_cache
    def a3(self):
        return [
            # 普攻a5的后三下
            # ["a", 0.05, 0.40],
            # ["a", 0.05, 0.40],
            # ["a", 0.05, 0.70],  # 拆分长等待
            # ["a", 0.05, 0.55],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            ["a", 0.05, 0.90],
        ]

    @combat_cache
    def R(self):
        return [
            # R
            ["R", 0.05, 2.63],
        ]

    @combat_cache
    def EQR(self):
        return [
            # EQR
            ["E", 0.05, 0.10],
            ["Q", 0.05, 0.10],
            ["R", 0.05, 2.63],
        ]

    @combat_cache
    def EQ_fast(self):
        return [
            # EQ
            ["E", 0.05, 0.05],
            ["Q", 0.00, 0.00],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):
        img = self.img_service.screenshot()
        energy_count = self.energy_count(img)
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        # is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)

        # 不管条件，入场就打aaEQ
        self.combo_action(self.a3EQ(), False)

        # 有大开大
        # if is_resonance_liberation_ready:
        #     self.combo_action(self.R(), False)
        #     time.sleep(0.05)
        #     return
        # 大招不易识别，直接按
        self.combo_action(self.R(), False)

        # 有能量就跳a
        if energy_count > 0:
            self.combo_action(self.ja3(), False)
            time.sleep(0.05)
            self.combo_action(self.EQ_fast(), False)
            return

        time.sleep(0.1)
        img = self.img_service.screenshot()
        energy_count = self.energy_count(img)
        if energy_count > 1:
            self.combo_action(self.ja3(), False)
        self.combo_action(self.EQ_fast(), False)
