import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from src.core.i18n import I18nText
from src.core.movement import Run, MoveStep

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class EnemyMeta:
    """敌人元数据类 - 用于描述每个敌人"""

    id: str  # 唯一标识
    name: str  # 显示名称
    species: EnemySpecies  # 物种/种族 (如呓语种、啸叫种等)
    rank: EnemyRank  # 阶级/等级 (如轻波级、巨浪级等)
    cost: EnemyCost  # 消耗值
    icon: EnemyIcon  # 图标
    version: EnemyVersion  # 实装版本
    sonata: SonataEffect  # 奏鸣效果
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

    @property
    def is_dungeon(self) -> bool:
        """是否是独立空间的副本boss，相对的为大世界boss"""
        if self.prefer_quick:
            return True
        return self.boss_meta.is_dungeon

    @property
    def battle_text(self) -> List[str]:
        """战斗文本，如左侧击败、顶部boss名"""
        if self.prefer_quick:
            return self.quick_boss_meta.battle_text
        return self.boss_meta.battle_text


class Enemy:
    Dreamless = EnemyMeta(
        id="test_001",
        name=I18nText.EnemyDreamless,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyFallacyOfNoReturn,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyLampylumenMyriad,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyBellBorneGeochelone,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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

    InfernoRider = EnemyMeta(
        id="test_001",
        name=I18nText.EnemyInfernoRider,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyImpermanenceHeron,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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

    MechAbomination = EnemyMeta(
        id="test_001",
        name=I18nText.EnemyMechAbomination,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyMourningAix,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyThunderingMephis,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyTempestMephis,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyFeilianBeringal,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyCrownless,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyJue,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemySentryConstruct,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyHecate,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyLorelei,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyDragonOfDirge,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareFeilianBeringal,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareImpermanenceHeron,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareTempestMephis,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareThunderingMephis,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareCrownless,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareInfernoRider,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareMourningAix,
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
        id="test_001",
        name=I18nText.EnemyNightmareLampylumenMyriad,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyFleurdelys,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareKelpie,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyLionessOfGlory,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareHecate,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyFenrico,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyLadyOfTheSea,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyTheFalseSovereign,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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

    ThrenodianLeviathan = EnemyMeta(
        id="test_001",
        name=I18nText.EnemyThrenodianLeviathan,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyHyvatia,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyReactorHusk,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemySigillum,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNamelessExplorer,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyDenia,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyNightmareAdamSmasher,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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

    MyriadSnareRustfireChassis = EnemyMeta(
        id="test_001",
        name=I18nText.EnemyMyriadSnareRustfireChassis,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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

    ThousandPuppetPavilion = EnemyMeta(
        id="test_001",
        name=I18nText.EnemyThousandPuppetPavilion,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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
        id="test_001",
        name=I18nText.EnemyCalamityEffigy,
        species=EnemySpecies.Whisperin,
        rank=EnemyRank.CalamityClass,
        cost=EnemyCost.Cost4,
        icon=EnemyIcon.Icon1,
        version=EnemyVersion.V1_0,
        sonata=SonataEffect.FreezingFrost,
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


