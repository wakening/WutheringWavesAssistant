import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, ResonatorNameEnum, \
    combat_cache, Morph
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseCartethyia(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁绿圈
        self._concerto_energy_checker = ColorChecker.concerto_aero()

        ### 常态 小卡技能

        # 共鸣技能 E 卡提希娅
        self._resonance_skill_cartethyia_point = [(1082, 635)]
        self._resonance_skill_cartethyia_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_cartethyia_checker = ColorChecker(
            self._resonance_skill_cartethyia_point, self._resonance_skill_cartethyia_color,
            logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1148, 653), (1148, 654)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放 R 听骑士从心祈愿
        self._resonance_liberation_point = [(1200, 654), (1205, 660), (1213, 661), (1218, 654)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color, logic=LogicEnum.AND)

        ### 大卡技能

        # 共鸣技能 E1 芙露德莉斯 此剑为潮浪之意
        self._resonance_skill_fleurdelys_point = [(1083, 625), (1075, 656), (1089, 656)]
        self._resonance_skill_fleurdelys_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_fleurdelys_checker = ColorChecker(
            self._resonance_skill_fleurdelys_point, self._resonance_skill_fleurdelys_color,
            logic=LogicEnum.AND)

        # 共鸣技能 E2 芙露德莉斯 凭风斩浪破敌
        self._resonance_skill_fleurdelys_2_point = [(1088, 653), (1091, 659), (1092, 661)]
        self._resonance_skill_fleurdelys_2_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_fleurdelys_2_checker = ColorChecker(
            self._resonance_skill_fleurdelys_2_point, self._resonance_skill_fleurdelys_2_color,
            logic=LogicEnum.AND)

        # 化身显示的是当前形态，切换有1.5秒冷却

        # 共鸣解放 R 化身·芙露德莉斯
        self._resonance_liberation_avatar_fleurdelys_point = [(1209, 631), (1210, 660), (1210, 662), (1197, 639)]
        self._resonance_liberation_avatar_fleurdelys_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_avatar_fleurdelys_checker = ColorChecker(
            self._resonance_liberation_avatar_fleurdelys_point, self._resonance_liberation_avatar_fleurdelys_color,
            logic=LogicEnum.AND)

        # 共鸣解放 R 化身·卡提希娅
        self._resonance_liberation_avatar_cartethyia_point = [(1210, 658), (1206, 658), (1196, 657)]
        self._resonance_liberation_avatar_cartethyia_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_avatar_cartethyia_checker = ColorChecker(
            self._resonance_liberation_avatar_cartethyia_point, self._resonance_liberation_avatar_cartethyia_color,
            logic=LogicEnum.AND)

        # 共鸣解放 R 看潮怒风哮之刃
        self._resonance_liberation_blade_of_howling_squall_point = [(1203, 641), (1209, 636), (1213, 643), (1199, 636)]
        self._resonance_liberation_blade_of_howling_squall_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_blade_of_howling_squall_checker = ColorChecker(
            self._resonance_liberation_blade_of_howling_squall_point,
            self._resonance_liberation_blade_of_howling_squall_color,
            logic=LogicEnum.AND)

        ### 状态识别

        # 剑一 重击 异权剑
        self._sword_of_discord_point = [(567, 663), (575, 663)]
        self._sword_of_discord_color = [(255, 255, 255)]  # BGR
        self._sword_of_discord_checker = ColorChecker(
            self._sword_of_discord_point, self._sword_of_discord_color, logic=LogicEnum.AND)

        # 剑二 普攻 神权剑
        self._sword_of_divinity_point = [(634, 663), (633, 663), (627, 667), (640, 667)]
        self._sword_of_divinity_color = [(255, 255, 255), (189, 194, 119), (106, 122, 50)]  # BGR
        self._sword_of_divinity_checker = ColorChecker(
            self._sword_of_divinity_point, self._sword_of_divinity_color)

        # 剑三 E   人权剑
        self._sword_of_virtue_point = [(692, 658), (701, 658), (690, 667), (703, 667)]
        self._sword_of_virtue_color = [(255, 255, 255), (147, 79, 67)]  # BGR
        self._sword_of_virtue_checker = ColorChecker(
            self._sword_of_virtue_point, self._sword_of_virtue_color)

        # 显化
        self._manifest_point = [(620, 679), (648, 679)]
        self._manifest_color = [(255, 255, 255)]  # BGR
        self._manifest_checker = ColorChecker(self._manifest_point, self._manifest_color,
                                              logic=LogicEnum.AND)
        # 决意 大卡血条上方能量条 仅大卡可见
        self._conviction_point = [(543, 668), (544, 668)]
        self._conviction_color = [
            (170, 161, 160),  # 灰色空能量
            (251, 187, 114),  # 蓝色能量未全满
            (255, 241, 135), (255, 254, 165), (242, 201, 117),  # 绿色满能量
        ]  # BGR
        self._conviction_checker = ColorChecker(self._conviction_point, self._conviction_color)

        ### 运行时动态变量

        # 化身·卡提希娅是否打过一套攻击，没打过就打一套，打过则变身
        self.is_avatar_cartethyia_attack_done = False

    def __str__(self):
        return self.resonator_name().value

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.cartethyia

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_resonance_skill_cartethyia_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_cartethyia_checker.check(img)
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

    def is_resonance_skill_fleurdelys_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_fleurdelys_checker.check(img)
        logger.debug(f"芙露德莉斯-共鸣技能 E1: {is_ready}")
        return is_ready

    def is_resonance_skill_fleurdelys_2_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_fleurdelys_2_checker.check(img)
        logger.debug(f"芙露德莉斯-共鸣技能 E2: {is_ready}")
        return is_ready

    def is_resonance_liberation_avatar_fleurdelys_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_avatar_fleurdelys_checker.check(img)
        logger.debug(f"芙露德莉斯-共鸣解放 R: {is_ready}")
        return is_ready

    def is_resonance_liberation_avatar_cartethyia_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_avatar_cartethyia_checker.check(img)
        logger.debug(f"化身·{self.resonator_name().value}-共鸣解放 R: {is_ready}")
        return is_ready

    def is_resonance_liberation_blade_of_howling_squall_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_blade_of_howling_squall_checker.check(img)
        logger.debug(f"芙露德莉斯-共鸣解放 R 看潮怒风哮之刃: {is_ready}")
        return is_ready

    def is_sword_of_discord_existing(self, img: np.ndarray) -> bool:
        is_existing = self._sword_of_discord_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-剑一 异权剑: {is_existing}")
        return is_existing

    def is_sword_of_divinity_existing(self, img: np.ndarray) -> bool:
        is_existing = self._sword_of_divinity_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-剑二 神权剑: {is_existing}")
        return is_existing

    def is_sword_of_virtue_existing(self, img: np.ndarray) -> bool:
        is_existing = self._sword_of_virtue_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-剑三 人权剑: {is_existing}")
        return is_existing

    def is_manifest_existing(self, img: np.ndarray) -> bool:
        is_existing = self._manifest_checker.check(img)
        logger.debug(f"芙露德莉斯-显化: {is_existing}")
        return is_existing

    def is_conviction_existing(self, img: np.ndarray) -> bool:
        is_existing = self._conviction_checker.check(img)
        logger.debug(f"芙露德莉斯-决意条: {is_existing}")
        return is_existing


class Cartethyia(BaseCartethyia):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 小卡
        # 普攻4a 召唤神权剑
        ["a", 0.05, 0.31],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        ["a", 0.05, 1.20],
        ["j", 0.05, 1.20],

        # 重击 召唤异权剑
        ["z", 0.90, 0.60],
        ["j", 0.05, 1.20],

        # Eza
        ["E", 0.05, 0.60],
        ["z", 0.90, 0.20],
        ["a", 0.05, 1.00],
        ["j", 0.05, 1.20],

        # Ea 召唤人权剑 收剑
        ["E", 0.05, 1.00],
        ["a", 0.05, 0.92],
        ["j", 0.05, 1.20],

        # 下落攻击 收剑
        ["j", 0.05, 0.24],
        ["a", 0.05, 0.80],
        ["j", 0.05, 1.20],

        # R
        ["R", 0.05, 4.00],
        ["j", 0.05, 1.20],
        ["w", 0.00, 1.20],

        # 大卡
        # 普攻5a
        ["a", 0.05, 0.32],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["a", 0.05, 0.90],
        ["j", 0.05, 1.20],
        ["w", 0.00, 1.20],

        # EaaEaaa
        ["E", 0.05, 0.93],
        ["a", 0.05, 0.68],
        ["a", 0.05, 1.20],
        ["E", 0.05, 1.65],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["a", 0.05, 0.90],
        ["j", 0.05, 1.20],
        ["w", 0.00, 1.20],

        # R
        # ["R", 0.05, 7.20],
        ["R", 0.05, 9.40],
        ["w", 0.05, 1.20],

        ["j", 0.05, 0.80],
        ["a", 0.05, 0.61],
        ["a", 0.05, 1.20],
        ["a", 0.05, 0.61],
        ["j", 0.05, 1.20],
    ]

    # 轴1
    COMBO_SEQ_1 = [
        # 小卡

        # 先打一套三剑下劈

        # 普攻4a
        ["a", 0.05, 0.31],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        # ["a", 0.05, 1.20],
        ["a", 0.05, 0.70],

        ["z", 0.70, 0.50],

        ["E", 0.05, 1.00],
        ["a", 0.05, 1.10],

        # R
        ["R", 0.05, 3.60],

        # 变大卡
        # 普攻5a
        # ["a", 0.05, 0.32],
        ["a", 0.05, 0.10],
        ["a", 0.05, 0.20],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["a", 0.05, 0.90],

        # EaaEaaa
        ["E", 0.05, 0.93],
        ["a", 0.05, 0.68],
        ["a", 0.05, 1.20],
        # ["E", 0.05, 1.65],
        ["E", 0.05, 1.10],

        # 切小卡

        ["R", 0.05, 1.10],

        # 再打一套三剑下劈

        # 普攻4a 大卡切化身小卡从第二段普攻开始打
        # ["a", 0.05, 0.33],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        # ["a", 0.05, 1.20],
        ["a", 0.05, 0.70],

        ["z", 0.70, 0.50],

        ["E", 0.05, 1.00],
        ["a", 0.05, 1.10],

        # 切大卡
        ["R", 0.05, 0.65],

        # 普攻5a 化身卡提希娅切回芙露德莉斯从普攻第三段开始打
        # ["a", 0.05, 0.32],
        # ["a", 0.05, 0.65],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["a", 0.05, 0.90],

        # R
        # ["R", 0.05, 7.20],
        ["R", 0.05, 9.40],
        ["w", 0.05, 1.20],
    ]

    # 轴2
    COMBO_SEQ_2 = [
        # 小卡
        # R
        ["R", 0.05, 3.60],

        # 切小卡
        ["w", 0.00, 0.20],
        ["R", 0.05, 1.10],

        # 再打一套三剑下劈

        # 普攻4a 大卡切化身小卡从第二段普攻开始打
        # ["a", 0.05, 0.33],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        # ["a", 0.05, 1.20],
        ["a", 0.05, 0.70],

        ["z", 0.70, 0.50],

        ["E", 0.05, 1.00],
        ["a", 0.05, 1.10],

        # 切大卡
        ["R", 0.05, 0.65],

        # 普攻5a 化身卡提希娅切回芙露德莉斯从普攻第三段开始打
        # ["a", 0.05, 0.32],
        # ["a", 0.05, 0.65],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["a", 0.05, 0.90],

        # EaaEaaa
        ["E", 0.05, 0.93],
        ["a", 0.05, 0.68],
        ["a", 0.05, 1.20],
        ["E", 0.05, 1.65],
        ["a", 0.05, 0.82],
        ["a", 0.05, 1.02],
        ["a", 0.05, 0.90],

        # R
        ["R", 0.05, 5.20],

        # 普攻4a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        # ["a", 0.05, 1.20],
        ["a", 0.05, 0.70],

        ["z", 0.70, 0.50],

        ["E", 0.05, 1.00],
        ["a", 0.05, 1.10],

        # 普攻4a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        # ["a", 0.05, 1.20],
        ["a", 0.05, 0.70],
        ["w", 0.00, 1.20],

        # 普攻4a
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.84],
        # ["a", 0.05, 1.20],
        ["a", 0.05, 0.70],
        ["w", 0.00, 1.20],

    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def cartethyia_a4(self):
        return [
            # 小卡
            # 普攻4a 召唤神权剑
            # ["a", 0.05, 0.31],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.16],

            # ["a", 0.05, 0.67],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.32],

            # ["a", 0.05, 0.84],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.20],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["w", 0.00, 0.75],
        ]

    @combat_cache
    def a3(self):
        return [
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
        ]

    @combat_cache
    def cartethyia_a2_start(self):
        return [
            # 普攻前两下
            # ["a", 0.05, 0.31],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.16],

            # ["a", 0.05, 0.67],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.32],
        ]

    @combat_cache
    def cartethyia_a2_end(self):
        return [
            # 普攻后两下
            # ["a", 0.05, 0.84],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.20],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["w", 0.00, 0.75],
        ]

    @combat_cache
    def cartethyia_a4Eza(self):
        return [
            # 小卡
            # 普攻4a
            # 小卡
            # 普攻4a 召唤神权剑
            # ["a", 0.05, 0.31],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.16],

            # ["a", 0.05, 0.67],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.32],

            # ["a", 0.05, 0.84],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            ## ["a", 0.05, 1.20],
            # ["a", 0.05, 0.90],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["w", 0.00, 0.45],

            # # Eza
            # # ["E", 0.05, 0.60],
            # ["E", 0.05, 0.20],
            # ["E", 0.05, 0.45],
            #
            # ["z", 0.90, 0.20],
            # # ["a", 0.05, 1.00],
            # ["a", 0.05, 0.15],
            # ["a", 0.05, 0.15],
            # ["w", 0.00, 0.65],

            # Eza
            # ["E", 0.05, 0.60],
            # ["z", 0.90, 0.20],
            # ["a", 0.05, 1.00],
            ["E", 0.05, 0.15],
            ["E", 0.05, 0.15],
            ["z", 1.30, 0.05],
            ["a", 0.05, 0.05],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.65],
        ]

    @combat_cache
    def cartethyia_E(self):
        return [
            # E 召唤人权剑
            ["E", 0.05, 1.00],
        ]

    @combat_cache
    def cartethyia_Ea(self):
        return [
            # Ea 召唤人权剑 收剑
            # ["E", 0.05, 1.00],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.75],

            # ["a", 0.05, 1.10],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.75],
        ]

    @combat_cache
    def cartethyia_zjEda(self):
        return [
            # zEa
            # ["z", 0.90, 0.20],
            ["z", 0.75, 0.25],
            ["j", 0.05, 0.05],
            # ["E", 0.05, 0.60],
            ["E", 0.05, 0.10],
            ["E", 0.05, 0.50],
            ["d", 0.05, 0.00],
            # ["a", 0.05, 1.00],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.10],
            ["w", 0.00, 0.65],
        ]

    @combat_cache
    def cartethyia_Eza(self):
        return [
            # Eza
            # ["E", 0.05, 0.60],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.45],

            ["z", 0.90, 0.20],
            # ["a", 0.05, 1.00],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.65],
        ]

    @combat_cache
    def cartethyia_z(self):
        return [
            # 重击 召唤异权剑
            # ["z", 0.90, 0.60],
            ["z", 0.90, 0.20],
            ["w", 0.00, 0.40],
        ]

    @combat_cache
    def cartethyia_ja(self):
        return [
            # 下落攻击 收剑
            ["j", 0.05, 0.20],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.20],
            ["w", 0.00, 0.40],
        ]

    @combat_cache
    def cartethyia_R(self):
        return [
            ["R", 0.05, 3.70],
        ]

    @combat_cache
    def fleurdelys_a5(self):
        return [
            # 大卡
            # 普攻5a
            # ["a", 0.05, 0.32],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],

            # ["a", 0.05, 0.82],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 1.02],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.22],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.90],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def fleurdelys_a2(self):
        return [
            # 大卡
            # 普攻5a
            # ["a", 0.05, 0.32],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],

            # # ["a", 0.05, 0.82],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.27],
            # ["a", 0.05, 0.30],
            #
            # # ["a", 0.05, 1.02],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.22],
            # ["a", 0.05, 0.25],
            #
            # # ["a", 0.05, 0.90],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.30],
        ]

    @combat_cache
    def fleurdelys_a3(self):
        return [
            # 大卡
            # 普攻5a
            # ["a", 0.05, 0.32],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],

            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            # # ["a", 0.05, 1.02],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.22],
            # ["a", 0.05, 0.25],
            #
            # # ["a", 0.05, 0.90],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.25],
            # ["a", 0.05, 0.30],
        ]

    @combat_cache
    def avatar_cartethyia_to_fleurdelys_Ra3(self):
        return [
            # 化身小卡切大卡
            # ["R", 0.05, 0.65],
            ["R", 0.05, 0.10],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            # 普攻5a 化身卡提希娅切回芙露德莉斯从普攻第三段开始打
            # ["a", 0.05, 0.32],
            # ["a", 0.05, 0.65],

            # ["a", 0.05, 0.82],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 1.02],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.22],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.90],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def fleurdelys_to_avatar_cartethyia_Ra3(self):
        return [
            # 大卡切化身小卡
            # ["R", 0.05, 1.10],
            ["R", 0.05, 0.20],

            # 普攻4a 大卡切化身小卡从第二段普攻开始打
            # ["a", 0.05, 0.36],

            # ["a", 0.05, 0.67],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.27],

            # ["a", 0.05, 0.84],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.20],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["w", 0.00, 0.75],
        ]

    @combat_cache
    def fleurdelys_za_a3(self):
        return [
            # 大卡 重击派生
            # za 射箭
            ["z", 0.90, 0.31],
            # ["a", 0.05, 0.93],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.28],
            ["a", 0.05, 0.30],

            # 普攻起飞
            # ["a", 0.05, 0.50],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            # 空中2a
            # ["a", 0.05, 0.68],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.33],
            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.85],
        ]

    @combat_cache
    def fleurdelys_ja2(self):
        return [
            # 大卡 空中2a
            # ["j", 0.05, 0.80],
            ["j", 0.05, 0.20],
            ["j", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],

            # ["a", 0.05, 0.68],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.33],

            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.85],
        ]

    @combat_cache
    def fleurdelys_ja3(self):
        return [
            # 大卡 空中3a
            # ["j", 0.05, 0.80],
            ["j", 0.05, 0.20],
            ["j", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],

            # ["a", 0.05, 0.68],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.33],

            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.85],

            # ["a", 0.05, 0.61],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["w", 0.00, 0.31],
        ]

    @combat_cache
    def fleurdelys_EaaEaaa(self):
        return [
            # 大卡
            # EaaEaaa
            # ["E", 0.05, 0.93],
            ["E", 0.05, 0.13],
            ["E", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.68],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.33],

            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],
            ["E", 0.05, 0.30],

            # ["E", 0.05, 1.65],
            ["E", 0.05, 0.30],
            ["E", 0.05, 0.30],
            ["E", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.82],
            ["a", 0.05, 0.22],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.02],
            ["a", 0.05, 0.17],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 0.90],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def fleurdelys_EaaE(self):
        return [
            # 大卡
            # EaaE
            # ["E", 0.05, 0.93],
            ["E", 0.05, 0.13],
            ["E", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.68],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.33],

            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],
            ["E", 0.05, 0.20],

            # ["E", 0.05, 1.65],
            ["E", 0.05, 0.10],
            ["E", 0.05, 0.20],
            ["a", 0.05, 1.45],
        ]

    @combat_cache
    def fleurdelys_R(self):
        return [
            # ["R", 0.05, 3.60],
            ["R", 0.05, 0.20],
            ["R", 0.05, 3.35],
        ]

    @combat_cache
    def Q(self):
        logger.debug("Q")
        return [
            # 声骸技能
            ["Q", 0.01, 0.00],
        ]

    @combat_cache
    def avatar_R(self):
        # 大小卡切换，大招期间
        return [
            ["R", 0.05, 0.05],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def exit_special_state(self, morph: Morph) -> bool:
        logger.debug("exit_special_state")

        img = self.img_service.screenshot()
        # 常态 小卡技能
        is_resonance_skill_cartethyia_ready = self.is_resonance_skill_cartethyia_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        # 大卡技能
        is_resonance_liberation_avatar_cartethyia_ready = self.is_resonance_liberation_avatar_cartethyia_ready(img)

        # 常态 卡提希娅
        if is_resonance_skill_cartethyia_ready or is_resonance_liberation_ready:
            return True
        # 化身·卡提希娅
        if is_resonance_liberation_avatar_cartethyia_ready:
            return True
        return False

    def combo(self):
        # 变奏后摇1.2s
        # 空中切人，附近有怪，自动打下落攻击，后摇0.8s，没人则在地面
        # 地面切人，附近有怪，自动打普攻第二段

        # 风蚀效应持续16s，超时清空
        # 普攻第四段叠一层
        # E技能叠两层
        # 变奏叠两层

        self.combo_action(self.a3(), False)

        img = self.img_service.screenshot()
        # 常态 小卡技能
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_cartethyia_ready = self.is_resonance_skill_cartethyia_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        # 大卡技能
        is_resonance_skill_fleurdelys_ready = self.is_resonance_skill_fleurdelys_ready(img)
        # is_resonance_skill_fleurdelys_2_ready = self.is_resonance_skill_fleurdelys_2_ready(img)
        is_resonance_liberation_avatar_fleurdelys_ready = self.is_resonance_liberation_avatar_fleurdelys_ready(img)
        is_resonance_liberation_avatar_cartethyia_ready = self.is_resonance_liberation_avatar_cartethyia_ready(img)
        is_resonance_liberation_blade_of_howling_squall_ready = self.is_resonance_liberation_blade_of_howling_squall_ready(
            img)
        # 状态
        is_sword_of_discord_existing = self.is_sword_of_discord_existing(img)
        is_sword_of_divinity_existing = self.is_sword_of_divinity_existing(img)
        is_sword_of_virtue_existing = self.is_sword_of_virtue_existing(img)
        # is_manifest_existing = self.is_manifest_existing(img)
        # is_conviction_existing = self.is_conviction_existing(img)

        boss_hp = self.boss_hp(img)

        # 化身·芙露德莉斯 狂澜，分割天地
        if is_resonance_liberation_blade_of_howling_squall_ready:
            # 有大开大
            self.combo_action(self.fleurdelys_R(), True)
            img = self.img_service.screenshot()
            boss_hp = self.boss_hp(img)
            if boss_hp <= 0.01:
                return
            # 小卡三剑
            is_resonance_skill_cartethyia_ready = self.is_resonance_skill_cartethyia_ready(img)
            if is_resonance_skill_cartethyia_ready:
                self.combo_action(self.Q(), False)
                self.combo_action(self.cartethyia_a4(), False)
                time.sleep(0.15)
                boss_hp = self.boss_hp(img)
                if boss_hp <= 0.01:
                    return
                time.sleep(0.15)
                self.combo_action(self.cartethyia_zjEda(), False)
            return

        self.combo_action(self.Q(), False)

        # 化身·卡提希娅
        avatar_cartethyia_to_fleurdelys = False
        if is_resonance_liberation_avatar_cartethyia_ready:
            # 打一套三剑下劈
            if is_resonance_skill_cartethyia_ready:
                self.combo_action(self.cartethyia_a4(), False)
                time.sleep(0.15)
                img = self.img_service.screenshot()
                boss_hp = self.boss_hp(img)
                if boss_hp <= 0.01:
                    return
                time.sleep(0.15)
                self.combo_action(self.cartethyia_zjEda(), self.is_avatar_cartethyia_attack_done)
            else:
                self.combo_action(self.cartethyia_a4(), self.is_avatar_cartethyia_attack_done)
            if boss_hp <= 0.01:
                return
            # 合轴
            if not self.is_avatar_cartethyia_attack_done:
                self.is_avatar_cartethyia_attack_done = True
                time.sleep(0.2)
                return
            # 再来就标记需改变状态切换化身
            avatar_cartethyia_to_fleurdelys = True

        # 化身·芙露德莉斯 决意未满 或 需切换成 化身·芙露德莉斯
        if is_resonance_liberation_avatar_fleurdelys_ready or avatar_cartethyia_to_fleurdelys:
            if avatar_cartethyia_to_fleurdelys:
                self.is_avatar_cartethyia_attack_done = False
                if self.random_float() < 0.5:
                    self.combo_action(self.avatar_cartethyia_to_fleurdelys_Ra3(), False)
                    img = self.img_service.screenshot()
                    boss_hp = self.boss_hp(img)
                    if boss_hp <= 0.01:
                        return
                else:
                    self.combo_action(self.avatar_R(), True)
                self.combo_action(self.fleurdelys_EaaE(), False)
            elif is_resonance_skill_fleurdelys_ready:
                self.combo_action(self.fleurdelys_EaaE(), False)
            else:
                if boss_hp <= 0.01:
                    self.combo_action(self.fleurdelys_a3(), False)
                    return
                if self.random_float() < 0.33:
                    self.combo_action(self.fleurdelys_a5(), False)
                else:
                    self.combo_action(self.fleurdelys_ja3(), False)

            # 检查E、R状态，有E打空中连，没有打普攻，补决意
            img = self.img_service.screenshot()
            boss_hp = self.boss_hp(img)
            if boss_hp <= 0.01:
                return
            is_resonance_liberation_blade_of_howling_squall_ready = self.is_resonance_liberation_blade_of_howling_squall_ready(
                img)

            # 此剑，斩灭诸恶
            if is_resonance_liberation_blade_of_howling_squall_ready:
                self.combo_action(self.fleurdelys_R(), True)
                # 若小卡E转好了再打一个 E合轴 或 三剑下劈
                img = self.img_service.screenshot()
                boss_hp = self.boss_hp(img)
                if boss_hp <= 0.01:
                    return
                is_resonance_skill_cartethyia_ready = self.is_resonance_skill_cartethyia_ready(img)
                if is_resonance_skill_cartethyia_ready:
                    if self.random_float() < 0.5:
                        self.combo_action(self.cartethyia_E(), False)
                        time.sleep(0.2)
                    else:
                        self.combo_action(self.cartethyia_a4(), False)
                        time.sleep(0.3)
                        self.combo_action(self.cartethyia_zjEda(), True)
                        time.sleep(0.2)
            return

        # 常态 卡提希娅
        if is_resonance_skill_cartethyia_ready or is_resonance_liberation_ready:
            need_cartethyia_ja = False
            is_cartethyia_a4_attack_done = False
            # 有大，补满三剑
            if is_resonance_liberation_ready:
                is_cartethyia_a4_attack_done = True
                if not is_sword_of_divinity_existing:
                    self.combo_action(self.cartethyia_a4(), False)
                if not is_sword_of_virtue_existing and is_resonance_skill_cartethyia_ready:
                    self.combo_action(self.cartethyia_zjEda(), True)
                elif not is_sword_of_discord_existing:
                    self.combo_action(self.cartethyia_z(), True)
                    self.combo_action(self.cartethyia_ja(), True)
            else:  # 没大，打一套普攻连
                if not is_sword_of_divinity_existing:
                    self.combo_action(self.cartethyia_a4(), False)
                    is_cartethyia_a4_attack_done = True

                img = self.img_service.screenshot()
                boss_hp = self.boss_hp(img)
                if boss_hp <= 0.01:
                    return
                is_resonance_skill_cartethyia_ready = self.is_resonance_skill_cartethyia_ready(img)
                # 检查E 收剑
                if is_resonance_skill_cartethyia_ready:
                    self.combo_action(self.cartethyia_zjEda(), True)
                else:
                    if not is_sword_of_discord_existing:
                        self.combo_action(self.cartethyia_z(), False)
                    need_cartethyia_ja = True  # 先记录状态，有大才收剑

            # 检查大招
            img = self.img_service.screenshot()
            boss_hp = self.boss_hp(img)
            if boss_hp <= 0.01:
                return
            is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)

            self.combo_action(self.Q(), False)

            # 大招还没好，结束
            if not is_resonance_liberation_ready:
                # 来都来了，什么技能都没有，就打一套普通吧
                if not is_cartethyia_a4_attack_done:
                    self.combo_action(self.cartethyia_a4(), False)
                return
            elif need_cartethyia_ja:
                self.combo_action(self.cartethyia_ja(), False)

            # 真容，于此展露
            self.combo_action(self.cartethyia_R(), True)

            # 显化爆发
            img = self.img_service.screenshot()
            is_resonance_skill_fleurdelys_ready = self.is_resonance_skill_fleurdelys_ready(img)
            if is_resonance_skill_fleurdelys_ready:
                self.combo_action(self.fleurdelys_EaaE(), False)
            else:
                self.combo_action(self.fleurdelys_ja3(), False)
            if self.random_float() < 0.5:
                # 切回小卡，保留显化
                self.combo_action(self.avatar_R(), True)
            return

        # 兜底
        self.combo_action(self.cartethyia_a4(), False)
