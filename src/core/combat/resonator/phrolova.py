import logging

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, LogicEnum, \
    Morph
from src.core.combat.resonator.generic import GenericCombo
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BasePhrolova(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁紫圈
        self._concerto_energy_checker = ColorChecker.concerto_havoc()

        # 弦乐
        self._volatile_note_strings_color = [(28, 14, 176), (26, 15, 134), (29, 19, 149)]  # BGR
        # 管乐
        self._volatile_note_winds_color = [(181, 28, 45), (138, 36, 52)]  # BGR
        # 彩乐
        self._volatile_note_cadenza_color = [(65, 53, 143), (59, 53, 102)]  # BGR
        # 乐声
        self._volatile_note_color = self._volatile_note_strings_color + self._volatile_note_winds_color + self._volatile_note_cadenza_color

        self._volatile_note1_point = [(577, 673), (577, 674)]
        self._volatile_note1_checker = ColorChecker(self._volatile_note1_point, self._volatile_note_color)

        self._volatile_note2_point = [(604, 668), (605, 669)]
        self._volatile_note2_checker = ColorChecker(self._volatile_note2_point, self._volatile_note_color)

        self._volatile_note3_point = [(632, 670), (632, 671)]
        self._volatile_note3_checker = ColorChecker(self._volatile_note3_point, self._volatile_note_color)

        self._volatile_note4_point = [(659, 671), (660, 672)]
        self._volatile_note4_checker = ColorChecker(self._volatile_note4_point, self._volatile_note_color)

        self._volatile_note5_point = [(687, 673), (687, 674)]
        self._volatile_note5_checker = ColorChecker(self._volatile_note5_point, self._volatile_note_color)

        self._volatile_note6_point = [(714, 671), (715, 672)]
        self._volatile_note6_checker = ColorChecker(self._volatile_note6_point, self._volatile_note_color)

        # 普攻·生与死的乐章
        self._basic_attack_point = [(941, 634), (943, 635), (936, 637), (968, 651)]
        self._basic_attack_color = [(255, 255, 255)]  # BGR
        self._basic_attack_checker = ColorChecker(
            self._basic_attack_point, self._basic_attack_color, logic=LogicEnum.AND)

        # 普攻·亡与死的乐章
        self._basic_attack_2_point = [(960, 641), (949, 646), (948, 647)]
        self._basic_attack_2_color = [(255, 255, 255)]  # BGR
        self._basic_attack_2_checker = ColorChecker(
            self._basic_attack_2_point, self._basic_attack_2_color, logic=LogicEnum.AND)

        # 共鸣技能·稍纵即逝的梦呓
        self._resonance_skill_point = [(1078, 635), (1078, 636), (1078, 637)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(
            self._resonance_skill_point, self._resonance_skill_color, logic=LogicEnum.AND)

        # 共鸣技能·永不消逝的梦呓
        self._resonance_skill_2_point = [(1084, 636), (1092, 637), (1093, 638)]
        self._resonance_skill_2_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_2_checker = ColorChecker(
            self._resonance_skill_2_point, self._resonance_skill_2_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1148, 653), (1149, 654), (1146, 660)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color, logic=LogicEnum.AND)

        # 共鸣解放
        self._resonance_liberation_point = [(1206, 640), (1213, 652)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color, logic=LogicEnum.AND)

        # 共鸣解放 指令·普攻
        self._cue_basic_attack_point = [(1132, 636), (1135, 637), (1154, 637), (1160, 651)]
        self._cue_basic_attack_color = [(255, 255, 255)]  # BGR
        self._cue_basic_attack_checker = ColorChecker(
            self._cue_basic_attack_point, self._cue_basic_attack_color, logic=LogicEnum.AND)

        ## 运行时参数
        # 上次释放定音的单调时间
        self._resolving_chord_monotonic_time = None
        self._resolving_chord_cd = 24  # 秒

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.phrolova

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def volatile_note_count(self, img: np.ndarray) -> int:
        volatile_note_count = 0
        if self._volatile_note1_checker.check(img):
            volatile_note_count = 1
        if volatile_note_count == 1 and self._volatile_note2_checker.check(img):
            volatile_note_count = 2
        if volatile_note_count == 2 and self._volatile_note3_checker.check(img):
            volatile_note_count = 3
        if volatile_note_count == 3 and self._volatile_note4_checker.check(img):
            volatile_note_count = 4
        if volatile_note_count == 4 and self._volatile_note5_checker.check(img):
            volatile_note_count = 5
        if volatile_note_count == 5 and self._volatile_note6_checker.check(img):
            volatile_note_count = 6
        logger.debug(f"{self.resonator_name().value}-乐声: {volatile_note_count}个")
        return volatile_note_count

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_basic_attack_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻: {is_ready}")
        return is_ready

    def is_basic_attack_2_ready(self, img: np.ndarray) -> bool:
        is_ready = self._basic_attack_2_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-普攻2: {is_ready}")
        return is_ready

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}")
        return is_ready

    def is_resonance_skill_2_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_2_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能2: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready

    def is_cue_curtain_call_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        is_ready &= self._cue_basic_attack_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放 指令·谢幕: {is_ready}")
        return is_ready


class Phrolova(BasePhrolova):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)
        self._generic_combo = GenericCombo(control_service)

    def exit_special_state(self, morph: Morph) -> bool:
        logger.debug("exit_special_state")
        img = self.img_service.screenshot()
        if not self.is_cue_curtain_call_ready(img):
            return True
        quit_seq = [
            # ["R", 0.05, 4.49],  # R升天
            ["R", 0.05, 2.40],  # R落地
        ]
        self.combo_action(quit_seq, True, ignore_event=True)
        return True

    def combo(self):
        self._generic_combo.combo(self)
