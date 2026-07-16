import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, ResonatorNameEnum, \
    Morph, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseCamellya(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁黄圈
        self._concerto_energy_checker = ColorChecker.concerto_havoc()

        # 能量 一格 血条上方的能量
        self._energy1_point = [(543, 668), (544, 668)]
        self._energy1_color = [(135, 66, 255), (131, 48, 255)]  # BGR
        self._energy1_checker = ColorChecker(self._energy1_point, self._energy1_color)

        # 能量 满格 血条上方的能量
        self._energy_full_point = [(724, 668), (725, 668)]
        self._energy_full_color = self._energy1_color
        self._energy_full_checker = ColorChecker(self._energy_full_point, self._energy_full_color)

        # 共鸣技能 E 红椿盛绽 进入盛绽状态
        self._resonance_skill_crimson_blossom_point = [(1088, 652)]
        self._resonance_skill_crimson_blossom_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_crimson_blossom_checker = ColorChecker(
            self._resonance_skill_crimson_blossom_point, self._resonance_skill_crimson_blossom_color,
            logic=LogicEnum.AND)

        # 共鸣技能 E 黯蕊猎心 退出盛绽状态
        self._resonance_skill_floral_ravage_point = [(1075, 652), (1078, 652)]
        self._resonance_skill_floral_ravage_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_floral_ravage_checker = ColorChecker(
            self._resonance_skill_floral_ravage_point, self._resonance_skill_floral_ravage_color,
            logic=LogicEnum.AND)

        # 共鸣技能 E 一日花
        self._resonance_skill_ephemeral_point = [(1087, 636), (1089, 634)]
        self._resonance_skill_ephemeral_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_ephemeral_checker = ColorChecker(
            self._resonance_skill_ephemeral_point,
            self._resonance_skill_ephemeral_color,
            logic=LogicEnum.AND
        )

        # 共鸣技能 E 一日花 入场粉紫色
        self._resonance_skill_ephemeral_incoming_color = [(153, 66, 212)]  # BGR
        self._resonance_skill_ephemeral_incoming_checker = ColorChecker(
            self._resonance_skill_ephemeral_point,
            self._resonance_skill_ephemeral_incoming_color,
            logic=LogicEnum.AND
        )

        # 声骸技能
        self._echo_skill_point = [(1136, 655), (1139, 653)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1209, 628), (1200, 658), (1219, 658)]
        self._resonance_liberation_color = [(255, 255, 255), (153, 66, 212)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.camellya

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def energy_count(self, img: np.ndarray) -> int:
        energy_count = 0
        if self._energy_full_checker.check(img):
            energy_count = 1
            logger.debug(f"{self.resonator_name().value}-能量: 已满")
        else:
            logger.debug(f"{self.resonator_name().value}-能量: 未满")
        return energy_count

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_resonance_skill_crimson_blossom_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_crimson_blossom_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能-红椿盛绽: {is_ready}")
        return is_ready

    def is_resonance_skill_floral_ravage_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_floral_ravage_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能-黯蕊猎心: {is_ready}")
        return is_ready

    def is_resonance_skill_ephemeral_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_ephemeral_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能-一日花: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready


class Camellya(BaseCamellya):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 白椿 普攻4a
        ["a", 0.05, 0.29],
        ["a", 0.05, 0.46],
        ["a", 0.05, 1.00],
        ["a", 0.05, 2.00],
        ["j", 0.05, 1.20],

        # 白椿 普攻3az 转圈派生
        ["a", 0.05, 0.29],
        ["a", 0.05, 0.46],
        ["a", 0.05, 1.00],
        ["z", 3.50, 0.41],
        ["j", 0.05, 1.20],

        # 白椿 重击
        ["z", 2.50, 1.40],
        ["j", 0.05, 1.20],

        # 白椿 重击 转圈派生
        ["z", 4.78, 0.80],
        ["j", 0.05, 1.20],

        # 一日花 Ea 下砸落地
        ["E", 0.05, 1.40],
        ["a", 0.05, 1.00],
        ["j", 0.05, 1.20],

        # 白椿转红椿 普攻重击转圈 下砸落地 消耗【红椿·蕊】
        ["E", 0.05, 1.25],
        ["a", 0.05, 0.85],
        ["a", 0.05, 0.69],
        ["z", 3.55, 0.35],
        ["j", 0.05, 0.93],
        ["a", 0.05, 1.28],
        ["j", 0.05, 1.20],

        # 白椿转红椿 重击转圈 下砸落地 消耗【红椿·蕊】
        ["E", 0.05, 0.50],
        ["z", 5.35, 0.50],
        ["j", 0.05, 1.01],
        ["a", 0.05, 1.20],
        ["j", 0.05, 1.20],

        # R
        ["R", 0.05, 4.06],
        ["j", 0.05, 1.20],

    ]

    # 进阶轴
    COMBO_SEQ_1 = [
        # 白椿Q闪取消转红椿 重击转圈 三连鞭
        ["E", 0.05, 0.27],
        ["Q", 0.05, 0.20],
        ["d", 0.05, 0.25],
        ["z", 5.00, 0.34],
        ["j", 0.05, 1.05],
        ["E", 0.05, 1.25],
        ["j", 0.05, 1.20],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a4(self):
        return [
            # 白椿 普攻4a
            ["a", 0.05, 0.29],

            # ["a", 0.05, 0.46],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.21],

            # ["a", 0.05, 1.00],  # 拆分
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            ["a", 0.05, 2.00],
        ]

    @combat_cache
    def a3(self):
        return [
            # 随便打几下普攻，入场防变奏
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
        ]

    @combat_cache
    def waz(self):
        # 从a2继续往后打
        return [
            # 白椿 普攻3az 转圈派生
            # ["a", 0.05, 0.29],
            # ["a", 0.05, 0.46],
            ["w", 0.00, 0.20],
            # ["a", 0.05, 1.00],  # 拆分
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            # ["a", 0.05, 0.30],

            # ["a", 0.05, 0.30],

            ["z", 3.50, 0.41],
        ]

    @combat_cache
    def a3z(self):
        return [
            # 白椿 普攻3az 转圈派生
            ["a", 0.05, 0.29],

            # ["a", 0.05, 0.46],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.21],

            # ["a", 0.05, 1.00],  # 拆分
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            ["z", 3.50, 0.41],
        ]

    @combat_cache
    def z(self):
        return [
            # 白椿 重击 转圈派生
            ["z", 4.78, 0.80],
        ]

    @combat_cache
    def EQdzjE(self):
        return [
            # 白椿Q闪取消转红椿 重击转圈 三连鞭
            ["E", 0.05, 0.27],
            ["Q", 0.05, 0.20],
            ["W_down", 0.00, 0.00],
            ["d", 0.05, 0.25],
            ["W_up", 0.00, 0.00],
            # ["z", 5.00, 0.34],
            ["z", 5.00, 0.20],
            ["j", 0.05, 1.05],

            # ["E", 0.05, 1.25],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.20],
            ["w", 0.05, 1.20],
        ]

    @combat_cache
    def QdEj(self):
        return [
            # 红椿Q闪取消转白椿 落地
            ["Q", 0.05, 0.20],
            ["W_down", 0.00, 0.00],
            ["d", 0.05, 0.25],
            ["W_up", 0.00, 0.00],
            ["E", 0.05, 0.27],
            ["j", 0.05, 0.05],
            ["w", 0.00, 1.00],
        ]

    @combat_cache
    def Eaazja(self):
        return [
            # 白椿转红椿 普攻重击转圈 下砸落地 消耗【红椿·蕊】
            # ["E", 0.05, 1.25],  # 拆分
            ["E", 0.05, 0.2],
            ["E", 0.05, 0.3],
            ["E", 0.05, 0.3],
            ["a", 0.05, 0.3],

            # ["a", 0.05, 0.85],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.69],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            ["z", 3.55, 0.35],
            # ["j", 0.05, 0.93],  # 拆分
            ["j", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.18],

            # ["a", 0.05, 1.28],
            ["a", 0.05, 0.10],  # 冗余，多打几个a
            ["a", 0.05, 0.10],
            ["a", 0.05, 1.00],
        ]

    @combat_cache
    def aazja(self):
        return [
            # # 白椿转红椿 普攻重击转圈 下砸落地 消耗【红椿·蕊】
            # # ["E", 0.05, 1.25],  # 拆分
            # ["E", 0.05, 0.2],
            # ["E", 0.05, 0.3],
            # ["E", 0.05, 0.3],
            # ["a", 0.05, 0.3],

            # ["a", 0.05, 0.85],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.69],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            ["z", 3.55, 0.35],
            # ["j", 0.05, 0.93],  # 拆分
            ["j", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.18],

            # ["a", 0.05, 1.28],
            ["a", 0.05, 0.10],  # 冗余，多打几个a
            ["a", 0.05, 0.10],
            ["a", 0.05, 1.00],
        ]

    @combat_cache
    def Ezja(self):
        return [
            # 白椿转红椿 重击转圈 下砸落地 消耗【红椿·蕊】
            # ["E", 0.05, 0.50],  # 拆分
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.20],

            ["z", 5.35, 0.50],

            # ["j", 0.05, 1.01],  # 拆分
            ["j", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.26],

            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.10],  # 冗余，多打几个a
            ["a", 0.05, 0.10],
            ["a", 0.05, 1.00],
        ]

    @combat_cache
    def zja(self):
        # 相比Ezja少一步变红椿
        return [
            # 红椿 重击转圈 下砸落地 消耗【红椿·蕊】
            # ["E", 0.05, 0.50],
            ["z", 5.35, 0.50],

            # ["j", 0.05, 1.01],  # 拆分
            ["j", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.26],

            # ["a", 0.05, 1.20],
            ["a", 0.05, 0.10],  # 冗余，多打几个a
            ["a", 0.05, 0.10],
            ["a", 0.05, 1.00],
        ]

    @combat_cache
    def ja(self):
        # 落地 退出红椿
        return [
            # 红椿转白椿
            # ["j", 0.05, 1.01],  # 拆分
            ["j", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.26],

            ["a", 0.05, 1.20],
        ]

    @combat_cache
    def ephemeral_a(self):
        return [
            # 一日花 Ea 下砸落地
            # ["E", 0.05, 1.40],  # 拆分
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.20],
            ["E", 0.05, 0.30],
            ["E", 0.05, 0.30],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 1.00],
            ["a", 0.05, 0.10],
            ["w", 0.00, 0.90],
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能
            ["Q", 0.05, 0.00],
        ]

    @combat_cache
    def R(self):
        return [
            # ["R", 0.05, 4.06],  # 拆分
            ["R", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["R", 0.05, 2.94],
        ]

    @combat_cache
    def RaRa(self):
        # 需要等R结束后放一日花，中途穿插普攻
        return [
            # ["R", 0.05, 4.06],  # 拆分
            ["R", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["a", 0.05, 0.20],

            ["R", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["R", 0.05, 0.20],
            ["a", 0.05, 0.20],

            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.26],
            ["a", 0.05, 0.50],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def exit_special_state(self, morph: Morph) -> bool:
        logger.debug("exit_special_state")
        self.combo_action(self.ja(), True, ignore_event=True)
        # 椿落地会前移，后闪复位
        self.control_service.dash_dodge()
        time.sleep(0.3)
        return True

    def combo(self):
        # 变奏
        self.combo_action(self.a3(), True)

        img = self.img_service.screenshot()
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_crimson_blossom_ready = self.is_resonance_skill_crimson_blossom_ready(img)
        is_resonance_skill_floral_ravage_ready = self.is_resonance_skill_floral_ravage_ready(img)
        is_resonance_skill_ephemeral_ready = self.is_resonance_skill_ephemeral_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        # boss_hp = self.boss_hp(img)

        if is_resonance_skill_ephemeral_ready and is_resonance_liberation_ready:
            # 一日花会清除【红椿·蕾】，先大
            self.combo_action(self.RaRa(), True)
            self.combo_action(self.ephemeral_a(), False)
            return

        # 手慢无
        if is_resonance_skill_ephemeral_ready:
            self.combo_action(self.ephemeral_a(), False)
            return

        # 化作椿花养料
        if is_resonance_liberation_ready:
            self.combo_action(self.R(), False)
            time.sleep(0.05)
            return

        # 冥歌海墟
        is_whimpering_wastes = False
        # 声骸boss
        is_echo_boss = True

        # 白椿
        if is_resonance_skill_crimson_blossom_ready:
            if is_whimpering_wastes:
                # self.combo_action(self.Eaazja(), False)
                # self.combo_action(self.Ezja(), False)
                self.combo_action(self.QdEj(), False)
            else:
                if self.random_float() < 0.5:
                    self.combo_action(self.waz(), False)
                else:
                    # self.combo_action(self.a3z(), False)  # 普攻次数不稳定，接不上派生转圈
                    # self.combo_action(self.z(), False)  # 被肘容易发呆
                    # self.combo_action(self.waz(), False)
                    self.combo_action(self.EQdzjE(), False)
            time.sleep(0.6)
        # 红椿
        elif is_resonance_skill_floral_ravage_ready:
            if is_whimpering_wastes:
                # 开转
                # self.combo_action(self.aazja(), False)
                self.combo_action(self.zja(), False)
                time.sleep(0.6)
            else:
                # 转白椿
                self.combo_action(self.EQdzjE(), False)
                return
        else:
            # 兜底，打一套普攻
            self.combo_action(self.a4(), False)
            time.sleep(0.6)

        img = self.img_service.screenshot()
        is_resonance_skill_ephemeral_ready = self.is_resonance_skill_ephemeral_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        boss_hp = self.boss_hp(img)

        if is_resonance_skill_ephemeral_ready and is_resonance_liberation_ready:
            # 一日花会清除【红椿·蕾】，先大
            if boss_hp >= 0.3:
                self.combo_action(self.RaRa(), True)
            self.combo_action(self.ephemeral_a(), False)
            return

        # 手慢无
        if is_resonance_skill_ephemeral_ready:
            self.combo_action(self.ephemeral_a(), False)
            return

        # 化作椿花养料
        if is_resonance_liberation_ready:
            self.combo_action(self.RaRa(), True)

            # 再检查一次一日花
            img = self.img_service.screenshot()
            is_resonance_skill_ephemeral_ready = self.is_resonance_skill_ephemeral_ready(img)
            if is_resonance_skill_ephemeral_ready:
                self.combo_action(self.ephemeral_a(), False)
                return

            return

        # self.combo_action(self.Q(), False)
