import logging

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, LogicEnum, \
    ScenarioEnum, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseMornye(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁红圈
        self._concerto_energy_checker = ColorChecker.concerto_fusion()

        ## 基准模式

        # 静质量能 满时可重击进入广域观测模式
        self._rest_mass_energy_20_point = [(570, 668), (571, 668), (571, 669)]
        self._rest_mass_energy_color = [(63, 119, 250)]  # BGR
        self._rest_mass_energy_20_checker = ColorChecker(
            self._rest_mass_energy_20_point, self._rest_mass_energy_color, logic=LogicEnum.AND)

        self._rest_mass_energy_50_point = [(633, 668), (634, 668)]
        self._rest_mass_energy_50_color = self._rest_mass_energy_color
        self._rest_mass_energy_50_checker = ColorChecker(
            self._rest_mass_energy_50_point, self._rest_mass_energy_50_color, logic=LogicEnum.AND)

        self._rest_mass_energy_80_point = [(692, 668), (693, 668), (693, 669)]
        self._rest_mass_energy_80_color = self._rest_mass_energy_color
        self._rest_mass_energy_80_checker = ColorChecker(
            self._rest_mass_energy_80_point, self._rest_mass_energy_80_color)

        # 重击·位势转换
        self._heavy_attack_geopotential_shift_point = [(954, 642), (953, 645), (956, 644), (953, 659)]
        self._heavy_attack_geopotential_shift_color = [(255, 255, 255)]  # BGR
        self._heavy_attack_geopotential_shift_checker = ColorChecker(
            self._heavy_attack_geopotential_shift_point, self._heavy_attack_geopotential_shift_color,
            logic=LogicEnum.AND)

        # # 共鸣技能·期望误差
        # self._resonance_skill_expectation_error_point = [(1078, 630), (1078, 658), (1096, 655)]
        # self._resonance_skill_expectation_error_color = [(255, 255, 255)]  # BGR
        # self._resonance_skill_expectation_error_checker = ColorChecker(
        #     self._resonance_skill_expectation_error_point, self._resonance_skill_expectation_error_color,
        #     logic=LogicEnum.AND)

        ## 广域观测模式

        # 广域观测模式
        self._wide_field_observation_mode_point = [(890, 627), (890, 640), (885, 644), (895, 644)]
        self._wide_field_observation_mode_color = [(255, 255, 255)]  # BGR
        self._wide_field_observation_mode_checker = ColorChecker(
            self._wide_field_observation_mode_point, self._wide_field_observation_mode_color, logic=LogicEnum.AND)

        # 相对动能 满时可释放重击·反演
        self._relative_momentum_20_point = self._rest_mass_energy_20_point
        self._relative_momentum_color = [(245, 202, 199), (255, 221, 188), (255, 206, 176), (255, 160, 140), (255, 237, 206)]  # BGR
        self._relative_momentum_20_checker = ColorChecker(
            self._relative_momentum_20_point, self._relative_momentum_color)

        self._relative_momentum_50_point = self._rest_mass_energy_50_point
        self._relative_momentum_50_color = self._relative_momentum_color
        self._relative_momentum_50_checker = ColorChecker(
            self._relative_momentum_50_point, self._relative_momentum_50_color, logic=LogicEnum.AND)

        self._relative_momentum_80_point = self._rest_mass_energy_80_point
        self._relative_momentum_80_color = self._relative_momentum_color
        self._relative_momentum_80_checker = ColorChecker(
            self._relative_momentum_80_point, self._relative_momentum_80_color, logic=LogicEnum.AND)

        # 共鸣技能·分布式阵列
        self._resonance_skill_optimal_solution_point = [(1082, 632), (1083, 632), (1084, 632)]
        self._resonance_skill_optimal_solution_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_optimal_solution_checker = ColorChecker(
            self._resonance_skill_optimal_solution_point, self._resonance_skill_optimal_solution_color,
            logic=LogicEnum.AND)

        # 重击·反演
        self._heavy_attack_inversion_point = [(949, 638), (959, 638), (954, 642), (953, 645), (956, 644)]
        self._heavy_attack_inversion_color = [(255, 255, 255)]  # BGR
        self._heavy_attack_inversion_checker = ColorChecker(
            self._heavy_attack_inversion_point, self._heavy_attack_inversion_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1145, 634)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1212, 652), (1212, 653), (1212, 654)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color, logic=LogicEnum.AND)

        # 共鸣解放2 谐振场内
        self._resonance_liberation_2_point = [(1205, 656), (1205, 657), (1205, 658)]
        self._resonance_liberation_2_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_2_checker = ColorChecker(
            self._resonance_liberation_2_point, self._resonance_liberation_2_color, logic=LogicEnum.AND)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.mornye

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Healer]

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def rest_mass_energy_count(self, img: np.ndarray) -> int:
        energy_count = 0
        if self._rest_mass_energy_20_checker.check(img):
            energy_count = 20
        if self._rest_mass_energy_50_checker.check(img):
            energy_count = 50
        if self._rest_mass_energy_80_checker.check(img):
            energy_count = 80
        logger.debug(f"{self.resonator_name().value}-静质量能: {energy_count}格")
        return energy_count

    def is_heavy_attack_geopotential_shift_ready(self, img: np.ndarray) -> bool:
        is_ready = self._heavy_attack_geopotential_shift_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-重击·位势转换: {is_ready}")
        return is_ready

    def is_wide_field_observation_mode_ready(self, img: np.ndarray) -> bool:
        is_ready = self._wide_field_observation_mode_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-广域观测模式: {is_ready}")
        return is_ready

    def relative_momentum_count(self, img: np.ndarray) -> int:
        energy_count = 0
        if self._relative_momentum_20_checker.check(img):
            energy_count = 20
        if self._relative_momentum_50_checker.check(img):
            energy_count = 50
        if self._relative_momentum_80_checker.check(img):
            energy_count = 80
        logger.debug(f"{self.resonator_name().value}-相对动能: {energy_count}格")
        return energy_count

    def is_resonance_skill_optimal_solution_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_optimal_solution_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能·分布式阵列: {is_ready}")
        return is_ready

    def is_heavy_attack_inversion_ready(self, img: np.ndarray) -> bool:
        is_ready = self._heavy_attack_inversion_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-重击·反演: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready

    def is_resonance_liberation_2_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_2_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放2: {is_ready}")
        return is_ready


class Mornye(BaseMornye):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    COMBO_SEQ = [
        # 基准模式
        # 4a
        ["a", 0.05, 0.42],
        ["a", 0.05, 0.70],
        ["a", 0.05, 0.86],
        ["a", 0.05, 1.20],
        ["j", 0.05, 1.50],

        # E
        ["E", 0.05, 1.45],
        ["j", 0.05, 1.50],

        # 3az
        ["a", 0.05, 0.42],
        ["a", 0.05, 0.70],
        ["a", 0.05, 0.30],
        ["z", 0.80, 1.00],
        # ["d", 0.05, 0.30],
        ["j", 0.05, 1.80],
        ["j", 0.05, 1.50],

        # 2aEaz
        ["a", 0.05, 0.42],
        ["a", 0.05, 0.10],
        ["E", 0.05, 0.10],
        ["a", 0.05, 0.30],
        ["z", 0.80, 1.00],
        # ["j", 0.05, 2.00],
        # ["j", 0.05, 1.50],

        ## 广域观测模式
        ["a", 0.05, 0.50],
        ["a", 0.05, 0.70],
        ["a", 0.05, 0.72],
        ["a", 0.05, 0.86],

        ["d", 0.05, 0.30],

    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a3z(self):
        return [
            # 3az
            # ["a", 0.05, 0.42],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.17],
            # ["a", 0.05, 0.70],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.30],
            ["a", 0.05, 0.13],
            ["a", 0.05, 0.12],
            ["z", 0.80, 0.20],
            ["w", 0.00, 0.80],
        ]

    def a3z_a3(self):
        return [
            # 3az
            # ["a", 0.05, 0.42],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.17],
            # ["a", 0.05, 0.70],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.30],
            ["a", 0.05, 0.13],
            ["a", 0.05, 0.12],
            # ["z", 0.80, 0.20],
            # ["w", 0.00, 0.80],
        ]

    def a3z_z(self):
        return [
            # 3az
            # # ["a", 0.05, 0.42],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.17],
            # # ["a", 0.05, 0.70],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.20],
            # # ["a", 0.05, 0.30],
            # ["a", 0.05, 0.13],
            # ["a", 0.05, 0.12],
            ["z", 1.20, 0.00],
            ["w", 0.00, 0.80],
        ]

    @combat_cache
    def a3(self):
        return [
            # 3az
            # ["a", 0.05, 0.42],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.17],
            # ["a", 0.05, 0.70],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.30],
            ["a", 0.05, 0.13],
            ["a", 0.05, 0.12],
            # ["z", 0.80, 0.20],
            # ["w", 0.00, 0.80],
        ]

    @combat_cache
    def Eaaaz(self):
        return [
            ["E", 0.05, 0.50],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["z", 1.20, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.20],
            ["z", 0.50, 0.20],
        ]

    @combat_cache
    def Eaa(self):
        return [
            # 共鸣技能 E
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
        ]

    @combat_cache
    def E(self):
        return [
            # 共鸣技能 E
            ["E", 0.05, 0.20],
        ]

    @combat_cache
    def z(self):
        return [
            ["z", 1.00, 0.50]
        ]

    @combat_cache
    def zaa(self):
        return [
            ["z", 1.00, 0.10],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
        ]

    @combat_cache
    def Q(self):
        return [
            ["Q", 0.05, 0.50],
        ]

    @combat_cache
    def R(self):
        return [
            ["R", 0.05, 0.00],
            ["w", 0.00, 5.64],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def exit_special_state(self, scenario_enum: ScenarioEnum | None = None):
        if scenario_enum != ScenarioEnum.BeforeEchoSearch:
            return
        logger.debug("exit_special_state")
        img = self.img_service.screenshot()
        if not self.is_wide_field_observation_mode_ready(img):
            return
        quit_seq = [
            ["j", 0.05, 2.00],
        ]
        self.combo_action(quit_seq, True, ignore_event=True)

    def combo(self):
        self.combo_action(self.a3z_a3(), True)

        img = self.img_service.screenshot()
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        # rest_mass_energy_count = self.rest_mass_energy_count(img)
        is_heavy_attack_geopotential_shift_ready = self.is_heavy_attack_geopotential_shift_ready(img)
        is_wide_field_observation_mode_ready = self.is_wide_field_observation_mode_ready(img)
        # relative_momentum_count = self.relative_momentum_count(img)
        is_resonance_skill_optimal_solution_ready = self.is_resonance_skill_optimal_solution_ready(img)
        # is_heavy_attack_inversion_ready = self.is_heavy_attack_inversion_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        is_resonance_liberation_2_ready = self.is_resonance_liberation_2_ready(img)

        # 不在广域观测模式
        if not is_wide_field_observation_mode_ready:
            if is_heavy_attack_geopotential_shift_ready:
                self.combo_action(self.E(), False)
                self.combo_action(self.a3z_z(), True)
                if self.random_float() < 0.25:
                    self.combo_action(self.E(), False)
                    return

                img = self.img_service.screenshot()
                is_wide_field_observation_mode_ready = self.is_wide_field_observation_mode_ready(img)
                is_resonance_skill_optimal_solution_ready = self.is_resonance_skill_optimal_solution_ready(img)
                is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
                is_resonance_liberation_2_ready = self.is_resonance_liberation_2_ready(img)
            else:
                self.combo_action(self.E(), False)
                self.combo_action(self.R(), is_resonance_liberation_ready)
                self.combo_action(self.Q(), False)
                return

        # 广域观测模式
        if is_wide_field_observation_mode_ready:
            if is_resonance_liberation_ready or is_resonance_liberation_2_ready:
                self.combo_action(self.R(), True)
                img = self.img_service.screenshot()
                is_resonance_skill_optimal_solution_ready = self.is_resonance_skill_optimal_solution_ready(img)

            if is_resonance_skill_optimal_solution_ready:
                if self.random_float() > 0.65:
                    self.combo_action(self.Eaaaz(), True)
                else:
                    self.combo_action(self.Eaa(), True)
                    self.combo_action(self.Q(), False)
                    return

            img = self.img_service.screenshot()
            is_heavy_attack_inversion_ready = self.is_heavy_attack_inversion_ready(img)
            if is_heavy_attack_inversion_ready:
                self.combo_action(self.zaa(), False)
            self.combo_action(self.Q(), False)
            return

        if is_resonance_liberation_ready or is_resonance_liberation_2_ready:
            self.combo_action(self.R(), False)
        # self.combo_action(self.zaa(), False)
        self.combo_action(self.Q(), False)
        return
