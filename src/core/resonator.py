import logging
import time

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, List

import numpy as np

from src.core.color import Color, RuleMode, ColorRule
from src.core.combat.combat_core import Morph
from src.core.exceptions import StopError
from src.core.geometry import Scaler, AnchorPoint, Align, AnchorBBox
from src.core.i18n import I18nText, Language, I18nTr
from src.core.resource import Resource
from src.core.workflow import NodeContext
from src.util import img_util
from src.util.img_sift_util import SIFTFeatureMatcher

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class Element(Enum):
    """元素属性"""
    GLACIO = "冷凝"
    FUSION = "热熔"
    ELECTRO = "导电"
    AERO = "气动"
    SPECTRO = "衍射"
    HAVOC = "湮灭"

    def __str__(self):
        return self.value


class Gender(Enum):
    """性别"""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    UNKNOWN = "unknown"

    def __str__(self):
        return self.value


class BodyType(Enum):
    """体型"""
    BABY = "baby"
    CHILD = "child"
    TEEN = "teen"
    YOUNG_ADULT = "young"
    ADULT = "adult"
    LARGE = "large"

    def __str__(self):
        return self.value


class RoleStyle(Enum):
    """战斗风格/定位"""
    MAIN_DAMAGE_DEALER = "main_damage_dealer"  # 主力输出
    RESONANCE_LIBERATION_DAMAGE = "resonance_liberation_damage"  # 共鸣解放伤害
    GLACIO_CHAFE = "glacio_chafe"  # 霜渐
    SUB_DPS = "sub_dps"  # 副C
    SUPPORT = "support"  # 辅助
    HEALER = "healer"  # 治疗
    SHIELD = "shield"  # 护盾
    ENHANCER = "enhancer"  # 增伤
    CROWD_CONTROL = "cc"  # 控制

    def __str__(self):
        return self.value


class DamageType(Enum):
    """伤害类型"""
    PHYSICAL = "physical"
    GLACIO = "glacio"
    FUSION = "fusion"
    ELECTRO = "electro"
    AERO = "aero"
    SPECTRO = "spectro"
    HAVOC = "havoc"

    def __str__(self):
        return self.value


class StarRating(Enum):
    """星级"""
    FOUR_STAR = 4
    FIVE_STAR = 5

    def __str__(self):
        return f"{self.value}star"

    @property
    def stars(self) -> str:
        return "★" * self.value


class Weapon(Enum):
    """武器类型"""
    SWORD = "sword"  # 迅刀
    GREATSWORD = "greatsword"  # 大剑
    POLEARM = "polearm"  # 长刃
    RECTIFIER = "rectifier"  # 音感仪
    GAUNTLET = "gauntlet"  # 臂铠

    def __str__(self):
        return self.value


class Birthplace(Enum):
    """出生地"""
    HUANGLONG = "huanglong"
    LINA_XITA = "lina_xita"
    OTHER = "other"
    UNKNOWN = "unknown"

    def __str__(self):
        return self.value


class Affiliation(Enum):
    """势力"""
    HUANGLONG_GOVERNMENT = "huanglong_government"
    MIDNIGHT_RANGERS = "midnight_rangers"
    NOCTURNUS = "nocturnus"
    LINA_XITA_GOVERNMENT = "lina_xita_government"
    INDEPENDENT = "independent"
    UNKNOWN = "unknown"

    def __str__(self):
        return self.value


class TalentType(Enum):
    """天赋类型"""
    NORMAL_ATTACK = "normal_attack"
    RESONANCE_SKILL = "resonance_skill"
    RESONANCE_LIBERATION = "resonance_liberation"
    FORTE_CIRCUIT = "forte_circuit"
    INHERENT_SKILL_1 = "inherent_1"
    INHERENT_SKILL_2 = "inherent_2"

    def __str__(self):
        return self.value


# ==================== 天赋技能 ====================

@dataclass(frozen=True)
class Talent:
    """天赋技能"""
    id: str
    name: str
    type: TalentType
    description: str
    scaling: Dict[str, float] = field(default_factory=dict)
    cooldown: float = 0.0
    concerto_cost: int = 0
    duration: float = 0.0
    max_level: int = 10


# ==================== 战斗属性分组 ====================

@dataclass(frozen=True)
class AttackStats:
    """攻击相关属性"""
    base_atk: int = 0
    secondary_stat: str = ""
    secondary_value: float = 0.0
    attack_range: float = 1.0
    attack_speed: float = 1.0
    hit_stop: float = 0.1


@dataclass(frozen=True)
class DefenseStats:
    """防御相关属性"""
    base_hp: int = 0
    base_def: int = 0
    base_shield: int = 0
    stagger_resistance: float = 1.0
    damage_reduction: float = 0.0
    shield_strength: float = 0.0


@dataclass(frozen=True)
class ElementalStats:
    """元素相关属性"""
    element_type: Element
    resonance_efficiency: float = 1.0
    crit_rate: float = 0.05
    crit_damage: float = 1.50

    glacio_dmg_bonus: float = 0.0
    fusion_dmg_bonus: float = 0.0
    electro_dmg_bonus: float = 0.0
    aero_dmg_bonus: float = 0.0
    spectro_dmg_bonus: float = 0.0
    havoc_dmg_bonus: float = 0.0

    element_resistance: Dict[Element, float] = field(default_factory=dict)

    @property
    def current_dmg_bonus(self) -> float:
        """当前元素伤害加成"""
        bonuses = {
            Element.GLACIO: self.glacio_dmg_bonus,
            Element.FUSION: self.fusion_dmg_bonus,
            Element.ELECTRO: self.electro_dmg_bonus,
            Element.AERO: self.aero_dmg_bonus,
            Element.SPECTRO: self.spectro_dmg_bonus,
            Element.HAVOC: self.havoc_dmg_bonus,
        }
        return bonuses.get(self.element_type, 0.0)


@dataclass(frozen=True)
class MovementStats:
    """移动相关属性"""
    walk_speed: float = 2.5
    run_speed: float = 5.0
    dash_speed: float = 8.0
    dash_cost: float = 20.0
    jump_power: float = 5.0
    stamina: int = 100


@dataclass(frozen=True)
class TeamRole:
    """队伍定位"""
    primary: RoleStyle
    secondary: Optional[RoleStyle] = None
    concerto_generation: float = 0.0
    uptime: float = 1.0


# ==================== 主数据类 ====================

@dataclass(frozen=True)
class CharacterMeta:
    """角色元数据（完整战斗版）"""

    # ----- 基础信息 -----
    id: str
    name: str
    title: Optional[str] = None
    body_type: BodyType = BodyType.ADULT
    element: Element = Element.GLACIO
    gender: Gender = Gender.UNKNOWN
    star: StarRating = StarRating.FOUR_STAR
    weapon: Weapon = Weapon.SWORD
    birthplace: Birthplace = Birthplace.UNKNOWN
    affiliation: Affiliation = Affiliation.UNKNOWN

    # ----- 战斗定位 -----
    role_style: RoleStyle = RoleStyle.MAIN_DAMAGE_DEALER
    damage_type: DamageType = DamageType.PHYSICAL
    secondary_style: Optional[RoleStyle] = None

    # ----- 版本信息 -----
    release_version: str = "1.0"
    release_date: Optional[datetime] = None

    # ----- 数值属性（分组）-----
    attack_stats: AttackStats = field(default_factory=AttackStats)
    defense_stats: DefenseStats = field(default_factory=DefenseStats)
    elemental_stats: ElementalStats = field(default_factory=lambda: ElementalStats(element_type=Element.GLACIO))
    movement_stats: MovementStats = field(default_factory=MovementStats)
    team_role: TeamRole = field(default_factory=lambda: TeamRole(primary=RoleStyle.SUB_DPS))

    # ----- 天赋系统 -----
    talents: Dict[TalentType, Talent] = field(default_factory=dict)

    # ----- 战斗机制 -----
    hitbox_radius: float = 0.5
    hitbox_height: float = 1.6
    auto_target_range: float = 10.0
    lock_on_range: float = 15.0

    poise: float = 100.0
    poise_regen: float = 25.0
    poise_regen_delay: float = 2.0

    concerto_particle: int = 3
    liberation_cost: int = 125
    liberation_cooldown: float = 20.0
    skill_cooldown: float = 6.0

    resonance_chain_effects: Dict[int, str] = field(default_factory=dict)

    # ----- 队伍加成 -----
    teammate_synergy: Dict[str, float] = field(default_factory=dict)

    # ----- AI/自动战斗 -----
    ai_priority: int = 5
    ai_rotation: List[str] = field(default_factory=list)

    # ----- 描述性 -----
    signature_weapon: Optional[str] = None
    description: str = ""

    # ===== 辅助属性 =====
    @property
    def full_name(self) -> str:
        if self.title:
            return f"{self.title} · {self.name}"
        return self.name

    @property
    def is_five_star(self) -> bool:
        return self.star == StarRating.FIVE_STAR

    @property
    def elemental_damage_bonus(self) -> float:
        return self.elemental_stats.current_dmg_bonus


# ==================== 示例角色 ====================

def create_example_fusion_dps() -> CharacterMeta:
    """示例：热熔主力输出（五星限定）"""
    attack = AttackStats(
        base_atk=350,
        secondary_stat="crit_rate",
        secondary_value=0.22,
        attack_range=4.0,
        attack_speed=0.9
    )
    defense = DefenseStats(base_hp=11000, base_def=650)
    elemental = ElementalStats(
        element_type=Element.FUSION,
        fusion_dmg_bonus=0.288,
        crit_rate=0.05,
        crit_damage=1.50,
        resonance_efficiency=1.0
    )
    team = TeamRole(primary=RoleStyle.MAIN_DAMAGE_DEALER, concerto_generation=0.8)

    return CharacterMeta(
        id="fusion_dps_01",
        name="炎息",
        title="熔火之心",
        body_type=BodyType.ADULT,
        element=Element.FUSION,
        gender=Gender.FEMALE,
        star=StarRating.FIVE_STAR,
        weapon=Weapon.GREATSWORD,
        birthplace=Birthplace.LINA_XITA,
        affiliation=Affiliation.LINA_XITA_GOVERNMENT,
        role_style=RoleStyle.MAIN_DAMAGE_DEALER,
        damage_type=DamageType.FUSION,
        release_version="1.1",
        attack_stats=attack,
        defense_stats=defense,
        elemental_stats=elemental,
        team_role=team,
        liberation_cost=150,
        liberation_cooldown=22,
        skill_cooldown=8,
        description="挥舞大剑的热熔战士，以爆炸性输出见长。"
    )


def create_example_glacio_chafe() -> CharacterMeta:
    """示例：霜渐输出（五星限定）"""
    attack = AttackStats(
        base_atk=340,
        secondary_stat="crit_damage",
        secondary_value=0.28,
        attack_range=5.0,
        attack_speed=1.0
    )
    defense = DefenseStats(base_hp=10500, base_def=600)
    elemental = ElementalStats(
        element_type=Element.GLACIO,
        glacio_dmg_bonus=0.30,
        crit_rate=0.05,
        crit_damage=1.55,
        resonance_efficiency=1.0
    )
    team = TeamRole(primary=RoleStyle.GLACIO_CHAFE, concerto_generation=0.9)

    return CharacterMeta(
        id="glacio_chafe_01",
        name="霜华",
        title="凛冬使者",
        body_type=BodyType.TEEN,
        element=Element.GLACIO,
        gender=Gender.MALE,
        star=StarRating.FIVE_STAR,
        weapon=Weapon.SWORD,
        birthplace=Birthplace.HUANGLONG,
        affiliation=Affiliation.MIDNIGHT_RANGERS,
        role_style=RoleStyle.GLACIO_CHAFE,
        damage_type=DamageType.GLACIO,
        release_version="1.2",
        attack_stats=attack,
        defense_stats=defense,
        elemental_stats=elemental,
        team_role=team,
        liberation_cost=130,
        liberation_cooldown=18,
        skill_cooldown=7,
        description="以冰元素持续伤害见长的剑士，霜渐效果可叠加。"
    )


def create_example_resonance_liberation_dps() -> CharacterMeta:
    """示例：共鸣解放伤害特化（五星常驻）"""
    attack = AttackStats(
        base_atk=360,
        secondary_stat="resonance_efficiency",
        secondary_value=0.32,
        attack_range=6.0
    )
    defense = DefenseStats(base_hp=10800, base_def=620)
    elemental = ElementalStats(
        element_type=Element.HAVOC,
        havoc_dmg_bonus=0.20,
        resonance_efficiency=1.3,
        crit_damage=1.60
    )
    team = TeamRole(primary=RoleStyle.RESONANCE_LIBERATION_DAMAGE, concerto_generation=1.2)

    return CharacterMeta(
        id="rl_dps_01",
        name="渊影",
        title="深渊回响",
        body_type=BodyType.ADULT,
        element=Element.HAVOC,
        gender=Gender.FEMALE,
        star=StarRating.FIVE_STAR,
        weapon=Weapon.POLEARM,
        birthplace=Birthplace.HUANGLONG,
        affiliation=Affiliation.NOCTURNUS,
        role_style=RoleStyle.RESONANCE_LIBERATION_DAMAGE,
        damage_type=DamageType.HAVOC,
        release_version="1.0",
        attack_stats=attack,
        defense_stats=defense,
        elemental_stats=elemental,
        team_role=team,
        liberation_cost=150,
        liberation_cooldown=20,
        skill_cooldown=5,
        description="特化共鸣解放伤害的输出角色，大招是其核心输出手段。"
    )


def create_example_support() -> CharacterMeta:
    """示例：辅助（四星常驻）"""
    attack = AttackStats(base_atk=240, attack_range=12.0)
    defense = DefenseStats(base_hp=8800, base_def=500)
    elemental = ElementalStats(
        element_type=Element.AERO,
        aero_dmg_bonus=0.0,
        resonance_efficiency=1.2
    )
    team = TeamRole(primary=RoleStyle.SUPPORT, concerto_generation=1.2)

    return CharacterMeta(
        id="support_01",
        name="风语",
        title="协奏之音",
        body_type=BodyType.TEEN,
        element=Element.AERO,
        gender=Gender.MALE,
        star=StarRating.FOUR_STAR,
        weapon=Weapon.RECTIFIER,
        birthplace=Birthplace.OTHER,
        affiliation=Affiliation.INDEPENDENT,
        role_style=RoleStyle.SUPPORT,
        damage_type=DamageType.AERO,
        release_version="1.0",
        attack_stats=attack,
        defense_stats=defense,
        elemental_stats=elemental,
        team_role=team,
        liberation_cost=100,
        description="提供团队增益和协奏能量回复的辅助角色。"
    )


# ==================== 使用示例 ====================

def demo():
    chars = [
        create_example_fusion_dps(),
        create_example_glacio_chafe(),
        create_example_resonance_liberation_dps(),
        create_example_support()
    ]

    print("=== 角色信息 ===\n")
    for c in chars:
        print(f"【{c.full_name}】")
        print(f"  性别: {c.gender.value} | 体型: {c.body_type.value}")
        print(f"  出生: {c.birthplace.value} | 势力: {c.affiliation.value}")
        print(f"  元素: {c.element} | 武器: {c.weapon.value}")
        print(f"  星级: {c.star} | 战斗风格: {c.role_style.value}")
        print(f"  共鸣解放消耗: {c.liberation_cost}")
        print()


def create_tmp_resonator(id: str) -> CharacterMeta:
    """临时占位用"""
    attack = AttackStats(
        base_atk=350,
        secondary_stat="crit_rate",
        secondary_value=0.22,
        attack_range=4.0,
        attack_speed=0.9
    )
    defense = DefenseStats(base_hp=11000, base_def=650)
    elemental = ElementalStats(
        element_type=Element.FUSION,
        fusion_dmg_bonus=0.288,
        crit_rate=0.05,
        crit_damage=1.50,
        resonance_efficiency=1.0
    )
    team = TeamRole(primary=RoleStyle.MAIN_DAMAGE_DEALER, concerto_generation=0.8)

    return CharacterMeta(
        id=id,
        name="炎息",
        title="熔火之心",
        body_type=BodyType.ADULT,
        element=Element.FUSION,
        gender=Gender.FEMALE,
        star=StarRating.FIVE_STAR,
        weapon=Weapon.GREATSWORD,
        birthplace=Birthplace.LINA_XITA,
        affiliation=Affiliation.LINA_XITA_GOVERNMENT,
        role_style=RoleStyle.MAIN_DAMAGE_DEALER,
        damage_type=DamageType.FUSION,
        release_version="1.1",
        attack_stats=attack,
        defense_stats=defense,
        elemental_stats=elemental,
        team_role=team,
        liberation_cost=150,
        liberation_cooldown=22,
        skill_cooldown=8,
        description="挥舞大剑的热熔战士，以爆炸性输出见长。"
    )


class Resonator(Enum):
    # 特殊
    Rover = create_tmp_resonator(I18nText.Rover)
    Generic = create_tmp_resonator(I18nText.Generic)
    Null = create_tmp_resonator(I18nText.Null)

    # 常驻
    Encore = create_tmp_resonator(I18nText.Encore)
    Verina = create_tmp_resonator(I18nText.Verina)
    Calcharo = create_tmp_resonator(I18nText.Calcharo)
    Lingyang = create_tmp_resonator(I18nText.Lingyang)
    Jianxin = create_tmp_resonator(I18nText.Jianxin)

    Yangyang = create_tmp_resonator(I18nText.Yangyang)
    Baizhi = create_tmp_resonator(I18nText.Baizhi)
    Chixia = create_tmp_resonator(I18nText.Chixia)
    Sanhua = create_tmp_resonator(I18nText.Sanhua)
    Aalto = create_tmp_resonator(I18nText.Aalto)
    Danjin = create_tmp_resonator(I18nText.Danjin)
    Mortefi = create_tmp_resonator(I18nText.Mortefi)
    Yuanwu = create_tmp_resonator(I18nText.Yuanwu)
    Taoqi = create_tmp_resonator(I18nText.Taoqi)

    # v1.0
    Jiyan = create_tmp_resonator(I18nText.Jiyan)
    Yinlin = create_tmp_resonator(I18nText.Yinlin)

    # v1.1
    Jinhsi = create_tmp_resonator(I18nText.Jinhsi)
    Changli = create_tmp_resonator(I18nText.Changli)

    # v1.2
    Zhezhi = create_tmp_resonator(I18nText.Zhezhi)
    XiangliYao = create_tmp_resonator(I18nText.XiangliYao)

    # v1.3
    Shorekeeper = create_tmp_resonator(I18nText.Shorekeeper)
    Youhu = create_tmp_resonator(I18nText.Youhu)

    # v1.4
    Camellya = create_tmp_resonator(I18nText.Camellya)
    Lumi = create_tmp_resonator(I18nText.Lumi)

    # v2.0
    Carlotta = create_tmp_resonator(I18nText.Carlotta)
    Roccia = create_tmp_resonator(I18nText.Roccia)

    # v2.1
    Phoebe = create_tmp_resonator(I18nText.Phoebe)
    Brant = create_tmp_resonator(I18nText.Brant)

    # v2.2
    Cantarella = create_tmp_resonator(I18nText.Cantarella)

    # v2.3
    Zanni = create_tmp_resonator(I18nText.Zanni)
    Ciaccona = create_tmp_resonator(I18nText.Ciaccona)

    # v2.4
    Cartethyia = create_tmp_resonator(I18nText.Cartethyia)
    Lupa = create_tmp_resonator(I18nText.Lupa)

    # v2.5
    Phrolova = create_tmp_resonator(I18nText.Phrolova)

    # v2.6
    Augusta = create_tmp_resonator(I18nText.Augusta)
    Iuno = create_tmp_resonator(I18nText.Iuno)

    # v2.7
    Galbrena = create_tmp_resonator(I18nText.Galbrena)
    Qiuyuan = create_tmp_resonator(I18nText.Qiuyuan)

    # v2.8
    Chisa = create_tmp_resonator(I18nText.Chisa)
    Buling = create_tmp_resonator(I18nText.Buling)

    # v3.0
    Lynae = create_tmp_resonator(I18nText.Lynae)
    Mornye = create_tmp_resonator(I18nText.Mornye)

    # v3.1
    Aemeath = create_tmp_resonator(I18nText.Aemeath)
    LuukHerssen = create_tmp_resonator(I18nText.LuukHerssen)

    # v3.2
    Sigrika = create_tmp_resonator(I18nText.Sigrika)

    # v3.3
    Hiyuki = create_tmp_resonator(I18nText.Hiyuki)
    Denia = create_tmp_resonator(I18nText.Denia)

    # v3.4
    Lucy = create_tmp_resonator(I18nText.Lucy)
    Rebecca = create_tmp_resonator(I18nText.Rebecca)
    Lucilla = create_tmp_resonator(I18nText.Lucilla)

    # v3.5
    YangyangXuanling = create_tmp_resonator(I18nText.YangyangXuanling)
    Suisui = create_tmp_resonator(I18nText.Suisui)

    # v3.6
    Qingxiao = create_tmp_resonator(I18nText.Qingxiao)
    Jingran = create_tmp_resonator(I18nText.Jingran)

    # v3.x
    Hsin = create_tmp_resonator(I18nText.Hsin)
    Suoming = create_tmp_resonator(I18nText.Suoming)

    __value_map = None

    @classmethod
    def from_key(cls, key: str):
        if cls.__value_map is None:
            cls.__value_map = {}
            for member in cls:
                if member in [cls.Rover, cls.Generic, cls.Null]:
                    continue
                cls.__value_map[member.value.id] = member
        # print(cls.__value_map.keys())
        return cls.__value_map.get(key)


    @staticmethod
    def i18n_keys():
        return [
            I18nText.Encore,
            I18nText.Verina,
            I18nText.Calcharo,
            I18nText.Lingyang,
            I18nText.Jianxin,
            I18nText.Yangyang,
            I18nText.Baizhi,
            I18nText.Chixia,
            I18nText.Sanhua,
            I18nText.Aalto,
            I18nText.Danjin,
            I18nText.Mortefi,
            I18nText.Yuanwu,
            I18nText.Taoqi,
            I18nText.Jiyan,
            I18nText.Yinlin,
            I18nText.Jinhsi,
            I18nText.Changli,
            I18nText.Zhezhi,
            I18nText.XiangliYao,
            I18nText.Shorekeeper,
            I18nText.Youhu,
            I18nText.Camellya,
            I18nText.Lumi,
            I18nText.Carlotta,
            I18nText.Roccia,
            I18nText.Phoebe,
            I18nText.Brant,
            I18nText.Cantarella,
            I18nText.Zanni,
            I18nText.Ciaccona,
            I18nText.Cartethyia,
            I18nText.Lupa,
            I18nText.Phrolova,
            I18nText.Augusta,
            I18nText.Iuno,
            I18nText.Galbrena,
            I18nText.Qiuyuan,
            I18nText.Chisa,
            I18nText.Buling,
            I18nText.Lynae,
            I18nText.Mornye,
            I18nText.Aemeath,
            I18nText.LuukHerssen,
            I18nText.Sigrika,
            I18nText.Hiyuki,
            I18nText.Denia,
            I18nText.Lucy,
            I18nText.Rebecca,
            I18nText.Lucilla,
            I18nText.YangyangXuanling,
            I18nText.Suisui,
            I18nText.Qingxiao,
            I18nText.Jingran,
            I18nText.Hsin,
            I18nText.Suoming,
        ]

    @staticmethod
    @lru_cache
    def avatar_mappings() -> dict[str, str]:
        """角色头像"""
        return {
            "T_IconRoleHead150_1.png": I18nText.Yangyang,
            "T_IconRoleHead150_2.png": I18nText.Chixia,
            "T_IconRoleHead150_3.png": I18nText.Verina,
            "T_IconRoleHead150_4.png": I18nText.Rover,
            "T_IconRoleHead150_4_a_UI.png": I18nText.Rover,
            "T_IconRoleHead150_5.png": I18nText.Rover,
            "T_IconRoleHead150_5_a_UI.png": I18nText.Rover,
            "T_IconRoleHead150_6.png": I18nText.Baizhi,
            "T_IconRoleHead150_7.png": I18nText.Sanhua,
            "T_IconRoleHead150_7_a.png": I18nText.Sanhua,
            "T_IconRoleHead150_8.png": I18nText.Encore,
            "T_IconRoleHead150_9.png": I18nText.Taoqi,
            "T_IconRoleHead150_10.png": I18nText.Danjin,
            "T_IconRoleHead150_11.png": I18nText.Jiyan,
            "T_IconRoleHead150_12.png": I18nText.Aalto,
            "T_IconRoleHead150_13.png": I18nText.Mortefi,
            "T_IconRoleHead150_14.png": I18nText.Lingyang,
            "T_IconRoleHead150_15.png": I18nText.Yuanwu,
            "T_IconRoleHead150_17.png": I18nText.Yinlin,
            "T_IconRoleHead150_18.png": I18nText.Calcharo,
            "T_IconRoleHead150_23_UI.png": I18nText.Jianxin,
            "T_IconRoleHead150_24_a_UI.png": I18nText.Jinhsi,
            "T_IconRoleHead150_24_UI.png": I18nText.Jinhsi,
            "T_IconRoleHead150_25_UI.png": I18nText.XiangliYao,
            "T_IconRoleHead150_26_a_UI.png": I18nText.Changli,
            "T_IconRoleHead150_26_UI.png": I18nText.Changli,
            "T_IconRoleHead150_27_UI.png": I18nText.Zhezhi,
            "T_IconRoleHead150_28_UI.png": I18nText.Shorekeeper,
            "T_IconRoleHead150_29_UI.png": I18nText.Camellya,
            "T_IconRoleHead150_30_UI.png": I18nText.Lumi,
            "T_IconRoleHead150_31_UI.png": I18nText.Youhu,
            "T_IconRoleHead150_32_a_UI.png": I18nText.Carlotta,
            "T_IconRoleHead150_32_UI.png": I18nText.Carlotta,
            "T_IconRoleHead150_33_UI.png": I18nText.Roccia,
            "T_IconRoleHead150_34_UI.png": I18nText.Cantarella,
            "T_IconRoleHead150_37_UI.png": I18nText.Ciaccona,
            "T_IconRoleHead150_38_a_UI.png": I18nText.Zanni,
            "T_IconRoleHead150_38_UI.png": I18nText.Zanni,
            "T_IconRoleHead150_40_UI.png": I18nText.Cartethyia,
            "T_IconRoleHead150_41_UI.png": I18nText.Phrolova,
            "T_IconRoleHead150_44_UI.png": I18nText.Brant,
            "T_IconRoleHead150_45_UI.png": I18nText.Phoebe,
            "T_IconRoleHead150_46_UI.png": I18nText.Lupa,
            "T_IconRoleHead150_48_UI.png": I18nText.Iuno,
            "T_IconRoleHead150_51_UI.png": I18nText.Augusta,
            "T_IconRoleHead150_53_UI.png": I18nText.Aemeath,
            "T_IconRoleHead150_54_UI.png": I18nText.LuukHerssen,
            "T_IconRoleHead150_55_UI.png": I18nText.Galbrena,
            "T_IconRoleHead150_56_UI.png": I18nText.Qiuyuan,
            "T_IconRoleHead150_57_Skin1_UI.png": I18nText.Chisa,
            "T_IconRoleHead150_57_UI.png": I18nText.Chisa,
            "T_IconRoleHead150_58_UI.png": I18nText.Buling,
            "T_IconRoleHead150_60_Skin1_UI.png": I18nText.Lynae,
            "T_IconRoleHead150_60_UI.png": I18nText.Lynae,
            "T_IconRoleHead150_61_Skin1_UI.png": I18nText.Mornye,
            "T_IconRoleHead150_61_UI.png": I18nText.Mornye,
            "T_IconRoleHead150_64_UI.png": I18nText.Denia,
            "T_IconRoleHead150_65_UI.png": I18nText.Sigrika,
            "T_IconRoleHead150_66_UI.png": I18nText.Lucilla,
            "T_IconRoleHead150_67_UI.png": I18nText.Hiyuki,
            "T_IconRoleHead150_68_UI.png": I18nText.Lucy,
            "T_IconRoleHead150_69_UI.png": I18nText.Rebecca,
            "T_IconRoleHead150_70_UI.png": I18nText.YangyangXuanling,
            "T_IconRoleHead150_71_UI.png": I18nText.Suisui,
            "T_IconRoleHead150_73_Guest1_UI.png": I18nText.Qingxiao,
            "T_IconRoleHead150_73_UI.png": I18nText.Qingxiao,
            "T_IconRoleHead150_74_UI.png": I18nText.Jingran,
        }


class TeamMember:
    """大世界 编队相关"""

    def __init__(self, ctx: NodeContext):
        self.ctx = ctx

    @classmethod
    def __match(cls, img: np.ndarray):
        points = [
            [
                AnchorPoint(1158, 146, Align.Top | Align.Right),
                AnchorPoint(1160, 151, Align.Top | Align.Right),
                AnchorPoint(1166, 143, Align.Top | Align.Right),
                AnchorPoint(1166, 151, Align.Top | Align.Right),
            ],
            [
                AnchorPoint(1159, 234, Align.Top | Align.Right),
                AnchorPoint(1158, 240, Align.Top | Align.Right),
                AnchorPoint(1167, 231, Align.Top | Align.Right),
                AnchorPoint(1168, 240, Align.Top | Align.Right),
            ],
            [
                AnchorPoint(1159, 322, Align.Top | Align.Right),
                AnchorPoint(1158, 328, Align.Top | Align.Right),
                AnchorPoint(1167, 319, Align.Top | Align.Right),
                AnchorPoint(1168, 328, Align.Top | Align.Right),
            ],
        ]
        bgr = Color.bgr(241, 241, 241)
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        return [ColorRule().points(p).colors(bgr, tol=20, mode=RuleMode.ALL).match(img, scaler) for p in points]

    @classmethod
    def get_size(cls, img: np.ndarray):
        """
        编队人数
        :param img: 大世界截图，右侧需有角色头像
        :return: 1、2、3
        """
        res = cls.__match(img)
        return min(sum(x for x in res) + 1, 3)

    @classmethod
    def get_cur_idx(cls, img: np.ndarray) -> Optional[int]:
        """
        获取当前主控角色编号，
        :param img: 大世界截图，右侧需有角色头像
        :return: 1、2、3
        """
        res = cls.__match(img)
        if not res[0]:
            return 1
        if not res[1]:
            return 2
        if not res[2]:
            return 3
        return None

    def switch_to(self, idx: int):
        """
        切换到角色
        :param idx: 1、2、3
        :return:
        """
        if idx > 3 or idx < 1:
            raise ValueError()
        self.ctx.control_service.toggle_team_member(idx)

    @staticmethod
    @lru_cache
    def load_role_features():
        """加载头像资源，约0.5s"""
        role_features = []
        logger.debug("Loading resources")
        matcher = SIFTFeatureMatcher()
        start_time = time.monotonic()
        for p in Resource.Unpacked.IconRoleHead150.glob("*.png"):
            feature_image = img_util.read_img(p.absolute())
            feature_data = matcher.build_feature_data_masked(feature_id=p.name, image=feature_image)
            role_features.append(feature_data)
        logger.debug(f"Loading complete. (Duration: {time.monotonic() - start_time:.2f}s)")
        return role_features

    @staticmethod
    def __spacing():
        """右侧角色头像之间的间距，血条高度差"""
        return 280 - 192

    @classmethod
    def get_members_by_icon(cls, img: np.ndarray) -> list[str | None]:
        """大世界通过右侧角色图标识别角色"""
        role_features = cls.load_role_features()
        matcher = SIFTFeatureMatcher()
        mappings = Resonator.avatar_mappings()
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))

        member_keys = []
        spacing = cls.__spacing()
        for i in range(3):
            roi = AnchorBBox(
                AnchorPoint(1140, 116 + spacing * i, Align.Top | Align.Right),
                AnchorPoint(1280, 210 + spacing * i, Align.Top | Align.Right),
            )
            scene_image = img[scaler.as_bbox(roi).as_slice()]
            res = matcher.identify_roles(scene_image, role_features, min_good_matches=3)
            logger.debug(f"identify_roles: {res}")
            if not res:
                member_keys.append(None)
                continue
            member_keys.append(mappings.get(res[0], None))
        logger.debug(f"member_keys: {member_keys}")

        cls.__print_keys(member_keys)
        return member_keys

    @classmethod
    def get_members_by_text(cls, ui) -> list[str | None]:
        """编队里通过角色名称识别角色"""
        res = []
        img = ui.img
        ctx = ui.ctx
        meta = [
            (
                AnchorPoint(433, 569, Align.Center | Align.Middle),
                AnchorBBox(
                    AnchorPoint(200, 540, Align.Center | Align.Middle),
                    AnchorPoint(510, 600, Align.Center | Align.Middle)
                )
            ),
            (
                AnchorPoint(810, 569, Align.Center | Align.Middle),
                AnchorBBox(
                    AnchorPoint(576, 540, Align.Center | Align.Middle),
                    AnchorPoint(888, 600, Align.Center | Align.Middle)
                )
            ),
            (
                AnchorPoint(1187, 569, Align.Center | Align.Middle),
                AnchorBBox(
                    AnchorPoint(954, 540, Align.Center | Align.Middle),
                    AnchorPoint(1280, 600, Align.Center | Align.Middle)
                )
            )
        ]
        keys = Resonator.i18n_keys()
        for m in meta:
            cr = ColorRule().points(m[0]).colors(Color.bgr(22, 18, 13))
            # 有黑色就说明有角色
            if not cr.match(img, ctx.scaler):
                res.append(None)
                continue
            # 按名字逐个匹配，匹配不到就是漂子
            result = next((k for k in keys if ui.search(ctx.tr(k), m[1])), I18nText.Rover)
            res.append(result)

        cls.__print_keys(res)
        return res

    @staticmethod
    def __print_keys(keys):
        tr = I18nTr(Language.sys_lang())
        tr_keys = []
        for key in keys:
            if not key:
                tr_keys.append(None)
                continue
            if not (res := tr(key)):
                logger.warning(f"Unknown key: {key}")
                tr_keys.append(None)
                continue
            tr_keys.append(res.raw)
        logger.debug(f"Members: {tr_keys}")

    @classmethod
    def downed(cls, img: np.ndarray, tolerance: int = 1, ratio: float = 0.5) -> list[bool]:
        """
        角色是否阵亡
        判断区域内是否有足够比例的灰色像素。

        img: BGR 图像，形状 (H, W, 3)
        tolerance: BGR 三通道允许的最大差值
        ratio: 灰色像素占比阈值，理论上是全灰，但刚阵亡时，可能有切人倒计时，那个数字不是灰的
        """
        spacing = cls.__spacing()
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        res = []
        for i in range(3):
            roi = AnchorBBox(
                AnchorPoint(1193, 162 + spacing * i, Align.Top | Align.Right),
                AnchorPoint(1201, 170 + spacing * i, Align.Top | Align.Right),
            )
            cropped_img = img[scaler.as_bbox(roi).as_slice()]
            diff = cropped_img.max(axis=2) - cropped_img.min(axis=2)
            gray_ratio = np.mean(diff <= tolerance)
            # logger.debug(f"gray_ratio: {gray_ratio}")
            res.append(gray_ratio >= ratio)
        # logger.info(f"downed: {res}")
        return res

    # # def reset_state(self, member_keys: list, morph: Morph) -> bool:
    # def reset_state(self, morph: Morph) -> bool:
    #     try:
    #         team_members = self.ctx.shared.team_members
    #         if not team_members:
    #             return False
    #
    #         src_idx = self.get_cur_idx(self.ctx.img_service.screenshot())
    #         logger.debug(f"src_idx: {src_idx}")
    #         if src_idx is None:
    #             return False
    #
    #         # resonator = Resonator.from_key(member_keys[src_idx - 1])
    #
    #         from src.core.combat.combat_system import CombatSystem
    #         combat_system = CombatSystem(self.ctx.control_service, self.ctx.img_service)
    #         combat_system.set_resonators(self.ctx.shared.team_members, is_print=False)
    #
    #         if not combat_system.resonators:
    #             return False
    #         resonators = [None, None, None]
    #         for i, r in enumerate(combat_system.resonators):
    #             if i > len(resonators) - 1 or not r:
    #                 break
    #             resonators[i] = r
    #         if not (resonator := resonators[src_idx - 1]):
    #             return False
    #         if resonator.exit_special_state(morph):
    #             return True
    #
    #         # for i in range(1, len(member_keys) + 1):
    #         for i in range(1, 4):
    #             if i == src_idx:
    #                 continue
    #
    #             self.switch_to(i)
    #             time.sleep(0.35)
    #             new_idx = self.get_cur_idx(self.ctx.img_service.screenshot())
    #             if new_idx is None:
    #                 break
    #             if new_idx != i:
    #                 # 没切成功，以防万一，点(0,0)关掉复活药弹窗
    #                 self.ctx.control_service.attack()
    #                 time.sleep(0.2)
    #                 continue
    #
    #             # resonator = Resonator.from_key(member_keys[new_idx - 1])
    #             # if resonator.exit_special_state(morph):
    #             #     return True
    #             if not (resonator := resonators[new_idx - 1]):
    #                 return False
    #             if resonator.exit_special_state(morph):
    #                 return True
    #     except (KeyboardInterrupt, StopError) as e:
    #         raise e
    #     except Exception as e:
    #         logger.exception(e)
    #     return False



if __name__ == '__main__':
    from src.util import file_util
    print(Resonator.from_key(I18nText.Cartethyia))
    print(TeamMember.get_members_by_icon(img_util.read_img(file_util.get_temp_screenshot("screenshot_1787206343_88366840.png"))))
    print(TeamMember.downed(img_util.read_img(file_util.get_temp_screenshot("screenshot_1788213527_21789223.png"))))
