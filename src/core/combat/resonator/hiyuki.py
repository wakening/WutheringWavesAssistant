import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, combat_cache, \
    LogicEnum
from src.core.geometry import Align
from src.core.interface import ControlService, ImgService
from src.core.regions import AlignEnum

logger = logging.getLogger(__name__)


class BaseHiyuki(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏
        self._concerto_energy_checker = ColorChecker.concerto_glacio()

        # 常世身

        # 心念100
        self._dedication_color = [(240, 212, 143), (255, 255, 255)]  # BGR
        self._dedication100_checker = ColorChecker(
            [(550, 662), (559, 662), (586, 662)], self._dedication_color)
        # 心念200
        self._dedication200_checker = ColorChecker(
            [(618, 662), (640, 662), (649, 662)], self._dedication_color)
        # 心念300
        self._dedication300_checker = ColorChecker(
            [(694, 662), (703, 662), (721, 662)], self._dedication_color)

        # 普攻·常世身
        self._basic_attack_present_self_checker = ColorChecker(
            [(940, 630), (945, 635), (953, 644), (959, 650)],
            [(255, 255, 255)],  # BGR
            logic=LogicEnum.AND
        )

        # 重击·寒簇·常世身 心念300解锁
        self._heavy_attack_frost_splinter_present_self_checker = ColorChecker(
            [(952, 616), (955, 616), (954, 618)],
            [(255, 249, 170)],  # BGR
            logic=LogicEnum.AND
        )

        # 共鸣技能·常世身
        self._resonance_skill_present_self_point = [(1068, 652), (1072, 656), (1083, 659)]
        self._resonance_skill_present_self_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_present_self_checker = ColorChecker(
            self._resonance_skill_present_self_point, self._resonance_skill_present_self_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1141, 651), (1150, 651)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放 预求我身·见心 释放【重击·寒簇·常世身】后解锁
        self._foreclaiming_inward_vision_point = [(1213, 662), (1217, 660)]
        self._foreclaiming_inward_vision_color = [(255, 255, 255)]  # BGR
        self._foreclaiming_inward_vision_checker = ColorChecker(
            self._foreclaiming_inward_vision_point, self._foreclaiming_inward_vision_color, logic=LogicEnum.AND)

        # 预求身

        # 普攻·预求身
        self._basic_attack_foreclaimed_self_checker = ColorChecker(
            [(876, 630), (880, 634), (890, 644), (895, 650)],
            [(255, 255, 255)],  # BGR
            logic=LogicEnum.AND
        )

        # 寒意100
        self._frostheart_color = [(230, 45, 71), (232, 60, 84), (230, 153, 150), (227, 141, 137)]  # BGR
        self._frostheart100_checker = ColorChecker(
            [(560, 659), (563, 659), (563, 661)], self._frostheart_color, logic=LogicEnum.AND)
        # 寒意200
        self._frostheart200_checker = ColorChecker(
            [(633, 661), (635, 661), (636, 662)], self._frostheart_color, logic=LogicEnum.AND)
        # 寒意300
        self._frostheart300_checker = ColorChecker(
            [(704, 660), (706, 660), (708, 661)], self._frostheart_color, logic=LogicEnum.AND)

        # 重击·枯霜·预求身
        self._heavy_attack_bitterfrost_foreclaimed_self_checker = ColorChecker(
            [(879, 659), (876, 656), (886, 662)],
            [(255, 255, 255)],  # BGR
            logic=LogicEnum.AND
        )

        # 共鸣技能·预求身
        self._resonance_skill_foreclaimed_self_point = [(1063, 637), (1072, 656), (1083, 656)]
        self._resonance_skill_foreclaimed_self_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_foreclaimed_self_checker = ColorChecker(
            self._resonance_skill_foreclaimed_self_point, self._resonance_skill_foreclaimed_self_color,
            logic=LogicEnum.AND)

        # 共鸣解放 预求我身·归刃
        self._foreclaiming_blade_liberation_point = [(1202, 639), (1216, 633), (1211, 654), (1221, 643)]
        self._foreclaiming_blade_liberation_color = [(255, 255, 255)]  # BGR
        self._foreclaiming_blade_liberation_checker = ColorChecker(
            self._foreclaiming_blade_liberation_point, self._foreclaiming_blade_liberation_color)

        # 血量1/4
        self._hp_1_4_point = [(586, 690)]
        self._hp_1_4_color = [(240, 240, 240)]  # BGR
        self._hp_1_4_checker = ColorChecker(self._hp_1_4_point, self._hp_1_4_color, align=AlignEnum.BUTTON_CENTER)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.hiyuki

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def dedication(self, img: np.ndarray) -> int:
        dedication = 0
        if self._dedication100_checker.check(img):
            dedication = 100
        if self._dedication200_checker.check(img):
            dedication = 200
        if self._dedication300_checker.check(img):
            dedication = 300
        logger.debug(f"{self.resonator_name().value}-心念: {dedication}")
        return dedication

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_basic_attack_present_self_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_present_self_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·常世身: {is_ready}")
        return is_ready

    def is_heavy_attack_frost_splinter_present_self_ready(self, img: np.ndarray) -> bool:
        is_ready = self._heavy_attack_frost_splinter_present_self_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-重击·寒簇·常世身: {is_ready}")
        return is_ready

    def is_resonance_skill_present_self_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_present_self_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能·常世身: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_foreclaiming_inward_vision_ready(self, img: np.ndarray) -> bool:
        is_ready = self._foreclaiming_inward_vision_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放 预求我身·见心: {is_ready}")
        return is_ready

    def is_basic_attack_foreclaimed_self_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_foreclaimed_self_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·预求身: {is_ready}")
        return is_ready

    def frostheart(self, img: np.ndarray) -> int:
        frostheart = 0
        if self._frostheart100_checker.check(img):
            frostheart = 100
        if self._frostheart200_checker.check(img):
            frostheart = 200
        if self._frostheart300_checker.check(img):
            frostheart = 300
        logger.debug(f"{self.resonator_name().value}-寒意: {frostheart}")
        return frostheart

    def is_heavy_attack_bitterfrost_foreclaimed_self_ready(self, img: np.ndarray) -> bool:
        is_ready = self._heavy_attack_bitterfrost_foreclaimed_self_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-重击·枯霜·预求身: {is_ready}")
        return is_ready

    def is_resonance_skill_foreclaimed_self_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_foreclaimed_self_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能·预求身: {is_ready}")
        return is_ready

    def is_foreclaiming_blade_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._foreclaiming_blade_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放 预求我身·归刃: {is_ready}")
        return is_ready

    def is_hp_1_4(self, img: np.ndarray) -> bool:
        is_ready = self._hp_1_4_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-血量1/4: {is_ready}")
        return is_ready


class Hiyuki(BaseHiyuki):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 常世身

        # Ea
        ["E", 0.05, 1.51],
        ["a", 0.05, 0.95],
        # ["j", 0.05, 1.50],

        # 3a
        ["a", 0.05, 0.43],
        ["a", 0.05, 0.57],
        ["a", 0.05, 1.10],
        # ["j", 0.05, 1.50],

        ["z", 1.15, 1.66],
        # ["j", 0.05, 1.50],

        # 预求身

        ["R", 0.05, 4.00],
        # ["j", 0.05, 1.50],

        # ["E", 0.05, 0.47],
        # ["E", 0.05, 1.10],
        # ["j", 0.05, 1.50],

        # 3aEE3a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.53],
        ["a", 0.05, 0.80],
        ["E", 0.05, 0.47],
        ["E", 0.05, 1.10],
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.53],
        ["a", 0.05, 1.00],
        # ["j", 0.05, 1.50],

        # adaaaz
        ["a", 0.05, 0.11],
        ["d_down", 0.00, 0.50],
        ["a", 0.05, 0.65],
        ["d_up", 0.00, 0.00],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.30],
        ["z", 0.85 + 0.35, 2.50],
        # ["j", 0.05, 1.50],

        # 5a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.53],
        ["a", 0.05, 1.00],
        ["a", 0.05, 1.03],
        ["a", 0.05, 1.30],
        # ["j", 0.05, 1.50],

        # 5a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.53],
        ["a", 0.05, 1.00],
        ["a", 0.05, 1.03],
        ["a", 0.05, 1.30],
        # ["j", 0.05, 1.50],

        # 5a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.53],
        ["a", 0.05, 1.00],
        ["a", 0.05, 1.03],
        ["a", 0.05, 1.30],
        # ["j", 0.05, 1.50],

        # adaaa
        ["a", 0.05, 0.11],
        ["d_down", 0.00, 0.50],
        ["a", 0.05, 0.65],
        ["d_up", 0.00, 0.00],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.65],
        # ["j", 0.05, 1.50],

        # 5a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.53],
        ["a", 0.05, 1.00],
        # ["a", 0.05, 1.03],
        # ["a", 0.05, 1.30],
        # ["j", 0.05, 1.50],

        ["R", 3.10, 5.15],
        ["j", 0.05, 1.50],

    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a3_present_self(self):
        """a3拆分为a2 + a"""
        return [
            # 3a
            # ["a", 0.05, 0.43],
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.57],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],
            # # ["a", 0.05, 1.10],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],
        ]

    @combat_cache
    def a2_present_self(self):
        """a3拆分为a2 + a"""
        return [
            # 3a
            # ["a", 0.05, 0.43],
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.57],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],
            # # ["a", 0.05, 1.10],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.25],
        ]

    @combat_cache
    def a_present_self(self):
        """a3拆分为a2 + a"""
        return [
            # 3a
            # # ["a", 0.05, 0.43],
            # ["a", 0.05, 0.18],
            # ["a", 0.05, 0.20],
            # # ["a", 0.05, 0.57],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],
            # ["a", 0.05, 1.10],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],
        ]

    @combat_cache
    def Ea_present_self(self):
        return [
            # ["E", 0.05, 1.51],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.20],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.31],
            # ["a", 0.05, 0.95],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.35],
            ["a", 0.05, 0.25],
        ]

    @combat_cache
    def a_foreclaimed_self(self):
        """a3拆分为a2 + a"""
        return [
            # ["a", 0.05, 0.33],
            # ["a", 0.05, 0.53],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.23],
            # ["a", 0.05, 0.80],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
        ]

    @combat_cache
    def a2(self):
        return [
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.05],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.00],
        ]

    @combat_cache
    def z_present_self(self):
        return [
            ["z", 1.15, 0.00],
            # ["w", 0.00, 1.66],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.26],
            ["a", 0.05, 0.25],
        ]

    @combat_cache
    def R_present_self(self):
        return [
            # ["R", 0.05, 4.00],
            ["R", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.00],
            ["w", 0.00, 0.45],
        ]

    @combat_cache
    def a3_foreclaimed_self(self):
        return [
            # 5a
            ["a", 0.05, 0.33],
            # ["a", 0.05, 0.53],
            ["a", 0.05, 0.23],
            ["a", 0.05, 0.25],
            # ["a", 0.05, 1.00],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.10],
            ["w", 0.00, 0.20],
            # ["a", 0.05, 1.03],
            # ["a", 0.05, 1.30],
        ]

    @combat_cache
    def EEa3_foreclaimed_self(self):
        return [
            # 3aEE3a
            # ["a", 0.05, 0.33],
            # ["a", 0.05, 0.53],
            # ["a", 0.05, 0.80],
            ["E", 0.05, 0.47],
            ["E", 0.05, 1.10],
            ["a", 0.05, 0.33],
            ["a", 0.05, 0.53],
            ["a", 0.05, 1.00],
        ]

    @combat_cache
    def ada_foreclaimed_self(self):
        return [
            # adaaaz
            ["a", 0.05, 0.11],
            ["d_down", 0.00, 0.50],
            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["d_up", 0.00, 0.00],
            ["a", 0.05, 0.30],
            # ["a", 0.05, 0.65],
            # ["a", 0.05, 0.65],
        ]

    @combat_cache
    def adaa_foreclaimed_self(self):
        return [
            # adaaaz
            ["a", 0.05, 0.11],
            ["d_down", 0.00, 0.50],
            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["d_up", 0.00, 0.00],
            ["a", 0.05, 0.30],
            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            # ["a", 0.05, 0.65],
        ]

    @combat_cache
    def adaaa_foreclaimed_self(self):
        return [
            # adaaa
            ["a", 0.05, 0.11],
            ["d_down", 0.00, 0.50],
            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["d_up", 0.00, 0.00],
            ["a", 0.05, 0.30],
            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def z_foreclaimed_self(self):
        return [
            # # adaaaz
            # ["a", 0.05, 0.11],
            # ["d_down", 0.00, 0.50],
            # ["a", 0.05, 0.65],
            # ["d_up", 0.00, 0.00],
            # ["a", 0.05, 0.65],
            # ["a", 0.05, 0.30],
            # ["z", 0.85 + 0.35, 2.50],
            ["z", 0.85 + 0.35, 1.70],
            ["w", 0.00, 0.80],
        ]

    @combat_cache
    def adaaaz_foreclaimed_self(self):
        return [
            # adaaaz
            ["a", 0.05, 0.11],
            ["d_down", 0.00, 0.50],
            ["a", 0.05, 0.65],
            ["d_up", 0.00, 0.00],
            ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["z", 0.85 + 0.35, 2.50],
        ]

    @combat_cache
    def E(self):
        return [
            ["E", 0.05, 1.51],
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能，普通摩托
            ["Q", 0.05, 0.30],
        ]

    @combat_cache
    def R_foreclaimed_self(self):
        return [
            ["R", 3.10, 5.15],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):

        time.sleep(0.1)
        self.combo_action(self.a2(), False)
        self.combo_action(self.Q(), False)

        img = self.img_service.screenshot()
        # dedication = self.dedication(img)
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_basic_attack_present_self_ready = self.is_basic_attack_present_self_ready(img)
        is_heavy_attack_frost_splinter_present_self_ready = self.is_heavy_attack_frost_splinter_present_self_ready(img)
        is_resonance_skill_present_self_ready = self.is_resonance_skill_present_self_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_foreclaiming_inward_vision_ready = self.is_foreclaiming_inward_vision_ready(img)
        is_basic_attack_foreclaimed_self_ready = self.is_basic_attack_foreclaimed_self_ready(img)
        frostheart = self.frostheart(img)
        is_heavy_attack_bitterfrost_foreclaimed_self_ready = self.is_heavy_attack_bitterfrost_foreclaimed_self_ready(
            img)
        is_resonance_skill_foreclaimed_self_ready = self.is_resonance_skill_foreclaimed_self_ready(img)
        is_foreclaiming_blade_liberation_ready = self.is_foreclaiming_blade_liberation_ready(img)

        # 是否是常世身
        def is_present_self() -> bool:
            if is_basic_attack_present_self_ready:
                return True
            if is_basic_attack_foreclaimed_self_ready:
                return False
            if is_resonance_skill_present_self_ready:
                return True
            if is_heavy_attack_frost_splinter_present_self_ready:
                return True
            if frostheart > 0:
                return False
            # if dedication > 0:
            #     return True
            return False

        is_present_self = is_present_self()
        logger.debug(f"is_present_self: {is_present_self}")
        is_present_self_to_foreclaimed_self = False

        # 常世身
        if is_present_self:
            if not is_foreclaiming_inward_vision_ready:
                # 正常情况没解锁重击，打完剩余普攻连段
                if not is_heavy_attack_frost_splinter_present_self_ready:
                    self.combo_action(self.a_present_self(), True)
                    img = self.img_service.screenshot()
                    is_heavy_attack_frost_splinter_present_self_ready = self.is_heavy_attack_frost_splinter_present_self_ready(
                        img)
                    is_resonance_skill_present_self_ready = self.is_resonance_skill_present_self_ready(img)
                    is_hp_1_4 = self.is_hp_1_4(img)
                    if not is_hp_1_4:
                        return

                # 检查重击，没解锁继续尝试打满心念
                if not is_heavy_attack_frost_splinter_present_self_ready:
                    if is_resonance_skill_present_self_ready:
                        self.combo_action(self.Ea_present_self(), False)
                    elif self.random_float() < 0.5:
                        self.combo_action(self.a3_present_self(), False)

                    img = self.img_service.screenshot()
                    is_heavy_attack_frost_splinter_present_self_ready = self.is_heavy_attack_frost_splinter_present_self_ready(
                        img)
                    is_hp_1_4 = self.is_hp_1_4(img)
                    if not is_hp_1_4:
                        return
                    boss_hp = self.boss_hp(img)
                    if boss_hp <= 0.01:
                        return
                    # 心念仍不满
                    if not is_heavy_attack_frost_splinter_present_self_ready:
                        return
                    # 轴较长，切人回血，防止暴毙
                    if self.random_float() < 0.5:
                        return

                # 打重击解锁一段大
                self.combo_action(self.z_present_self(), False)

                for i in range(2):
                    img = self.img_service.screenshot()
                    is_foreclaiming_inward_vision_ready = self.is_foreclaiming_inward_vision_ready(img)
                    is_hp_1_4 = self.is_hp_1_4(img)
                    if not is_hp_1_4:
                        return
                    # boss_hp = self.boss_hp(img)
                    # if boss_hp <= 0.01:
                    #     return
                    if is_foreclaiming_inward_vision_ready:
                        break
                    if i == 0:
                        time.sleep(0.25)
                        continue
                    return

            # 开大
            self.combo_action(self.R_present_self(), True)
            is_present_self_to_foreclaimed_self = True

        # 预求身
        if not is_present_self or is_present_self_to_foreclaimed_self:
            if frostheart <= 100:
                self.combo_action(self.a3_foreclaimed_self(), True)
                img = self.img_service.screenshot()
                frostheart = self.frostheart(img)
                is_heavy_attack_bitterfrost_foreclaimed_self_ready = self.is_heavy_attack_bitterfrost_foreclaimed_self_ready(
                    img)
                is_resonance_skill_foreclaimed_self_ready = self.is_resonance_skill_foreclaimed_self_ready(img)
                is_foreclaiming_blade_liberation_ready = self.is_foreclaiming_blade_liberation_ready(img)
                is_hp_1_4 = self.is_hp_1_4(img)
                if not is_hp_1_4:
                    return
                boss_hp = self.boss_hp(img)
                if boss_hp <= 0.01:
                    return

            if is_resonance_skill_foreclaimed_self_ready:
                # 有E打EE
                self.combo_action(self.EEa3_foreclaimed_self(), True)
                img = self.img_service.screenshot()
                frostheart = self.frostheart(img)
                is_heavy_attack_bitterfrost_foreclaimed_self_ready = self.is_heavy_attack_bitterfrost_foreclaimed_self_ready(
                    img)
                is_resonance_skill_foreclaimed_self_ready = self.is_resonance_skill_foreclaimed_self_ready(img)
                is_foreclaiming_blade_liberation_ready = self.is_foreclaiming_blade_liberation_ready(img)
                is_hp_1_4 = self.is_hp_1_4(img)
                if not is_hp_1_4 or is_resonance_skill_foreclaimed_self_ready:
                    return
            elif frostheart <= 100:
                self.combo_action(self.a3_foreclaimed_self(), True)

            if frostheart > 0:
                if frostheart == 100:
                    # 有居合打居合
                    self.combo_action(self.ada_foreclaimed_self(), True)
                elif frostheart >= 200:
                    #     self.combo_action(self.adaa_foreclaimed_self(), True)
                    # elif frostheart == 300:
                    self.combo_action(self.adaaa_foreclaimed_self(), True)
                img = self.img_service.screenshot()
                frostheart = self.frostheart(img)
                is_heavy_attack_bitterfrost_foreclaimed_self_ready = self.is_heavy_attack_bitterfrost_foreclaimed_self_ready(
                    img)
                if not is_foreclaiming_blade_liberation_ready:
                    is_foreclaiming_blade_liberation_ready = self.is_foreclaiming_blade_liberation_ready(img)
                is_hp_1_4 = self.is_hp_1_4(img)
                if not is_hp_1_4:
                    return
                # boss_hp = self.boss_hp(img)
                # if boss_hp <= 0.01:
                #     return
                # 打完一套还有2豆，可能被打了，切人回血
                if frostheart >= 200:
                    return

            if is_heavy_attack_bitterfrost_foreclaimed_self_ready:
                # 有重击打重击
                self.combo_action(self.z_foreclaimed_self(), not is_foreclaiming_blade_liberation_ready)  # 预输入
                img = self.img_service.screenshot()
                if not is_foreclaiming_blade_liberation_ready:
                    is_foreclaiming_blade_liberation_ready = self.is_foreclaiming_blade_liberation_ready(img)
                is_hp_1_4 = self.is_hp_1_4(img)
                if not is_hp_1_4:
                    return
                boss_hp = self.boss_hp(img)
                if boss_hp <= 0.01:
                    return

            self.combo_action(self.Q(), False)

            if is_foreclaiming_blade_liberation_ready:
                self.combo_action(self.R_foreclaimed_self(), True)
            return

        # 兜底
        self.combo_action(self.a2(), False)
        self.combo_action(self.Q(), False)
