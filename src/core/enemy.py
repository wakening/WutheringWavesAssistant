import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, ClassVar

import numpy as np

from src.core.geometry import Point, Scaler, AnchorPoint, Align
from src.core.i18n import I18nText, Language, I18nTr
from src.core.movement import Run, MoveStep

logger = logging.getLogger(__name__)


def _tr(key: str) -> str:
    return I18nTr(Language.sys_lang())(key).raw


class EnemyElement(Enum):
    """敌人抗性"""
    Aero = "Aero"  # 气动
    Electro = "Electro"  # 导电
    Fusion = "Fusion"  # 热熔
    Spectro = "Spectro"  # 衍射
    Havoc = "Havoc"  # 湮灭
    Glacio = "Glacio"  # 冷凝


class EnemySpecies(Enum):
    """敌人物种枚举"""
    Whisperin = "Whisperin"  # 呓语种
    Howler = "Howler"  # 啸叫种
    Tranquilite = "Tranquilite"  # 静默种
    Clamorling = "Clamorling"  # 轰鸣种
    Staticoid = "Staticoid"  # 噪声种
    Wanderer = "Wanderer"  # 流浪者
    Fractsidus = "Fractsidus"  # 残星会
    Special = "Special"  # 特殊种类
    Tidespawn = "Tidespawn"  # 受黑潮影响的残像
    Gladiator = "Gladiator"  # 角斗士
    Royan = "Royan"  # 罗伊族
    Other = "Other"  # 其他
    Exoswarm = "Exoswarm"  # 隧群
    NightmareTacetDiscord = "Nightmare Tacet Discord"  # 梦魇残象


class EnemyRank(Enum):
    """敌人分类枚举"""
    CommonClass = "Common Class"  # 轻波级
    EliteClass = "Elite Class"  # 巨浪级
    OverlordClass = "Overlord Class"  # 怒涛级
    CalamityClass = "Calamity Class"  # 海啸级
    EndlessArena = "Endless Arena"  # 无穷尽


class EnemyCost(Enum):
    """敌人消耗值枚举"""
    Cost1 = 1
    Cost3 = 3
    Cost4 = 4


class EnemyIcon(Enum):
    """敌人图标枚举 - 对应图片文件名"""
    Icon1 = "icon1.png"
    Icon2 = "icon2.png"
    Icon3 = "icon3.png"
    Icon4 = "icon4.png"
    Icon5 = "icon5.png"


class EnemyVersion(Enum):
    """实装版本枚举"""
    # 1.x
    V1_0 = "v1.0"
    V1_1 = "v1.1"
    V1_2 = "v1.2"
    V1_3 = "v1.3"
    V1_4 = "v1.4"
    # 2.x
    V2_0 = "v2.0"
    V2_1 = "v2.1"
    V2_2 = "v2.2"
    V2_3 = "v2.3"
    V2_4 = "v2.4"
    V2_5 = "v2.5"
    V2_6 = "v2.6"
    V2_7 = "v2.7"
    V2_8 = "v2.8"
    # 3.x
    V3_0 = "v3.0"
    V3_1 = "v3.1"
    V3_2 = "v3.2"
    V3_3 = "v3.3"
    V3_4 = "v3.4"
    V3_5 = "v3.5"
    V3_6 = "v3.6"
    V3_7 = "v3.7"
    # 4.x
    V4_0 = "v4.0"
    V4_1 = "v4.1"
    V4_2 = "v4.2"
    V4_3 = "v4.3"
    V4_4 = "v4.4"
    V4_5 = "v4.5"
    V4_6 = "v4.6"


class SonataEffect(Enum):
    """声骸套装合鸣效果枚举"""
    FreezingFrost = "Freezing Frost"  # 凝夜白霜
    MoltenRift = "Molten Rift"  # 熔山裂谷
    VoidThunder = "Void Thunder"  # 彻空冥雷
    SierraGale = "Sierra Gale"  # 啸谷长风
    CelestialLight = "Celestial Light"  # 浮星祛暗
    HavocEclipse = "Havoc Eclipse"  # 沉日劫明
    RejuvenatingGlow = "Rejuvenating Glow"  # 隐世回光
    MoonlitClouds = "Moonlit Clouds"  # 轻云出月
    LingeringTunes = "Lingering Tunes"  # 不绝余音
    FrostyResolve = "Frosty Resolve"  # 凌冽决断之心
    EternalRadiance = "Eternal Radiance"  # 此间永驻之光
    MidnightVeil = "Midnight Veil"  # 幽夜隐匿之帷
    EmpyreanAnthem = "Empyrean Anthem"  # 高天共奏之曲
    TidebreakingCourage = "Tidebreaking Courage"  # 无惧浪涛之勇
    GustsOfWelkin = "Gusts of Welkin"  # 流云逝尽之空
    WindwardPilgrimage = "Windward Pilgrimage"  # 愿戴荣光之旅
    FlamingClawprint = "Flaming Clawprint"  # 奔狼燎原之焰
    DreamOfTheLost = "Dream of the Lost"  # 失序彼岸之梦
    CrownOfValor = "Crown of Valor"  # 荣斗铸锋之冠
    LawOfHarmony = "Law of Harmony"  # 息界同调之律
    FlamewingShadow = "Flamewing's Shadow"  # 焚羽猎魔之影
    ThreadOfSeveredFate = "Thread of Severed Fate"  # 命理崩毁之弦
    PactOfNeonlightLeap = "Pact of Neonlight Leap"  # 逆光跃彩之约
    HaloOfStarryRadiance = "Halo of Starry Radiance"  # 星构寻辉之环
    RiteOfGildedRevelation = "Rite of Gilded Revelation"  # 流金溯真之式
    TrailblazingStar = "Trailblazing Star"  # 长路启航之星
    ChromaticFoam = "Chromatic Foam"  # 斑驳粉饰之沫
    SoundOfTrueName = "Sound of True Name"  # 听唤语义之愿
    WishesOfQuietSnowfall = "Wishes of Quiet Snowfall"  # 雪落无声之愿
    ReelOfSplicedMemories = "Reel of Spliced Memories"  # 剪心辑梦之影
    ShadowOfShatteredDreams = "Shadow of Shattered Dreams"  # 碎梦亡鬼之魇
    SongOfFeatheredTrace = "Song of Feathered Trace"  # 羽落空尘之歌
    HeartOfEvilsPurge = "Heart of Evil's Purge"  # 清邪荡煞之心
    LampOfNetherRoad = "Lamp of Nether Road"  # 冥途夜行之灯


@dataclass(frozen=True)
class BossMeta:
    """Boss 相关信息"""
    name: str  # Boss 名称 (用于副本/活动显示)
    is_dungeon: bool  # 是否在独立副本内 (True=副本内, False=野外)
    dungeon_name: Optional[str]  # 副本名称
    auto_respawn: bool  # 是否自动刷新
    enter_text: Optional[str]  # 进入 Boss 房文本
    battle_text: List[str]  # Boss 战时特殊文本
    routes: List[MoveStep]  # 路线 (如 ["路线1", "路线2"])


@dataclass(frozen=True)
class QuickBossMeta:
    """快速挑战 Boss 相关信息"""
    name: str  # Boss 名称 (用于副本/活动显示)
    menu: str  # 快捷挑战菜单标识 (如 "weekly_boss", "event_boss" 等)
    dungeon_name: str  # 副本名称
    battle_text: List[str]  # Boss 战时特殊文本
    routes: List[MoveStep]  # 路线 (如 ["路线1", "路线2"])


@dataclass(frozen=True)
class EnemyMeta:
    """敌人元数据类 - 用于描述每个敌人"""

    ENEMIES: ClassVar[dict[str, "EnemyMeta"]] = {}

    id: str  # 唯一标识，I18nText.xxx
    name: str  # 显示名称，仅作开发调试用，将id翻译成系统语言，不可用于判断，得用id
    species: EnemySpecies  # 物种/种族 (如呓语种、啸叫种等)
    rank: EnemyRank  # 阶级/等级 (如轻波级、巨浪级等)
    cost: EnemyCost  # 消耗值
    icon: EnemyIcon  # 图标
    version: EnemyVersion  # 实装版本
    sonata: List[SonataEffect]  # 奏鸣效果
    elements: List[EnemyElement]  # 元素属性列表 (拥有该属性即对该属性有抗性)
    prefer_quick: bool = False  # 是否优先从快速菜单进入 (True=快速菜单, False=野外)
    boss_meta: Optional[BossMeta] = None  # Boss 信息 (非 Boss 敌人为 None)
    quick_boss_meta: Optional[QuickBossMeta] = None  # 快速挑战 Boss 信息 (不支持快速挑战或非 Boss 为 None)

    def __post_init__(self):
        if self.prefer_quick:
            if not self.quick_boss_meta:
                raise ValueError("quick_boss_meta is empty")
        else:
            if not self.boss_meta:
                raise ValueError("boss_meta is empty")

        if not self.id:
            raise ValueError("id is empty")
        if self.id in self.ENEMIES:
            raise ValueError(f"Duplicate enemy id: {self.id}")

        # if not self.battle_text:
        #     raise ValueError("battle_text is empty")

        self.ENEMIES[self.id] = self

    @property
    def is_dungeon(self) -> bool:
        """是否是独立空间的副本boss，相对的为野外boss"""
        # 菜单直接挑战的都在独立空间
        if self.prefer_quick:
            return True
        # 野外的
        return self.boss_meta.is_dungeon

    @property
    def battle_text(self) -> List[str]:
        """战斗文本，如左侧击败、顶部boss名"""
        if self.prefer_quick:
            return self.quick_boss_meta.battle_text
        return self.boss_meta.battle_text

    @property
    def auto_respawn(self) -> bool:
        """是否自动刷新，部分梦魇boss"""
        return bool(not self.prefer_quick and self.boss_meta and self.boss_meta.auto_respawn)

    @property
    def routes(self) -> List[MoveStep]:
        if self.prefer_quick:
            return self.quick_boss_meta.routes
        return self.boss_meta.routes


class Enemy:
    Dreamless = EnemyMeta(
        id=I18nText.EnemyDreamless,
        name=_tr(I18nText.EnemyDreamless),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    FallacyOfNoReturn = EnemyMeta(
        id=I18nText.EnemyFallacyOfNoReturn,
        name=_tr(I18nText.EnemyFallacyOfNoReturn),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    LampylumenMyriad = EnemyMeta(
        id=I18nText.EnemyLampylumenMyriad,
        name=_tr(I18nText.EnemyLampylumenMyriad),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    BellBorneGeochelone = EnemyMeta(
        id=I18nText.EnemyBellBorneGeochelone,
        name=_tr(I18nText.EnemyBellBorneGeochelone),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=True,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=QuickBossMeta(
            name=_tr(I18nText.EnemyBellBorneGeochelone),
            menu=I18nText.WeeklyChallenge,
            dungeon_name=I18nText.BellOfArchaicChants,
            battle_text=[I18nText.DefeatTheEnemies],
            routes=[],
        ),
    )

    InfernoRider = EnemyMeta(
        id=I18nText.EnemyInfernoRider,
        name=_tr(I18nText.EnemyInfernoRider),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    ImpermanenceHeron = EnemyMeta(
        id=I18nText.EnemyImpermanenceHeron,
        name=_tr(I18nText.EnemyImpermanenceHeron),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=True,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=QuickBossMeta(
            name=_tr(I18nText.EnemyImpermanenceHeron),
            menu=I18nText.BossChallenge,
            dungeon_name=I18nText.EnemyImpermanenceHeron,
            battle_text=[I18nText.DefeatTheEnemies],
            routes=[],
        ),
    )

    MechAbomination = EnemyMeta(
        id=I18nText.EnemyMechAbomination,
        name=_tr(I18nText.EnemyMechAbomination),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    MourningAix = EnemyMeta(
        id=I18nText.EnemyMourningAix,
        name=_tr(I18nText.EnemyMourningAix),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    ThunderingMephis = EnemyMeta(
        id=I18nText.EnemyThunderingMephis,
        name=_tr(I18nText.EnemyThunderingMephis),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    TempestMephis = EnemyMeta(
        id=I18nText.EnemyTempestMephis,
        name=_tr(I18nText.EnemyTempestMephis),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    FeilianBeringal = EnemyMeta(
        id=I18nText.EnemyFeilianBeringal,
        name=_tr(I18nText.EnemyFeilianBeringal),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Crownless = EnemyMeta(
        id=I18nText.EnemyCrownless,
        name=_tr(I18nText.EnemyCrownless),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Jue = EnemyMeta(
        id=I18nText.EnemyJue,
        name=_tr(I18nText.EnemyJue),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    SentryConstruct = EnemyMeta(
        id=I18nText.EnemySentryConstruct,
        name=_tr(I18nText.EnemySentryConstruct),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Hecate = EnemyMeta(
        id=I18nText.EnemyHecate,
        name=_tr(I18nText.EnemyHecate),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Lorelei = EnemyMeta(
        id=I18nText.EnemyLorelei,
        name=_tr(I18nText.EnemyLorelei),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    DragonOfDirge = EnemyMeta(
        id=I18nText.EnemyDragonOfDirge,
        name=_tr(I18nText.EnemyDragonOfDirge),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareFeilianBeringal = EnemyMeta(
        id=I18nText.EnemyNightmareFeilianBeringal,
        name=_tr(I18nText.EnemyNightmareFeilianBeringal),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareImpermanenceHeron = EnemyMeta(
        id=I18nText.EnemyNightmareImpermanenceHeron,
        name=_tr(I18nText.EnemyNightmareImpermanenceHeron),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareTempestMephis = EnemyMeta(
        id=I18nText.EnemyNightmareTempestMephis,
        name=_tr(I18nText.EnemyNightmareTempestMephis),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareThunderingMephis = EnemyMeta(
        id=I18nText.EnemyNightmareThunderingMephis,
        name=_tr(I18nText.EnemyNightmareThunderingMephis),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareCrownless = EnemyMeta(
        id=I18nText.EnemyNightmareCrownless,
        name=_tr(I18nText.EnemyNightmareCrownless),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareInfernoRider = EnemyMeta(
        id=I18nText.EnemyNightmareInfernoRider,
        name=_tr(I18nText.EnemyNightmareInfernoRider),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareMourningAix = EnemyMeta(
        id=I18nText.EnemyNightmareMourningAix,
        name=_tr(I18nText.EnemyNightmareMourningAix),
        species=EnemySpecies.NightmareTacetDiscord,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.EternalRadiance,
        elements=[EnemyElement.Spectro],
        prefer_quick=False,
        boss_meta=BossMeta(
            name=I18nText.EnemyNightmareMourningAix,
            is_dungeon=False,
            dungeon_name=None,
            auto_respawn=True,
            enter_text=None,
            battle_text=[I18nText.CombatNightmareMourningAix],
            routes=[Run.forward(3.6)]
        ),
        quick_boss_meta=None,
    )

    NightmareLampylumenMyriad = EnemyMeta(
        id=I18nText.EnemyNightmareLampylumenMyriad,
        name=_tr(I18nText.EnemyNightmareLampylumenMyriad),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Fleurdelys = EnemyMeta(
        id=I18nText.EnemyFleurdelys,
        name=_tr(I18nText.EnemyFleurdelys),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareKelpie = EnemyMeta(
        id=I18nText.EnemyNightmareKelpie,
        name=_tr(I18nText.EnemyNightmareKelpie),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    LionessOfGlory = EnemyMeta(
        id=I18nText.EnemyLionessOfGlory,
        name=_tr(I18nText.EnemyLionessOfGlory),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareHecate = EnemyMeta(
        id=I18nText.EnemyNightmareHecate,
        name=_tr(I18nText.EnemyNightmareHecate),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Fenrico = EnemyMeta(
        id=I18nText.EnemyFenrico,
        name=_tr(I18nText.EnemyFenrico),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    LadyOfTheSea = EnemyMeta(
        id=I18nText.EnemyLadyOfTheSea,
        name=_tr(I18nText.EnemyLadyOfTheSea),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    TheFalseSovereign = EnemyMeta(
        id=I18nText.EnemyTheFalseSovereign,
        name=_tr(I18nText.EnemyTheFalseSovereign),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=True,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=QuickBossMeta(
            name=_tr(I18nText.EnemyTheFalseSovereign),
            menu=I18nText.BossChallenge,
            dungeon_name=I18nText.EnemyTheFalseSovereign,
            battle_text=[I18nText.DefeatTheEnemies],
            routes=[],
        ),
    )

    ThrenodianLeviathan = EnemyMeta(
        id=I18nText.EnemyThrenodianLeviathan,
        name=_tr(I18nText.EnemyThrenodianLeviathan),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Hyvatia = EnemyMeta(
        id=I18nText.EnemyHyvatia,
        name=_tr(I18nText.EnemyHyvatia),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    ReactorHusk = EnemyMeta(
        id=I18nText.EnemyReactorHusk,
        name=_tr(I18nText.EnemyReactorHusk),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Sigillum = EnemyMeta(
        id=I18nText.EnemySigillum,
        name=_tr(I18nText.EnemySigillum),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NamelessExplorer = EnemyMeta(
        id=I18nText.EnemyNamelessExplorer,
        name=_tr(I18nText.EnemyNamelessExplorer),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    Denia = EnemyMeta(
        id=I18nText.EnemyDenia,
        name=_tr(I18nText.EnemyDenia),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    NightmareAdamSmasher = EnemyMeta(
        id=I18nText.EnemyNightmareAdamSmasher,
        name=_tr(I18nText.EnemyNightmareAdamSmasher),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=True,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=QuickBossMeta(
            name=_tr(I18nText.EnemyNightmareAdamSmasher),
            menu=I18nText.BossChallenge,
            dungeon_name=I18nText.EnemyNightmareAdamSmasher,
            battle_text=[I18nText.DefeatTheEnemies],
            routes=[],
        ),
    )

    MyriadSnareRustfireChassis = EnemyMeta(
        id=I18nText.EnemyMyriadSnareRustfireChassis,
        name=_tr(I18nText.EnemyMyriadSnareRustfireChassis),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V3_5,
        sonata=[SonataEffect.HeartOfEvilsPurge, SonataEffect.LampOfNetherRoad],
        elements=[EnemyElement.Fusion],
        prefer_quick=True,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=QuickBossMeta(
            name="",
            menu=I18nText.BossChallenge,
            dungeon_name=I18nText.EnemyThousandPuppetPavilion,
            battle_text=[I18nText.DefeatTheEnemies],
            routes=[],
        ),
    )

    ThousandPuppetPavilion = EnemyMeta(
        id=I18nText.EnemyThousandPuppetPavilion,
        name=_tr(I18nText.EnemyThousandPuppetPavilion),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=[SonataEffect.FreezingFrost],
        elements=[EnemyElement.Havoc],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    CalamityEffigy = EnemyMeta(
        id=I18nText.EnemyCalamityEffigy,
        name=_tr(I18nText.EnemyCalamityEffigy),
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V3_6,
        sonata=[SonataEffect.HeartOfEvilsPurge, SonataEffect.LampOfNetherRoad],
        elements=[EnemyElement.Aero],
        prefer_quick=False,
        boss_meta=BossMeta(
            name="深渊低语者",
            is_dungeon=True,
            dungeon_name="沉睡深渊",
            auto_respawn=False,
            enter_text="你踏入了沉睡深渊的深处",
            battle_text=[],
            routes=[],
        ),
        quick_boss_meta=None,
    )

    @staticmethod
    def enemies():
        return EnemyMeta.ENEMIES

    @classmethod
    def from_key(cls, key: str):
        enemy = cls.enemies().get(key)
        if not enemy:
            raise ValueError("Key not found")
        return enemy


class EnemyHpBar:
    """敌人血条"""

    @staticmethod
    def detect(img: np.ndarray) -> float | None:
        # ===== 调试参数 =====

        left = AnchorPoint(456, 40, Align.Center | Align.Top)
        right = AnchorPoint(829, 40, Align.Center | Align.Top)

        # 渐变两端颜色，BGR
        left_color = (68, 179, 255)
        right_color = (8, 37, 255)

        # 黑条颜色，BGR
        black_color = (44, 24, 9)

        # 渐变颜色容差
        color_tolerance = 10

        # 黑条颜色容差
        black_tolerance = 35

        # 是否要求必须存在渐变
        require_gradient = False

        # 不要求渐变时，黑条至少占血条的多少比例
        # 例如 0.9 = 90%
        min_black_ratio = 0.9

        # ====================

        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        left = scaler.as_point(left)
        right = scaler.as_point(right)

        height, width = img.shape[:2]

        x1 = max(0, min(left.x, width - 1))
        x2 = max(0, min(right.x, width - 1))
        y = max(0, min(left.y, height - 1))

        if x1 > x2:
            x1, x2 = x2, x1

        pixels = img[y, x1:x2 + 1]

        if len(pixels) == 0:
            return None

        left_color = np.array(left_color, dtype=np.int16)
        right_color = np.array(right_color, dtype=np.int16)
        black_color = np.array(black_color, dtype=np.int16)

        color_min = np.minimum(left_color, right_color) - color_tolerance

        color_max = np.maximum(left_color, right_color) + color_tolerance

        def is_black(pixel: np.ndarray):
            pixel = pixel.astype(np.int16)
            return np.all(np.abs(pixel - black_color) <= black_tolerance)

        def is_gradient(pixel: np.ndarray):
            pixel = pixel.astype(np.int16)
            return np.all(
                (pixel >= color_min) & (pixel <= color_max)
            )

        # --------------------------------------------------
        # 像素分类
        #
        # 0 = 未知
        # 1 = 渐变
        # 2 = 黑色
        # --------------------------------------------------

        states = np.zeros(len(pixels), dtype=np.uint8)

        for i, pixel in enumerate(pixels):
            if is_black(pixel):
                states[i] = 2
            elif is_gradient(pixel):
                states[i] = 1

        gradient_count = np.count_nonzero(states == 1)
        black_count = np.count_nonzero(states == 2)

        total = len(states)
        black_ratio = black_count / total

        # --------------------------------------------------
        # 1. 要求必须存在渐变
        # --------------------------------------------------

        if require_gradient:
            if gradient_count == 0:
                return None

        # --------------------------------------------------
        # 2. 没有渐变
        #
        # 此时必须有足够比例的黑条，
        # 否则不能认为这是血条。
        # --------------------------------------------------

        if gradient_count == 0:
            if black_ratio >= min_black_ratio:
                return 0.0

            return None

        # --------------------------------------------------
        # 3. 有渐变
        #
        # 如果几乎没有黑条，就是满血。
        # --------------------------------------------------

        if black_count == 0:
            return 1.0

        # --------------------------------------------------
        # 4. 有渐变 + 黑条
        #
        # 找 [渐变][黑条] 的分界位置
        # --------------------------------------------------

        black_start = None

        # 连续几个黑像素才认为真正进入黑条
        min_black_pixels = 3

        for i in range(len(states) - min_black_pixels + 1):
            segment = states[i:i + min_black_pixels]

            if np.all(segment == 2):
                black_start = i
                break

        # 有黑像素，但没有形成可靠的黑色区域
        # 认为只是噪声，仍然当作满血
        if black_start is None:
            return 1.0

        # --------------------------------------------------
        # 5. 黑条从最左边开始
        #
        # 渐变已经完全消失。
        # --------------------------------------------------

        if black_start == 0:
            return 0.0

        # --------------------------------------------------
        # 6. 计算血量比例
        # --------------------------------------------------

        hp = black_start / total

        return float(np.clip(hp, 0.0, 1.0))


class EnemyVsBar:
    """共振度 Vibration Strength Bar"""

    @staticmethod
    def detect(img: np.ndarray) -> float:
        # ==================== 调试参数 ====================

        # 架势条左右端点
        left = AnchorPoint(456, 52, Align.Center | Align.Top)
        right = AnchorPoint(829, 52, Align.Center | Align.Top)

        # 架势条两种有效颜色，BGR
        white_color = (255, 255, 255)
        yellow_color = (24, 235, 255)

        # 颜色容差
        color_tolerance = 20

        # ==================================================

        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        left = scaler.as_point(left)
        right = scaler.as_point(right)

        height, width = img.shape[:2]

        # 防止坐标超出图片范围
        x1 = max(0, min(left.x, width - 1))
        x2 = max(0, min(right.x, width - 1))
        y = max(0, min(left.y, height - 1))

        if x1 > x2:
            x1, x2 = x2, x1

        pixels = img[y, x1:x2 + 1].astype(np.int16)

        # 区域无效时返回 0
        if len(pixels) == 0:
            return 0.0

        white_color = np.asarray(white_color, dtype=np.int16)

        yellow_color = np.asarray(yellow_color, dtype=np.int16)

        # --------------------------------------------------
        # 判断像素是否接近指定颜色
        # --------------------------------------------------

        def is_color(pixel: np.ndarray, color: np.ndarray):
            return np.all(np.abs(pixel - color) <= color_tolerance)

        # --------------------------------------------------
        # 根据最左边的像素判断当前架势条颜色
        #
        # 白色 → 当前是白色架势条
        # 黄色 → 当前是黄色架势条
        # 其他 → 没有检测到架势条
        # --------------------------------------------------

        first_pixel = pixels[0]

        if is_color(first_pixel, white_color):
            stance_color = white_color
        elif is_color(first_pixel, yellow_color):
            stance_color = yellow_color
        else:
            return 0.0

        stance_end = None

        for i, pixel in enumerate(pixels):
            if not is_color(pixel, stance_color):
                stance_end = i
                break

        # --------------------------------------------------
        # 整条都是同一种有效颜色
        # --------------------------------------------------

        if stance_end is None:
            return 1.0

        # --------------------------------------------------
        # 计算架势条比例
        # --------------------------------------------------

        ratio = stance_end / len(pixels)

        return float(np.clip(ratio, 0.0, 1.0))


if __name__ == '__main__':
    print(Enemy.enemies())

    import ctypes

    buf = ctypes.create_unicode_buffer(85)
    ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)

    print(buf.value)