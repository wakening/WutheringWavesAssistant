import logging

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Set, List

from src.core.i18n import I18nText

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

    # v3.x
    YangyangXuanling = create_tmp_resonator(I18nText.YangyangXuanling)
    Suisui = create_tmp_resonator(I18nText.Suisui)
    Suoming = create_tmp_resonator(I18nText.Suoming)
    Jingran = create_tmp_resonator(I18nText.Jingran)
    Qingxiao = create_tmp_resonator(I18nText.Qingxiao)
    Hsin = create_tmp_resonator(I18nText.Hsin)

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
            I18nText.Suoming,
            I18nText.Jingran,
            I18nText.Qingxiao,
            I18nText.Hsin,
        ]


if __name__ == '__main__':
    t = Resonator.from_key(I18nText.Cartethyia)
    print(t)
