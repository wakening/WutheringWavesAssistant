import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, combat_cache, \
    LogicEnum
from src.core.interface import ControlService, ImgService
from src.core.regions import AlignEnum

logger = logging.getLogger(__name__)


class BaseLucilla(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏
        self._concerto_energy_checker = ColorChecker.concerto_glacio()

        # 照片1
        self._photo_color = [(253, 237, 208)]  # BGR
        self._photo1_checker = ColorChecker(
            [(572, 659), (576, 657), (582, 654)], self._photo_color, logic=LogicEnum.AND)
        # 照片2
        self._photo2_checker = ColorChecker(
            [(627, 653), (634, 653), (640, 653)], self._photo_color, logic=LogicEnum.AND)
        # 照片3
        self._photo3_checker = ColorChecker(
            [(687, 654), (693, 657), (697, 659)], self._photo_color, logic=LogicEnum.AND)

        # 追忆状态
        self._reminiscence_checker = ColorChecker(
            [(603, 669), (664, 669)], [(201, 255, 255), (158, 225, 241)], logic=LogicEnum.AND)

        # 普攻·溯念留形
        self._basic_attack_tracing_forms_checker = ColorChecker(
            [(1072, 658), (1091, 633)], [(255, 255, 255)], logic=LogicEnum.AND)

        # 断舍离
        self._letting_it_go_checker = ColorChecker(
            [(1080, 642), (1082, 641), (1081, 643), (1083, 643)], [(255, 255, 255)], logic=LogicEnum.AND)

        # 共鸣技能
        self._resonance_skill_point = [(1074, 654), (1088, 655), (1090, 654)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(
            self._resonance_skill_point, self._resonance_skill_color, logic=LogicEnum.AND)

        # 共鸣解放
        self._resonance_liberation_point = [(1196, 631), (1206, 626), (1205, 628)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color, logic=LogicEnum.AND)


    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.lucilla

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Support]

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}", stacklevel=2)
        return is_ready

    def photo(self, img: np.ndarray) -> int:
        photo = 0
        if self._photo1_checker.check(img):
            photo = 1
        if self._photo2_checker.check(img):
            photo = 2
        if self._photo3_checker.check(img):
            photo = 3
        logger.debug(f"{self.resonator_name().value}-照片: {photo}", stacklevel=2)
        return photo

    def is_reminiscence(self, img: np.ndarray) -> int:
        is_ready = self._reminiscence_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-追忆状态: {is_ready}", stacklevel=2)
        return is_ready

    def is_basic_attack_tracing_forms_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_tracing_forms_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·溯念留形: {is_ready}", stacklevel=2)
        return is_ready

    def is_letting_it_go_ready(self, img: np.ndarray) -> bool:
        is_ready = self._letting_it_go_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-断舍离: {is_ready}", stacklevel=2)
        return is_ready

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}", stacklevel=2)
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}", stacklevel=2)
        return is_ready


class Lucilla(BaseLucilla):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        ["a", 0.05, 0.36],
        ["a", 0.05, 0.51],
        ["a", 0.05, 0.74],
        ["j", 0.05, 1.50],

        ["E", 1.86, 0.85],
        ["j", 0.05, 1.50],

        ["z", 2.81, 0.55],
        ["j", 0.05, 1.50],

        ["z", 2.81, 0.55],
        ["j", 0.05, 1.50],

        ["R", 0.05, 4.50],
        ["j", 0.05, 1.50],

        ["z", 4.35, 0.72],
        ["j", 0.05, 1.50],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a3(self):
        return [
            ["a", 0.05, 0.36],
            # ["a", 0.05, 0.51],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.21],
            # ["a", 0.05, 0.74],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.24],
        ]

    @combat_cache
    def a2(self):
        return [
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
        ]

    @combat_cache
    def a(self):
        return [
            # ["a", 0.05, 0.36],
            # # ["a", 0.05, 0.51],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.21],
            # ["a", 0.05, 0.74],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.24],
        ]

    @combat_cache
    def z(self):
        return [
            # ["z", 2.81, 0.55],
            ["a_down", 0.00, 0.00],
            ["w", 0.00, 1.00],
            ["w", 0.00, 1.00],
            ["w", 0.00, 1.10],
            ["a_up", 0.00, 0.26],
        ]

    @combat_cache
    def z_reminiscence(self):
        return [
            # ["z", 4.35, 0.72],
            ["a_down", 0.00, 0.00],
            ["w", 0.00, 1.00],
            ["w", 0.00, 1.00],
            ["w", 0.00, 1.00],
            ["Q", 0.00, 1.00],
            ["w", 0.00, 1.00],
            ["w", 0.00, 0.70],
            ["a_up", 0.00, 0.37],
        ]

    @combat_cache
    def Ea(self):
        return [
            # ["E", 1.86, 0.85],
            ["E_down", 0.00, 0.05],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.20],
            ["E_up", 0.00, 0.05],
            ["a", 0.05, 0.21],
        ]

    @combat_cache
    def Q(self):
        return [
            ["Q", 0.00, 0.05],
        ]

    @combat_cache
    def Ra(self):
        return [
            # ["R", 0.05, 4.50],
            ["R", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def ER(self):
        return [
            ["E", 0.05, 0.10],
            ["R", 0.05, 0.10],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):
        self.combo_action(self.a2(), False)

        img = self.img_service.screenshot()
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        photo = self.photo(img)
        # is_reminiscence = self.is_reminiscence(img)
        is_basic_attack_tracing_forms_ready = self.is_basic_attack_tracing_forms_ready(img)
        is_letting_it_go_ready = self.is_letting_it_go_ready(img)
        is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)

        if is_resonance_liberation_ready:
            self.combo_action(self.Ra(), True)
            self.combo_action(self.z_reminiscence(), True)
            self.combo_action(self.Q(), False)
            return
        if is_resonance_skill_ready:
            self.combo_action(self.Ea(), True)
            if photo < 2:
                self.combo_action(self.Q(), False)
                return
        elif is_basic_attack_tracing_forms_ready or is_letting_it_go_ready:
            self.combo_action(self.z_reminiscence(), False)
        else:
            if photo < 2:
                self.combo_action(self.a(), True)
                self.combo_action(self.Q(), False)
                return
            elif photo == 2:
                if self.random_float() > 0.4:
                    self.combo_action(self.a(), True)
                    self.combo_action(self.Q(), False)
                    return
                self.combo_action(self.z(), True)
                img = self.img_service.screenshot()
                is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
                if not is_resonance_liberation_ready:
                    return
        for i in range(2):
            if not is_resonance_liberation_ready:
                img = self.img_service.screenshot()
                is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
            if is_resonance_liberation_ready:
                self.combo_action(self.Ra(), True)
                self.combo_action(self.z_reminiscence(), True)
                self.combo_action(self.Q(), False)
                return
            time.sleep(0.2)

        self.combo_action(self.Q(), False)