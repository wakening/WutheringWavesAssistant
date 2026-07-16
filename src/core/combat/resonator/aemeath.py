import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, LogicEnum, \
    Morph
from src.core.combat.resonator.generic import GenericCombo
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseAemeath(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁红圈
        self._concerto_energy_checker = ColorChecker.concerto_fusion()

        # 同步率 上限200点
        self._synchronization_rate_color = [(251, 221, 190), (255, 252, 236), (255, 237, 243), (255, 219, 247)]  # BGR

        self._synchronization_rate_100_point = [(660, 668), (661, 668)]
        self._synchronization_rate_100_checker = ColorChecker(
            self._synchronization_rate_100_point, self._synchronization_rate_color)

        self._synchronization_rate_200_point = [(709, 668), (710, 668)]
        self._synchronization_rate_200_checker = ColorChecker(
            self._synchronization_rate_200_point, self._synchronization_rate_color)

        # 共鸣率 上限4点
        self._resonance_rate_color = [(255, 255, 255)]  # BGR

        self._resonance_rate_1_point = [(566, 661), (567, 661), (567, 662)]
        self._resonance_rate_1_checker = ColorChecker(
            self._resonance_rate_1_point, self._resonance_rate_color, logic=LogicEnum.AND)

        self._resonance_rate_2_point = [(588, 661), (589, 661), (588, 662)]
        self._resonance_rate_2_checker = ColorChecker(
            self._resonance_rate_2_point, self._resonance_rate_color, logic=LogicEnum.AND)

        self._resonance_rate_3_point = [(679, 661), (680, 661), (679, 662)]
        self._resonance_rate_3_checker = ColorChecker(
            self._resonance_rate_3_point, self._resonance_rate_color, logic=LogicEnum.AND)

        self._resonance_rate_4_point = [(700, 661), (701, 661), (701, 662)]
        self._resonance_rate_4_checker = ColorChecker(
            self._resonance_rate_4_point, self._resonance_rate_color, logic=LogicEnum.AND)

        ## 爱弥斯形态

        # 重击·爱弥斯
        self._heavy_attack_aemeath_point = [(946, 660), (950, 657), (959, 655)]
        self._heavy_attack_aemeath_color = [(255, 255, 255)]  # BGR
        self._heavy_attack_aemeath_checker = ColorChecker(
            self._heavy_attack_aemeath_point, self._heavy_attack_aemeath_color, logic=LogicEnum.AND)

        # 共鸣技能 构型切换·机兵
        self._resonance_skill_form_switch_mech_point = [(1076, 634), (1086, 633), (1094, 635), (1087, 659), (1096, 653)]
        self._resonance_skill_form_switch_mech_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_form_switch_mech_checker = ColorChecker(
            self._resonance_skill_form_switch_mech_point,
            self._resonance_skill_form_switch_mech_color,
            logic=LogicEnum.AND)

        # 共鸣技能 合击·突刺·兵装融合
        self._resonance_skill_sync_strike_armament_merge_point = [(1083, 636), (1086, 632), (1078, 654), (1090, 650), (1096, 656)]
        self._resonance_skill_sync_strike_armament_merge_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_sync_strike_armament_merge_checker = ColorChecker(
            self._resonance_skill_sync_strike_armament_merge_point,
            self._resonance_skill_sync_strike_armament_merge_color,
            logic=LogicEnum.AND)

        # 共鸣技能 光翼共奏·降临 消耗100同步率
        self._resonance_skill_seraphic_duet_overture_point = [(1072, 637), (1078, 636), (1090, 636), (1082, 651)]
        self._resonance_skill_seraphic_duet_overture_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_seraphic_duet_overture_checker = ColorChecker(
            self._resonance_skill_seraphic_duet_overture_point,
            self._resonance_skill_seraphic_duet_overture_color,
            logic=LogicEnum.AND)

        ## 机兵形态

        # 重击·机兵
        self._heavy_attack_mech_point = [(948, 628), (938, 655), (945, 656), (962, 656), (960, 650)]
        self._heavy_attack_mech_color = [(255, 255, 255)]  # BGR
        self._heavy_attack_mech_checker = ColorChecker(
            self._heavy_attack_mech_point, self._heavy_attack_mech_color, logic=LogicEnum.AND)

        # 共鸣技能 构型切换·爱弥斯
        self._resonance_skill_form_switch_aemeath_point = [(1084, 628), (1085, 628), (1081, 657)]
        self._resonance_skill_form_switch_aemeath_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_form_switch_aemeath_checker = ColorChecker(
            self._resonance_skill_form_switch_aemeath_point,
            self._resonance_skill_form_switch_aemeath_color,
            logic=LogicEnum.AND)

        # 共鸣技能 合击·突刺·启明之音
        self._resonance_skill_sync_strike_call_of_dawn_point = [(1096, 633), (1098, 633), (1074, 634), (1075, 650)]
        self._resonance_skill_sync_strike_call_of_dawn_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_sync_strike_call_of_dawn_checker = ColorChecker(
            self._resonance_skill_sync_strike_call_of_dawn_point,
            self._resonance_skill_sync_strike_call_of_dawn_color,
            logic=LogicEnum.AND)

        # 共鸣技能 光翼共奏·登台 消耗100同步率
        self._resonance_skill_seraphic_duet_encore_point = [(1083, 629), (1067, 647), (1073, 655), (1092, 654), (1098, 644)]
        self._resonance_skill_seraphic_duet_encore_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_seraphic_duet_encore_checker = ColorChecker(
            self._resonance_skill_seraphic_duet_encore_point,
            self._resonance_skill_seraphic_duet_encore_color,
            logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1144, 659), (1147, 659)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放 星辉破界而来·过载 自动切换为机兵形态
        self._resonance_liberation_heavenfall_edict_overdrive_point = [(1209, 630), (1210, 630), (1209, 662)]
        self._resonance_liberation_heavenfall_edict_overdrive_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_heavenfall_edict_overdrive_checker = ColorChecker(
            self._resonance_liberation_heavenfall_edict_overdrive_point,
            self._resonance_liberation_heavenfall_edict_overdrive_color,
            logic=LogicEnum.AND)

        # 共鸣解放 星辉破界而来·终结
        self._resonance_liberation_heavenfall_edict_finale_point = [(1213, 643), (1212, 657), (1213, 658)]
        self._resonance_liberation_heavenfall_edict_finale_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_heavenfall_edict_finale_checker = ColorChecker(
            self._resonance_liberation_heavenfall_edict_finale_point,
            self._resonance_liberation_heavenfall_edict_finale_color,
            logic=LogicEnum.AND)


    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.aemeath

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def synchronization_rate_count(self, img: np.ndarray) -> int:
        synchronization_rate = 0
        if self._synchronization_rate_100_checker.check(img):
            synchronization_rate = 100
        if self._synchronization_rate_200_checker.check(img):
            synchronization_rate = 200
        logger.debug(f"{self.resonator_name().value}-同步率: {synchronization_rate}点")
        return synchronization_rate

    def resonance_rate_count(self, img: np.ndarray) -> int:
        resonance_rate = 0
        if self._resonance_rate_1_checker.check(img):
            resonance_rate = 1
        if self._resonance_rate_2_checker.check(img):
            resonance_rate = 2
        if self._resonance_rate_3_checker.check(img):
            resonance_rate = 3
        if self._resonance_rate_4_checker.check(img):
            resonance_rate = 4
        logger.debug(f"{self.resonator_name().value}-共鸣率: {resonance_rate}点")
        return resonance_rate

    def is_heavy_attack_aemeath_ready(self, img: np.ndarray) -> bool:
        is_ready = self._heavy_attack_aemeath_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-重击·爱弥斯: {is_ready}")
        return is_ready

    def is_resonance_skill_form_switch_mech_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_form_switch_mech_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能 构型切换·机兵: {is_ready}")
        return is_ready

    def is_resonance_skill_sync_strike_armament_merge_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_sync_strike_armament_merge_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能 合击·突刺·兵装融合: {is_ready}")
        return is_ready

    def is_resonance_skill_seraphic_duet_overture_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_seraphic_duet_overture_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能 光翼共奏·降临: {is_ready}")
        return is_ready

    def is_heavy_attack_mech_ready(self, img: np.ndarray) -> bool:
        is_ready = self._heavy_attack_mech_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-重击·机兵: {is_ready}")
        return is_ready

    def is_resonance_skill_form_switch_aemeath_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_form_switch_aemeath_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能 构型切换·爱弥斯: {is_ready}")
        return is_ready

    def is_resonance_skill_sync_strike_call_of_dawn_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_sync_strike_call_of_dawn_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能 合击·突刺·启明之音: {is_ready}")
        return is_ready

    def is_resonance_skill_seraphic_duet_encore_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_seraphic_duet_encore_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能 光翼共奏·登台: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_heavenfall_edict_overdrive_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_heavenfall_edict_overdrive_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放 星辉破界而来·过载: {is_ready}")
        return is_ready

    def is_resonance_liberation_heavenfall_edict_finale_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_heavenfall_edict_finale_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放 星辉破界而来·终结: {is_ready}")
        return is_ready


class Aemeath(BaseAemeath):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)
        self._generic_combo = GenericCombo(control_service)

    def exit_special_state(self, morph: Morph) -> bool:
        logger.debug("exit_special_state")
        img = self.img_service.screenshot()
        is_resonance_skill_form_switch_aemeath_ready = self.is_resonance_skill_form_switch_aemeath_ready(img)
        is_resonance_skill_sync_strike_call_of_dawn_ready = self.is_resonance_skill_sync_strike_call_of_dawn_ready(img)
        is_resonance_skill_seraphic_duet_encore_ready = self.is_resonance_skill_seraphic_duet_encore_ready(img)
        is_resonance_liberation_heavenfall_edict_finale_ready = self.is_resonance_liberation_heavenfall_edict_finale_ready(img)

        quit_seq = None
        if is_resonance_skill_form_switch_aemeath_ready:
            quit_seq = [
                ["E", 0.05, 1.00],
            ]
        elif is_resonance_skill_sync_strike_call_of_dawn_ready:
            quit_seq = [
                ["E", 0.05, 2.00],
            ]
        elif is_resonance_skill_seraphic_duet_encore_ready:
            quit_seq = [
                ["E", 0.05, 4.00],
            ]
        elif is_resonance_liberation_heavenfall_edict_finale_ready:
            quit_seq = [
                ["R", 0.05, 6.00],
            ]
        if quit_seq:
            self.combo_action(quit_seq, True, ignore_event=True)
        return True

    def combo(self):

        # img = self.img_service.screenshot()
        # synchronization_rate_count = self.synchronization_rate_count(img)
        # resonance_rate_count = self.resonance_rate_count(img)
        # is_heavy_attack_aemeath_ready = self.is_heavy_attack_aemeath_ready(img)
        # is_resonance_skill_form_switch_mech_ready = self.is_resonance_skill_form_switch_mech_ready(img)
        # is_resonance_skill_sync_strike_armament_merge_ready = self.is_resonance_skill_sync_strike_armament_merge_ready(img)
        # is_resonance_skill_seraphic_duet_overture_ready = self.is_resonance_skill_seraphic_duet_overture_ready(img)
        # is_heavy_attack_mech_ready = self.is_heavy_attack_mech_ready(img)
        # is_resonance_skill_form_switch_aemeath_ready = self.is_resonance_skill_form_switch_aemeath_ready(img)
        # is_resonance_skill_sync_strike_call_of_dawn_ready = self.is_resonance_skill_sync_strike_call_of_dawn_ready(img)
        # is_resonance_skill_seraphic_duet_encore_ready = self.is_resonance_skill_seraphic_duet_encore_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        # is_resonance_liberation_heavenfall_edict_overdrive_ready = self.is_resonance_liberation_heavenfall_edict_overdrive_ready(img)
        # is_resonance_liberation_heavenfall_edict_finale_ready = self.is_resonance_liberation_heavenfall_edict_finale_ready(img)

        self._generic_combo.combo(self)
        self._generic_combo.combo(self)
