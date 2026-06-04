import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, LogicEnum, \
    combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseLynae(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁黄圈
        self._concerto_energy_checker = ColorChecker.concerto_spectro()

        ## 光学取样阶段 Optical Sampling Stage

        # # 溢彩
        # self._overflow_point = []

        # 普攻·灵感碰撞，进入绮彩巡游状态
        self._basic_attack_spark_collision_point = [(965, 637), (960, 640), (955, 629), (969, 648)]
        self._basic_attack_spark_collision_color = [(255, 255, 255)]  # BGR
        self._basic_attack_spark_collision_checker = ColorChecker(
            self._basic_attack_spark_collision_point, self._basic_attack_spark_collision_color, logic=LogicEnum.AND)

        ## 绮彩巡游状态 Kaleidoscopic Parade

        # 流光 120
        self._lumiflow_point = [(715, 667), (715, 668)]
        self._lumiflow_color = [(255, 255, 255)]  # BGR
        self._lumiflow_checker = ColorChecker(self._lumiflow_point, self._lumiflow_color)

        # 本色 能量1 血条上方的3格能量
        self._true_color1_point = [(567, 668), (574, 668), (580, 668), (587, 668), (593, 668)]
        self._true_color1_color = [(184, 238, 93), (191, 240, 101), (177, 240, 71), (194, 255, 98), (164, 244, 77)]  # BGR
        self._true_color1_checker = ColorChecker(self._true_color1_point, self._true_color1_color, tolerance=50)

        # 本色 能量2 血条上方的3格能量
        self._true_color2_point = [(613, 668), (622, 668), (632, 668), (643, 668), (654, 668)]
        self._true_color2_color = [(225, 255, 99), (235, 255, 59), (255, 255, 99), (234, 224, 53), (249, 204, 60)]  # BGR
        self._true_color2_checker = ColorChecker(self._true_color2_point, self._true_color2_color, tolerance=50)

        # 本色 能量3 血条上方的3格能量
        self._true_color3_point = [(668, 668), (677, 668), (687, 668), (701, 668), (712, 668)]
        self._true_color3_color = [(255, 130, 161), (255, 145, 202), (255, 142, 227), (255, 133, 255), (255, 142, 227)]  # BGR
        self._true_color3_checker = ColorChecker(self._true_color3_point, self._true_color3_color, tolerance=50)

        # 绮彩巡游·普攻 轮滑形态的普攻，可判断是否在轮滑状态
        self._kaleidoscopic_parade_basic_attack_point = [(955, 630), (951, 639), (940, 654), (949, 660)]
        self._kaleidoscopic_parade_basic_attack_color = [(255, 255, 255)]  # BGR
        self._kaleidoscopic_parade_basic_attack_checker = ColorChecker(
            self._kaleidoscopic_parade_basic_attack_point, self._kaleidoscopic_parade_basic_attack_color, logic=LogicEnum.AND)

        # 普攻·幻光折跃 强化跳跃
        self._basic_attack_polychrome_leap_point = [(1091, 634), (1078, 657)]
        self._basic_attack_polychrome_leap_color = [(255, 255, 255)]  # BGR
        self._basic_attack_polychrome_leap_checker = ColorChecker(
            self._basic_attack_polychrome_leap_point, self._basic_attack_polychrome_leap_color)

        # 普攻·虹彩飞溅 强化下落攻击青春版
        self._basic_attack_iridescent_splash_point = [(1096, 647), (1071, 655), (968, 646), (945, 656)]
        self._basic_attack_iridescent_splash_color = [(255, 255, 255)]  # BGR
        self._basic_attack_iridescent_splash_checker = ColorChecker(
            self._basic_attack_iridescent_splash_point, self._basic_attack_iridescent_splash_color, logic=LogicEnum.AND)

        # 普攻·视觉冲击 强化下落攻击
        self._basic_attack_visual_impact_point = [(1081, 629), (1085, 650), (953, 627), (946, 647)]
        self._basic_attack_visual_impact_color = [(255, 255, 255)]  # BGR
        self._basic_attack_visual_impact_checker = ColorChecker(
            self._basic_attack_visual_impact_point, self._basic_attack_visual_impact_color, logic=LogicEnum.AND)

        # 共鸣技能
        self._resonance_skill_point = [(1091, 634), (1078, 657)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(
            self._resonance_skill_point, self._resonance_skill_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1144, 632), (1142, 654)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1216, 634), (1208, 655)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.lynae

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
    #     if self._energy5_checker.check(img):
    #         energy_count = 5
    #     logger.debug(f"{self.resonator_name().value}-能量: {energy_count}格")
    #     return energy_count

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

    def is_basic_attack_spark_collision_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_spark_collision_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·灵感碰撞: {is_ready}")
        return is_ready

    def is_max_lumiflow(self, img: np.ndarray) -> bool:
        is_ready = self._lumiflow_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-流光: {'已满' if is_ready else '未满'}")
        return is_ready

    def true_color_count(self, img: np.ndarray) -> int:
        true_color_count = 0
        if self._true_color1_checker.check(img):
            true_color_count = 1
        if self._true_color2_checker.check(img):
            true_color_count = 2
        if self._true_color3_checker.check(img):
            true_color_count = 3
        logger.debug(f"{self.resonator_name().value}-本色: {true_color_count}格")
        return true_color_count

    def is_kaleidoscopic_parade_basic_attack_ready(self, img: np.ndarray) -> bool:
        is_ready = self._kaleidoscopic_parade_basic_attack_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-绮彩巡游·普攻: {is_ready}")
        return is_ready

    def is_basic_attack_polychrome_leap_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_polychrome_leap_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·幻光折跃: {is_ready}")
        return is_ready

    def is_basic_attack_iridescent_splash_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_iridescent_splash_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·虹彩飞溅: {is_ready}")
        return is_ready

    def is_basic_attack_visual_impact_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_visual_impact_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻·视觉冲击: {is_ready}")
        return is_ready


class Lynae(BaseLynae):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # E2a
        ["E", 0.05, 0.88],
        # ["a", 0.05, 0.33],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["j", 0.05, 1.50],

        # 3a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["j", 0.05, 1.50],

        # z
        ["z", 2.26, 0.70],
        # ["j", 0.05, 1.20],

        # # 3jza
        # ["j", 0.05, 0.50],
        # ["j", 0.05, 0.50],
        # ["j", 0.05, 0.50],
        # ["z", 1.50, 0.10],
        # ["a", 0.05, 1.22],
        # ["j", 0.05, 1.20],

        # 2jzja
        ["j", 0.05, 0.50],
        ["j", 0.05, 0.50],
        ["z", 1.50, 0.10],
        ["j", 0.05, 0.50],
        ["a", 0.05, 1.22],
        ["j", 0.05, 1.20],

        # 5a
        ["a", 0.05, 0.45],
        ["a", 0.05, 0.55],
        ["a", 0.05, 0.58],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.80],  # 扔罐子
        ["w", 0.00, 0.85],  # 爆炸
        ["j", 0.05, 1.20],

        # E4a
        ["E", 0.05, 0.88],
        # ["a", 0.05, 0.45],
        ["a", 0.05, 0.55],
        ["a", 0.05, 0.58],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.80],  # 扔罐子
        ["w", 0.00, 0.85],  # 爆炸
        ["j", 0.05, 1.20],

        # R
        ["R", 0.05, 4.88],
        ["j", 0.05, 1.20],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def E(self):
        return [
            ["E", 0.05, 0.88],
        ]

    @combat_cache
    def optical_sampling_stage_a3(self):
        return [
            # 3a
            ["a", 0.05, 0.33],

            # ["a", 0.05, 0.82],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.22],

            # ["a", 0.05, 1.02],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.32],
        ]

    @combat_cache
    def optical_sampling_stage_E2a(self):
        return [
            # ["E", 0.05, 0.88],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.63],

            # ["a", 0.05, 0.33],

            # ["a", 0.05, 0.82],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.22],

            # ["a", 0.05, 1.02],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.32],
        ]

    @combat_cache
    def ER(self):
        return [
            ["E", 0.05, 0.30],
            ["R", 0.05, 0.30],
            ["R", 0.05, 3.65],
        ]

    @combat_cache
    def a(self):
        return [
            # 2a
            ["a", 0.05, 0.33],
        ]

    @combat_cache
    def a3(self):
        return [
            # a
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
        ]

    # @combat_cache
    # def a2(self):
    #     return [
    #         # 2a
    #         ["a", 0.05, 0.33],
    #         # ["a", 0.05, 0.82],  # 拆分
    #         ["a", 0.05, 0.33],
    #         ["a", 0.05, 0.34],  # kaleidoscopic_parade_a2
    #         ["a", 0.05, 0.15],  # optical_sampling_stage_a2
    #     ]

    @combat_cache
    def optical_sampling_stage_zQ(self):
        return [
            # ["z", 2.26, 0.70],
            ["a_down", 1.20, 0.00],
            ["Q", 0.00, 1.06],
            ["a_up", 0.00, 0.20],
            ["w", 0.00, 0.50],
        ]

    @combat_cache
    def optical_sampling_stage_EzQ(self):
        return [
            ["E", 0.05, 0.30],
            # ["z", 2.26, 0.70],
            ["a_down", 1.20, 0.00],
            ["Q", 0.00, 1.06],
            ["a_up", 0.00, 0.20],
            ["w", 0.00, 0.50],
        ]

    @combat_cache
    def optical_sampling_stage_RzQ(self):
        # 预输入重击
        return [
            # ["R", 0.05, 4.70],
            ["R", 0.05, 0.30],
            ["R", 0.05, 3.65],

            # ["z", 2.26, 0.70],
            ["a_down", 0.00, 0.80],
            ["Q", 0.00, 0.00],
            ["w", 0.00, 1.40],
            ["Q", 0.00, 0.00],
            ["w", 0.00, 0.76],
            ["a_up", 0.00, 0.20],
            ["w", 0.00, 0.50],
        ]

    @combat_cache
    def optical_sampling_stage_EprezQ(self):
        # 预输入重击
        return [
            # ["E", 0.05, 0.88],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.00],

            # ["z", 2.26, 0.70],
            ["z_down", 1.20 + 0.63, 0.00],
            ["Q", 0.00, 0.00],
            ["z_up", 1.06, 0.20],
            ["w", 0.00, 0.50],
        ]

    @combat_cache
    def kaleidoscopic_parade_z(self):
        return [
            ["z", 1.50, 0.10],
        ]

    @combat_cache
    def kaleidoscopic_parade_j(self):
        return [
            ["j", 0.05, 0.50],
        ]

    @combat_cache
    def kaleidoscopic_parade_3jza(self):
        return [
            ["j", 0.05, 0.50],
            ["j", 0.05, 0.50],
            ["j", 0.05, 0.50],
            ["z", 1.50, 0.10],
            # ["a", 0.05, 1.22],  # 拆分
            ["a", 0.05, 0.20],
            ["E", 0.05, 0.20],
            ["w", 0.00, 0.77],
        ]

    @combat_cache
    def kaleidoscopic_parade_2jzja(self):
        return [
            ["j", 0.05, 0.50],
            ["j", 0.05, 0.50],
            ["z", 1.50, 0.10],
            ["j", 0.05, 0.50],
            # ["a", 0.05, 1.22],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.00, 0.20],
            ["a", 0.00, 0.20],
            ["w", 0.00, 0.37],
        ]

    @combat_cache
    def kaleidoscopic_parade_3ja(self):
        return [
            ["j", 0.05, 0.50],
            ["j", 0.05, 0.50],
            ["j", 0.05, 0.50],
            # ["a", 0.05, 1.22],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.00, 0.20],
            ["a", 0.00, 0.20],
            ["w", 0.00, 0.37],
        ]

    @combat_cache
    def kaleidoscopic_parade_a5(self):
        return [
            # ["a", 0.05, 0.45],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 0.55],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.58],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.28],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.80],  # 扔罐子
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            ["w", 0.00, 0.85],  # 爆炸
        ]

    @combat_cache
    def kaleidoscopic_parade_E4a(self):
        return [
            ["E", 0.05, 0.88],
            # ["a", 0.05, 0.45],

            # ["a", 0.05, 0.55],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.58],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.28],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.80],  # 扔罐子
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            ["w", 0.00, 0.85],  # 爆炸
        ]

    @combat_cache
    def aQ(self):
        return [
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.10],
            ["Q", 0.05, 0.10],
        ]

    @combat_cache
    def Q(self):
        return [
            ["Q", 0.05, 0.10],
        ]

    @combat_cache
    def R(self):
        return [
            ["R", 0.05, 4.00],
            ["w", 0.00, 0.70],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):

        # 光学取样阶段
        # 普攻或重击普攻，最多三段
        # 打满溢彩能量，重击蓄力（霸体减伤）可进入轮滑形态，满蓄力获得120点满流光

        # 绮彩巡游状态
        # 普攻最多5段
        # 可强化跳跃三次，每次消耗40点流光，并获得一点本色，最多三点
        # 三点本色可打出强化下落攻击
        # 重击可持续自动普攻转圈，消耗体力，跳跃可在空中转圈，只可在空中转圈一次，需要落地重置
        # 延奏会退出绮彩巡游状态，变奏不会

        # E后从普攻第二段开始

        self.combo_action(self.a3(), True)

        img = self.img_service.screenshot()

        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        is_basic_attack_spark_collision_ready = self.is_basic_attack_spark_collision_ready(img)
        # is_max_lumiflow = self.is_max_lumiflow(img)
        true_color_count = self.true_color_count(img)
        is_kaleidoscopic_parade_basic_attack_ready = self.is_kaleidoscopic_parade_basic_attack_ready(img)
        # is_basic_attack_polychrome_leap_ready = self.is_basic_attack_polychrome_leap_ready(img)
        # is_basic_attack_visual_impact_ready = self.is_basic_attack_visual_impact_ready(img)

        is_optical_sampling_stage_z = False
        # 光学取样阶段
        if not is_kaleidoscopic_parade_basic_attack_ready:
            # 溢彩能量满，进入绮彩巡游状态
            if is_basic_attack_spark_collision_ready:
                # 开大预输入重击
                if is_resonance_liberation_ready:
                    self.combo_action(self.optical_sampling_stage_RzQ(), True)
                else:
                    self.combo_action(self.optical_sampling_stage_zQ(), True)
                is_optical_sampling_stage_z = True
            else:
                # 溢彩能量没满
                if is_resonance_liberation_ready and is_resonance_skill_ready:
                    self.combo_action(self.E(), True)
                    self.combo_action(self.R(), True)
                    return
                # 有大开大
                elif is_resonance_liberation_ready:
                    self.combo_action(self.R(), True)
                    self.combo_action(self.E(), False)
                    return
                # 有E打E合轴
                elif is_resonance_skill_ready:
                    if self.random_float() > 0.6:
                        self.combo_action(self.E(), False)
                    else:
                        self.combo_action(self.optical_sampling_stage_E2a(), True)
                    time.sleep(0.1)
                    return

        # 绮彩巡游状态
        if is_kaleidoscopic_parade_basic_attack_ready or is_optical_sampling_stage_z:
            if is_optical_sampling_stage_z:
                # 检查流光能量
                img = self.img_service.screenshot()
                is_resonance_skill_ready = self.is_resonance_skill_ready(img)
                is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
                is_max_lumiflow = self.is_max_lumiflow(img)
                # 流光能量满，三跳下砸
                if is_max_lumiflow:
                    if self.random_float() < 0.5:
                        self.combo_action(self.kaleidoscopic_parade_2jzja(), True)
                    else:
                        self.combo_action(self.kaleidoscopic_parade_3ja(), True)
                    return

            # 想要什么颜色
            if is_resonance_skill_ready:
                self.combo_action(self.E(), False)
                if is_resonance_liberation_ready:
                    time.sleep(0.4)
            # 送你个惊喜
            if is_resonance_liberation_ready:
                self.combo_action(self.R(), True)

            img = self.img_service.screenshot()
            true_color_count = self.true_color_count(img)
            # 本色能量满
            if true_color_count == 3:
                self.combo_action(self.kaleidoscopic_parade_j(), True)
                self.combo_action(self.a(), False)
                time.sleep(0.2)
                self.combo_action(self.a(), False)
                return

            # 重击打太多会缺体力
            if self.random_float() < 0.5:
                self.combo_action(self.kaleidoscopic_parade_z(), True)
            else:
                self.combo_action(self.optical_sampling_stage_a3(), True)

            ## 空中攻击

            # 检查流光能量
            img = self.img_service.screenshot()
            is_max_lumiflow = self.is_max_lumiflow(img)
            is_basic_attack_polychrome_leap_ready = self.is_basic_attack_polychrome_leap_ready(img)
            # 流光能量满，三跳下砸
            if is_max_lumiflow:
                if self.random_float() < 0.5:
                    self.combo_action(self.kaleidoscopic_parade_2jzja(), True)
                else:
                    self.combo_action(self.kaleidoscopic_parade_3ja(), True)
                return
            if not is_basic_attack_polychrome_leap_ready:
                return

            # 折跃
            self.combo_action(self.kaleidoscopic_parade_j(), True)
            if self.random_float() < 0.25:
                self.combo_action(self.kaleidoscopic_parade_z(), False)

            # 喷涂
            img = self.img_service.screenshot()
            is_max_lumiflow = self.is_max_lumiflow(img)
            is_basic_attack_polychrome_leap_ready = self.is_basic_attack_polychrome_leap_ready(img)
            # 流光能量满 或 流光能量不足1/3，下砸结束
            if is_max_lumiflow or not is_basic_attack_polychrome_leap_ready:
                self.combo_action(self.aQ(), False)
                return
            self.combo_action(self.kaleidoscopic_parade_j(), False)

            # 来兜个风
            time.sleep(0.2)
            img = self.img_service.screenshot()
            is_max_lumiflow = self.is_max_lumiflow(img)
            is_basic_attack_polychrome_leap_ready = self.is_basic_attack_polychrome_leap_ready(img)
            time.sleep(0.5 - 0.2)
            # 流光能量满 或 流光能量不足1/3，下砸结束
            if is_max_lumiflow or not is_basic_attack_polychrome_leap_ready:
                self.combo_action(self.a3(), True)
                return
            self.combo_action(self.kaleidoscopic_parade_j(), True)
            self.combo_action(self.a3(), True)
            return

        # 兜底
        self.combo_action(self.R(), False)
        self.combo_action(self.optical_sampling_stage_a3(), False)
        self.combo_action(self.E(), False)
