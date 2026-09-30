from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from src.core.i18n import I18nText, I18nTr


class DungeonIcon(Enum):
    """图标枚举 - 对应图片文件名"""
    Icon1 = "icon1.png"
    Icon2 = "icon2.png"
    Icon3 = "icon3.png"
    Icon4 = "icon4.png"
    Icon5 = "icon5.png"


@dataclass(frozen=True)
class DungeonMeta:
    id: str
    localized_name: str
    menu: str
    register: List[dict[str, "DungeonMeta"]]
    icon: DungeonIcon
    region: str
    waveplate: Optional[int]
    enemy_id: Optional[str]
    rewards: Optional[List[str]]

    def __post_init__(self):
        if not self.id:
            raise ValueError("id is empty")

        if self.register is not None and len(self.register) > 0:
            for mapping in self.register:
                mapping[self.id] = self

    def __eq__(self, other):
        if not isinstance(other, DungeonMeta):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


@dataclass(frozen=True)
class ForgeryChallengeMeta(DungeonMeta):
    weapon: str


class Dungeon:
    ForgeryChallenge: dict[str, ForgeryChallengeMeta] = {}
    BossChallenge: dict[str, DungeonMeta] = {}
    TacetSuppression: dict[str, DungeonMeta] = {}
    WeeklyChallenge: dict[str, DungeonMeta] = {}
    TacetDiscordNest: dict[str, DungeonMeta] = {}
    NightmarePurification: dict[str, DungeonMeta] = {}


class DungeonForgeryChallenge:
    # ------- ForgeryChallenge -------

    WingfallChasm = ForgeryChallengeMeta(
        id=I18nText.WingfallChasm,
        localized_name=I18nTr.l10n(I18nText.WingfallChasm),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Polarizer],
        weapon=I18nText.Sword,
    )

    SilentChasm = ForgeryChallengeMeta(
        id=I18nText.SilentChasm,
        localized_name=I18nTr.l10n(I18nText.SilentChasm),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.String],
        weapon=I18nText.Rectifier,
    )

    SplitChasm = ForgeryChallengeMeta(
        id=I18nText.SplitChasm,
        localized_name=I18nTr.l10n(I18nText.SplitChasm),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.CarvedCrystal],
        weapon=I18nText.Broadblade,
    )

    ErodedChasm = ForgeryChallengeMeta(
        id=I18nText.ErodedChasm,
        localized_name=I18nTr.l10n(I18nText.ErodedChasm),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.WavewornShard],
        weapon=I18nText.Gauntlets,
    )

    AshenChasm = ForgeryChallengeMeta(
        id=I18nText.AshenChasm,
        localized_name=I18nTr.l10n(I18nText.AshenChasm),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Combustor],
        weapon=I18nText.Pistols,
    )

    FallenSanctum = ForgeryChallengeMeta(
        id=I18nText.FallenSanctum,
        localized_name=I18nTr.l10n(I18nText.FallenSanctum),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Polarizer],
        weapon=I18nText.Sword,
    )

    LessonInSunset = ForgeryChallengeMeta(
        id=I18nText.LessonInSunset,
        localized_name=I18nTr.l10n(I18nText.LessonInSunset),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.String],
        weapon=I18nText.Rectifier,
    )

    StrickenSanctum = ForgeryChallengeMeta(
        id=I18nText.StrickenSanctum,
        localized_name=I18nTr.l10n(I18nText.StrickenSanctum),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.CarvedCrystal],
        weapon=I18nText.Broadblade,
    )

    LessonInVoid = ForgeryChallengeMeta(
        id=I18nText.LessonInVoid,
        localized_name=I18nTr.l10n(I18nText.LessonInVoid),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.WavewornShard],
        weapon=I18nText.Gauntlets,
    )

    LessonInEmbers = ForgeryChallengeMeta(
        id=I18nText.LessonInEmbers,
        localized_name=I18nTr.l10n(I18nText.LessonInEmbers),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Combustor],
        weapon=I18nText.Pistols,
    )

    GardenOfSalvation = ForgeryChallengeMeta(
        id=I18nText.GardenOfSalvation,
        localized_name=I18nTr.l10n(I18nText.GardenOfSalvation),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.MetallicDrip],
        weapon=I18nText.Sword,
    )

    AbyssOfInitiation = ForgeryChallengeMeta(
        id=I18nText.AbyssOfInitiation,
        localized_name=I18nTr.l10n(I18nText.AbyssOfInitiation),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Helix],
        weapon=I18nText.Rectifier,
    )

    GardenOfAdoration = ForgeryChallengeMeta(
        id=I18nText.GardenOfAdoration,
        localized_name=I18nTr.l10n(I18nText.GardenOfAdoration),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.WavewornResidue],
        weapon=I18nText.Broadblade,
    )

    AbyssOfSacrifice = ForgeryChallengeMeta(
        id=I18nText.AbyssOfSacrifice,
        localized_name=I18nTr.l10n(I18nText.AbyssOfSacrifice),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Cadence],
        weapon=I18nText.Gauntlets,
    )

    AbyssOfConfession = ForgeryChallengeMeta(
        id=I18nText.AbyssOfConfession,
        localized_name=I18nTr.l10n(I18nText.AbyssOfConfession),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Phlogiston],
        weapon=I18nText.Pistols,
    )

    FlamingRemnants = ForgeryChallengeMeta(
        id=I18nText.FlamingRemnants,
        localized_name=I18nTr.l10n(I18nText.FlamingRemnants),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.MetallicDrip],
        weapon=I18nText.Sword,
    )

    MistyForest = ForgeryChallengeMeta(
        id=I18nText.MistyForest,
        localized_name=I18nTr.l10n(I18nText.MistyForest),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Helix],
        weapon=I18nText.Rectifier,
    )

    ErodedRuins = ForgeryChallengeMeta(
        id=I18nText.ErodedRuins,
        localized_name=I18nTr.l10n(I18nText.ErodedRuins),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.WavewornResidue],
        weapon=I18nText.Broadblade,
    )

    MoonlitGroves = ForgeryChallengeMeta(
        id=I18nText.MoonlitGroves,
        localized_name=I18nTr.l10n(I18nText.MoonlitGroves),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Cadence],
        weapon=I18nText.Gauntlets,
    )

    MarigoldWoods = ForgeryChallengeMeta(
        id=I18nText.MarigoldWoods,
        localized_name=I18nTr.l10n(I18nText.MarigoldWoods),
        menu=I18nText.ForgeryChallenge,
        register=[Dungeon.ForgeryChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=[I18nText.Phlogiston],
        weapon=I18nText.Pistols,
    )


class DungeonBossChallenge:
    # ------- BossChallenge -------

    EnemyCalamityEffigy = DungeonMeta(
        id=I18nText.EnemyCalamityEffigy,
        localized_name=I18nTr.l10n(I18nText.EnemyCalamityEffigy),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyCalamityEffigy,
        rewards=[I18nText.ForgedEmpyreansSigh],
    )

    EnemyMyriadSnareRustfireChassis = DungeonMeta(
        id=I18nText.EnemyMyriadSnareRustfireChassis,
        localized_name=I18nTr.l10n(I18nText.EnemyMyriadSnareRustfireChassis),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyMyriadSnareRustfireChassis,
        rewards=[I18nText.SolidaritysLoneflame],
    )

    EnemyNightmareAdamSmasher = DungeonMeta(
        id=I18nText.EnemyNightmareAdamSmasher,
        localized_name=I18nTr.l10n(I18nText.EnemyNightmareAdamSmasher),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=I18nText.EnemyNightmareAdamSmasher,
        rewards=[I18nText.NightmareFlashdrive],
    )

    EnemyNamelessExplorer = DungeonMeta(
        id=I18nText.EnemyNamelessExplorer,
        localized_name=I18nTr.l10n(I18nText.EnemyNamelessExplorer),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=I18nText.EnemyNamelessExplorer,
        rewards=[I18nText.OurChoice],
    )

    EnemyHyvatia = DungeonMeta(
        id=I18nText.EnemyHyvatia,
        localized_name=I18nTr.l10n(I18nText.EnemyHyvatia),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=I18nText.EnemyHyvatia,
        rewards=[I18nText.SuncovetersReach],
    )

    EnemyReactorHusk = DungeonMeta(
        id=I18nText.EnemyReactorHusk,
        localized_name=I18nTr.l10n(I18nText.EnemyReactorHusk),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=I18nText.EnemyReactorHusk,
        rewards=[I18nText.BurningJudgment],
    )

    EnemyLadyOfTheSea = DungeonMeta(
        id=I18nText.EnemyLadyOfTheSea,
        localized_name=I18nTr.l10n(I18nText.EnemyLadyOfTheSea),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyLadyOfTheSea,
        rewards=[I18nText.AbyssalHusk],
    )

    EnemyTheFalseSovereign = DungeonMeta(
        id=I18nText.EnemyTheFalseSovereign,
        localized_name=I18nTr.l10n(I18nText.EnemyTheFalseSovereign),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyTheFalseSovereign,
        rewards=[I18nText.BlightedCrownOfPuppetKing],
    )

    EnemyFenrico = DungeonMeta(
        id=I18nText.EnemyFenrico,
        localized_name=I18nTr.l10n(I18nText.EnemyFenrico),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyFenrico,
        rewards=[I18nText.TruthInLies],
    )

    EnemyFenrico = DungeonMeta(
        id=I18nText.EnemyFenrico,
        localized_name=I18nTr.l10n(I18nText.EnemyFenrico),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyFenrico,
        rewards=[I18nText.TruthInLies],
    )

    EnemyLionessOfGlory = DungeonMeta(
        id=I18nText.EnemyLionessOfGlory,
        localized_name=I18nTr.l10n(I18nText.EnemyLionessOfGlory),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyLionessOfGlory,
        rewards=[I18nText.UnfadingGlory],
    )

    EnemyDragonOfDirge = DungeonMeta(
        id=I18nText.EnemyDragonOfDirge,
        localized_name=I18nTr.l10n(I18nText.EnemyDragonOfDirge),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyDragonOfDirge,
        rewards=[I18nText.BlazingBone],
    )

    EnemyLorelei = DungeonMeta(
        id=I18nText.EnemyLorelei,
        localized_name=I18nTr.l10n(I18nText.EnemyLorelei),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyLorelei,
        rewards=[I18nText.CleansingConch],
    )

    EnemySentryConstruct = DungeonMeta(
        id=I18nText.EnemySentryConstruct,
        localized_name=I18nTr.l10n(I18nText.EnemySentryConstruct),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemySentryConstruct,
        rewards=[I18nText.PlatinumCore],
    )

    EnemyFallacyOfNoReturn = DungeonMeta(
        id=I18nText.EnemyFallacyOfNoReturn,
        localized_name=I18nTr.l10n(I18nText.EnemyFallacyOfNoReturn),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookTheBlackShores,
        waveplate=60,
        enemy_id=I18nText.EnemyFallacyOfNoReturn,
        rewards=[I18nText.TopologicalConfinement],
    )

    EnemyCrownless = DungeonMeta(
        id=I18nText.EnemyCrownless,
        localized_name=I18nTr.l10n(I18nText.EnemyCrownless),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyCrownless,
        rewards=[I18nText.StrifeTacetCore],
    )

    EnemyThunderingMephis = DungeonMeta(
        id=I18nText.EnemyThunderingMephis,
        localized_name=I18nTr.l10n(I18nText.EnemyThunderingMephis),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyThunderingMephis,
        rewards=[I18nText.HiddenThunderTacetCore],
    )

    EnemyTempestMephis = DungeonMeta(
        id=I18nText.EnemyTempestMephis,
        localized_name=I18nTr.l10n(I18nText.EnemyTempestMephis),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyTempestMephis,
        rewards=[I18nText.ThunderingTacetCore],
    )

    EnemyInfernoRider = DungeonMeta(
        id=I18nText.EnemyInfernoRider,
        localized_name=I18nTr.l10n(I18nText.EnemyInfernoRider),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyInfernoRider,
        rewards=[I18nText.RageTacetCore],
    )

    EnemyFeilianBeringal = DungeonMeta(
        id=I18nText.EnemyFeilianBeringal,
        localized_name=I18nTr.l10n(I18nText.EnemyFeilianBeringal),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyFeilianBeringal,
        rewards=[I18nText.RoaringRockFist],
    )

    EnemyMourningAix = DungeonMeta(
        id=I18nText.EnemyMourningAix,
        localized_name=I18nTr.l10n(I18nText.EnemyMourningAix),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyMourningAix,
        rewards=[I18nText.ElegyTacetCore],
    )

    EnemyImpermanenceHeron = DungeonMeta(
        id=I18nText.EnemyImpermanenceHeron,
        localized_name=I18nTr.l10n(I18nText.EnemyImpermanenceHeron),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyImpermanenceHeron,
        rewards=[I18nText.GoldDissolvingFeather],
    )

    EnemyLampylumenMyriad = DungeonMeta(
        id=I18nText.EnemyLampylumenMyriad,
        localized_name=I18nTr.l10n(I18nText.EnemyLampylumenMyriad),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyLampylumenMyriad,
        rewards=[I18nText.SoundKeepingTacetCore],
    )

    EnemyMechAbomination = DungeonMeta(
        id=I18nText.EnemyMechAbomination,
        localized_name=I18nTr.l10n(I18nText.EnemyMechAbomination),
        menu=I18nText.BossChallenge,
        register=[Dungeon.BossChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyMechAbomination,
        rewards=[I18nText.GroupAbominationTacetCore],
    )


class DungeonTacetSuppression:
    # ------- TacetSuppression -------

    TacetFieldHeartOfStillness = DungeonMeta(
        id=I18nText.TacetFieldHeartOfStillness,
        localized_name=I18nTr.l10n(I18nText.TacetFieldHeartOfStillness),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldHeartOfFlames = DungeonMeta(
        id=I18nText.TacetFieldHeartOfFlames,
        localized_name=I18nTr.l10n(I18nText.TacetFieldHeartOfFlames),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    WesternFangPeaksTacetField = DungeonMeta(
        id=I18nText.WesternFangPeaksTacetField,
        localized_name=I18nTr.l10n(I18nText.WesternFangPeaksTacetField),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    EasternXuanPeaksTacetField = DungeonMeta(
        id=I18nText.EasternXuanPeaksTacetField,
        localized_name=I18nTr.l10n(I18nText.EasternXuanPeaksTacetField),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldSolisiaLanding = DungeonMeta(
        id=I18nText.TacetFieldSolisiaLanding,
        localized_name=I18nTr.l10n(I18nText.TacetFieldSolisiaLanding),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldFrostlandsTransitPort = DungeonMeta(
        id=I18nText.TacetFieldFrostlandsTransitPort,
        localized_name=I18nTr.l10n(I18nText.TacetFieldFrostlandsTransitPort),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldMountGjallar = DungeonMeta(
        id=I18nText.TacetFieldMountGjallar,
        localized_name=I18nTr.l10n(I18nText.TacetFieldMountGjallar),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldMawburrowDesert = DungeonMeta(
        id=I18nText.TacetFieldMawburrowDesert,
        localized_name=I18nTr.l10n(I18nText.TacetFieldMawburrowDesert),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldStagnantRun = DungeonMeta(
        id=I18nText.TacetFieldStagnantRun,
        localized_name=I18nTr.l10n(I18nText.TacetFieldStagnantRun),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldMournfellCanyon = DungeonMeta(
        id=I18nText.TacetFieldMournfellCanyon,
        localized_name=I18nTr.l10n(I18nText.TacetFieldMournfellCanyon),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldBeohrWaters = DungeonMeta(
        id=I18nText.TacetFieldBeohrWaters,
        localized_name=I18nTr.l10n(I18nText.TacetFieldBeohrWaters),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldRiccioliIslands = DungeonMeta(
        id=I18nText.TacetFieldRiccioliIslands,
        localized_name=I18nTr.l10n(I18nText.TacetFieldRiccioliIslands),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldFagaceaePeninsula = DungeonMeta(
        id=I18nText.TacetFieldFagaceaePeninsula,
        localized_name=I18nTr.l10n(I18nText.TacetFieldFagaceaePeninsula),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldPenitentsEnd = DungeonMeta(
        id=I18nText.TacetFieldPenitentsEnd,
        localized_name=I18nTr.l10n(I18nText.TacetFieldPenitentsEnd),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldCentralPlains = DungeonMeta(
        id=I18nText.TacetFieldCentralPlains,
        localized_name=I18nTr.l10n(I18nText.TacetFieldCentralPlains),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldDesorockHighlandI = DungeonMeta(
        id=I18nText.TacetFieldDesorockHighlandI,
        localized_name=I18nTr.l10n(I18nText.TacetFieldDesorockHighlandI),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldTigersMaw = DungeonMeta(
        id=I18nText.TacetFieldTigersMaw,
        localized_name=I18nTr.l10n(I18nText.TacetFieldTigersMaw),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldWhiningAixsMire = DungeonMeta(
        id=I18nText.TacetFieldWhiningAixsMire,
        localized_name=I18nTr.l10n(I18nText.TacetFieldWhiningAixsMire),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldPortCityOfGuixu = DungeonMeta(
        id=I18nText.TacetFieldPortCityOfGuixu,
        localized_name=I18nTr.l10n(I18nText.TacetFieldPortCityOfGuixu),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldDesorockHighlandII = DungeonMeta(
        id=I18nText.TacetFieldDesorockHighlandII,
        localized_name=I18nTr.l10n(I18nText.TacetFieldDesorockHighlandII),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )

    TacetFieldDimForest = DungeonMeta(
        id=I18nText.TacetFieldDimForest,
        localized_name=I18nTr.l10n(I18nText.TacetFieldDimForest),
        menu=I18nText.TacetSuppression,
        register=[Dungeon.TacetSuppression],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=None,
        rewards=None,
    )


class DungeonWeeklyChallenge:
    # ------- WeeklyChallenge -------

    OrdinanceOfTheInevitable = DungeonMeta(
        id=I18nText.OrdinanceOfTheInevitable,
        localized_name=I18nTr.l10n(I18nText.OrdinanceOfTheInevitable),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=I18nText.EnemySuhsinTheInevitable,
        rewards=[I18nText.SkywardGlazedHeart],
    )

    CourtOfShackledSouls = DungeonMeta(
        id=I18nText.CourtOfShackledSouls,
        localized_name=I18nTr.l10n(I18nText.CourtOfShackledSouls),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookMengzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyThousandPuppetPavilion,
        rewards=[I18nText.SkywardGlazedHeart],
    )

    SeedOfIllusoryOrigin = DungeonMeta(
        id=I18nText.SeedOfIllusoryOrigin,
        localized_name=I18nTr.l10n(I18nText.SeedOfIllusoryOrigin),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=I18nText.EnemyDenia,
        rewards=[I18nText.WeWhoQuestion],
    )

    GateOfTheLostStar = DungeonMeta(
        id=I18nText.GateOfTheLostStar,
        localized_name=I18nTr.l10n(I18nText.GateOfTheLostStar),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookLahaiRoi,
        waveplate=60,
        enemy_id=I18nText.EnemySigillum,
        rewards=[I18nText.GoldInMemory],
    )

    CinderniteApocalypse = DungeonMeta(
        id=I18nText.CinderniteApocalypse,
        localized_name=I18nTr.l10n(I18nText.CinderniteApocalypse),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyThrenodianLeviathan,
        rewards=[I18nText.CurseOfTheAbyss],
    )

    TheWheelOfBrokenFate = DungeonMeta(
        id=I18nText.TheWheelOfBrokenFate,
        localized_name=I18nTr.l10n(I18nText.TheWheelOfBrokenFate),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyFleurdelys,
        rewards=[I18nText.WhenIrisesBloom],
    )

    BeyondTheCrimsonCurtain = DungeonMeta(
        id=I18nText.BeyondTheCrimsonCurtain,
        localized_name=I18nTr.l10n(I18nText.BeyondTheCrimsonCurtain),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookRinascita,
        waveplate=60,
        enemy_id=I18nText.EnemyHecate,
        rewards=[I18nText.TheNetherworldsStare],
    )

    TheFatedConfrontation = DungeonMeta(
        id=I18nText.TheFatedConfrontation,
        localized_name=I18nTr.l10n(I18nText.TheFatedConfrontation),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyJue,
        rewards=[I18nText.SentinelsDagger],
    )

    StatueOfTheCrownless = DungeonMeta(
        id=I18nText.StatueOfTheCrownless,
        localized_name=I18nTr.l10n(I18nText.StatueOfTheCrownless),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyDreamless,
        rewards=[I18nText.DreamlessFeather],
    )

    ChaoticJuncture = DungeonMeta(
        id=I18nText.ChaoticJuncture,
        localized_name=I18nTr.l10n(I18nText.ChaoticJuncture),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyScarAberrantNightmare,
        rewards=[I18nText.UnendingDestruction],
    )

    BellOfArchaicChants = DungeonMeta(
        id=I18nText.BellOfArchaicChants,
        localized_name=I18nTr.l10n(I18nText.BellOfArchaicChants),
        menu=I18nText.WeeklyChallenge,
        register=[Dungeon.WeeklyChallenge],
        icon=DungeonIcon.Icon1,
        region=I18nText.GuidebookJinzhou,
        waveplate=60,
        enemy_id=I18nText.EnemyBellBorneGeochelone,
        rewards=[I18nText.MonumentBell],
    )


# class DungeonTacetDiscordNest:
#     # ------- TacetDiscordNest -------
#
#     CourtOfShackledSouls = DungeonMeta(
#         id=I18nText.CourtOfShackledSouls,
#         localized_name=I18nTr.l10n(I18nText.CourtOfShackledSouls),
#         menu=I18nText.TacetDiscordNest,
#         register=[Dungeon.TacetDiscordNest],
#         icon=DungeonIcon.Icon1,
#         region=I18nText.GuidebookMengzhou,
#         waveplate=60,
#         enemy_id=I18nText.EnemyThousandPuppetPavilion,
#         rewards=[I18nText.SkywardGlazedHeart],
#     )


# class DungeonNightmarePurification:
#     # ------- NightmarePurification -------
#
#     CourtOfShackledSouls = DungeonMeta(
#         id=I18nText.CourtOfShackledSouls,
#         localized_name=I18nTr.l10n(I18nText.CourtOfShackledSouls),
#         menu=I18nText.NightmarePurification,
#         register=[Dungeon.NightmarePurification],
#         icon=DungeonIcon.Icon1,
#         region=I18nText.GuidebookMengzhou,
#         waveplate=60,
#         enemy_id=I18nText.EnemyThousandPuppetPavilion,
#         rewards=[I18nText.SkywardGlazedHeart],
#     )

if __name__ == '__main__':
    print(Dungeon.ForgeryChallenge)
    print(Dungeon.BossChallenge)
    print(Dungeon.TacetSuppression)
    print(Dungeon.WeeklyChallenge)
    print(Dungeon.TacetDiscordNest)
    print(Dungeon.NightmarePurification)