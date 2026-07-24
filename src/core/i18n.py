import logging
import re
from enum import Enum

from src.core.geometry import AnchorBBox, AnchorPoint, Align, BBox

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """
    BCP 47 / ISO
    """
    ZH = 'zh-CN'  # Simplified Chinese - 简体中文
    ZH_TW = 'zh-TW'  # Traditional Chinese (Taiwan、Hong Kong) - 繁体中文
    EN = 'en'  # English - 英语
    FR = 'fr'  # French - 法语
    DE = 'de'  # German - 德语
    ES = 'es'  # Spanish - 西班牙语
    JA = 'ja'  # Japanese - 日语
    KO = 'ko'  # Korean - 韩语
    RU = 'ru'  # Russian - 俄语
    PT = 'pt'  # Portuguese - 葡萄牙语
    IT = 'it'  # Italian - 意大利语
    AR = 'ar'  # Arabic - 阿拉伯语
    NL = 'nl'  # Dutch - 荷兰语
    SV = 'sv'  # Swedish - 瑞典语
    DA = 'da'  # Danish - 丹麦语
    NO = 'no'  # Norwegian - 挪威语
    FI = 'fi'  # Finnish - 芬兰语
    PL = 'pl'  # Polish - 波兰语
    TR = 'tr'  # Turkish - 土耳其语
    VI = 'vi'  # Vietnamese - 越南语
    HI = 'hi'  # Hindi - 印地语
    TH = 'th'  # Thai - 泰语
    ID = 'id'  # Indonesian - 印度尼西亚语
    HE = 'he'  # Hebrew - 希伯来语

    def __str__(self):
        return self.value


def flex_ws(text: str):
    """将字符串内的空白字符 替换为 任意空白正则字符串"""
    return re.sub(r"\s+", r"\\s*?", text)


class RegexStr(str):
    """
    增强正则字符串，用于解决打印日志时直接展示这条正则过于难看，展示原句更自然

    兼容 str 的所有行为，
    同时可附带额外元信息。
    """

    def __new__(
            cls,
            value: str,
            *,
            raw: str | None = None,
            desc: str | None = None,
            flags: int = re.I,
    ):
        obj = super().__new__(cls, value)
        # 原始文本，用于展示、打印日志等
        obj.raw = raw if raw is not None else value
        # 描述
        obj.desc = desc
        # 可选标记，默认忽略大小写
        obj.flags = flags

        return obj

    def __repr__(self):
        return (
            f"RegexStr("
            f"{super().__repr__()}, "
            f"raw={self.raw!r}, "
            f"desc={self.desc!r}, "
            f"flags={self.flags}"
            f")"
        )


class I18nText:
    """国际化key，唯一，kv必须一样，不然无法保证唯一性，有冲突就加功能前缀"""

    # ------- game window title -------
    WutheringWaves = "WutheringWaves"

    # ------- Resonator -------
    Rover = "Rover"
    Generic = "Generic"
    Null = "Null"
    Encore = "Encore"
    Verina = "Verina"
    Calcharo = "Calcharo"
    Lingyang = "Lingyang"
    Jianxin = "Jianxin"
    Yangyang = "Yangyang"
    Baizhi = "Baizhi"
    Chixia = "Chixia"
    Sanhua = "Sanhua"
    Aalto = "Aalto"
    Danjin = "Danjin"
    Mortefi = "Mortefi"
    Yuanwu = "Yuanwu"
    Taoqi = "Taoqi"
    Jiyan = "Jiyan"
    Yinlin = "Yinlin"
    Jinhsi = "Jinhsi"
    Changli = "Changli"
    Zhezhi = "Zhezhi"
    XiangliYao = "XiangliYao"
    Shorekeeper = "Shorekeeper"
    Youhu = "Youhu"
    Camellya = "Camellya"
    Lumi = "Lumi"
    Carlotta = "Carlotta"
    Roccia = "Roccia"
    Phoebe = "Phoebe"
    Brant = "Brant"
    Cantarella = "Cantarella"
    Zanni = "Zanni"
    Ciaccona = "Ciaccona"
    Cartethyia = "Cartethyia"
    Lupa = "Lupa"
    Phrolova = "Phrolova"
    Augusta = "Augusta"
    Iuno = "Iuno"
    Galbrena = "Galbrena"
    Qiuyuan = "Qiuyuan"
    Chisa = "Chisa"
    Buling = "Buling"
    Lynae = "Lynae"
    Mornye = "Mornye"
    Aemeath = "Aemeath"
    LuukHerssen = "LuukHerssen"
    Sigrika = "Sigrika"
    Hiyuki = "Hiyuki"
    Denia = "Denia"
    Lucy = "Lucy"
    Rebecca = "Rebecca"
    Lucilla = "Lucilla"
    YangyangXuanling = "YangyangXuanling"
    Suisui = "Suisui"
    Suoming = "Suoming"
    Jingran = "Jingran"
    Qingxiao = "Qingxiao"
    Hsin = "Hsin"

    # ------- Task -------
    DailyTask = "DailyTask"
    BossRushTask = "BossRushTask"
    EchoMergeTask = "EchoMergeTask"
    StoryTask = "StoryTask"
    PickupTask = "PickupTask"
    SoarToTheBeatMacroReplayTask = "SoarToTheBeatMacroReplayTask"
    SoarToTheBeatMacroRecordTask = "SoarToTheBeatMacroRecordTask"

    # ------- Enemy Tracing -------
    # 加前缀是因为boss名、角色名有相同的，达妮娅
    EnemyDreamless = "EnemyDreamless"
    EnemyFallacyOfNoReturn = "EnemyFallacyOfNoReturn"
    EnemyLampylumenMyriad = "EnemyLampylumenMyriad"
    EnemyBellBorneGeochelone = "EnemyBellBorneGeochelone"
    EnemyInfernoRider = "EnemyInfernoRider"
    EnemyImpermanenceHeron = "EnemyImpermanenceHeron"
    EnemyMechAbomination = "EnemyMechAbomination"
    EnemyMourningAix = "EnemyMourningAix"
    EnemyThunderingMephis = "EnemyThunderingMephis"
    EnemyTempestMephis = "EnemyTempestMephis"
    EnemyFeilianBeringal = "EnemyFeilianBeringal"
    EnemyCrownless = "EnemyCrownless"
    EnemyJue = "EnemyJue"
    EnemySentryConstruct = "EnemySentryConstruct"
    EnemyHecate = "EnemyHecate"
    EnemyLorelei = "EnemyLorelei"
    EnemyDragonOfDirge = "EnemyDragonOfDirge"
    EnemyNightmareFeilianBeringal = "EnemyNightmareFeilianBeringal"
    EnemyNightmareImpermanenceHeron = "EnemyNightmareImpermanenceHeron"
    EnemyNightmareTempestMephis = "EnemyNightmareTempestMephis"
    EnemyNightmareThunderingMephis = "EnemyNightmareThunderingMephis"
    EnemyNightmareCrownless = "EnemyNightmareCrownless"
    EnemyNightmareInfernoRider = "EnemyNightmareInfernoRider"
    EnemyNightmareMourningAix = "EnemyNightmareMourningAix"
    EnemyNightmareLampylumenMyriad = "EnemyNightmareLampylumenMyriad"
    EnemyFleurdelys = "EnemyFleurdelys"
    EnemyNightmareKelpie = "EnemyNightmareKelpie"
    EnemyLionessOfGlory = "EnemyLionessOfGlory"
    EnemyNightmareHecate = "EnemyNightmareHecate"
    EnemyFenrico = "EnemyFenrico"
    EnemyLadyOfTheSea = "EnemyLadyOfTheSea"
    EnemyTheFalseSovereign = "EnemyTheFalseSovereign"
    EnemyThrenodianLeviathan = "EnemyThrenodianLeviathan"
    EnemyHyvatia = "EnemyHyvatia"
    EnemyReactorHusk = "EnemyReactorHusk"
    EnemySigillum = "EnemySigillum"
    EnemyNamelessExplorer = "EnemyNamelessExplorer"
    EnemyDenia = "EnemyDenia"
    EnemyNightmareAdamSmasher = "EnemyNightmareAdamSmasher"
    EnemyMyriadSnareRustfireChassis = "EnemyMyriadSnareRustfireChassis"

    # ------- Sonata -------
    FreezingFrost = "FreezingFrost"
    MoltenRift = "MoltenRift"
    VoidThunder = "VoidThunder"
    SierraGale = "SierraGale"
    CelestialLight = "CelestialLight"
    HavocEclipse = "HavocEclipse"
    RejuvenatingGlow = "RejuvenatingGlow"
    MoonlitClouds = "MoonlitClouds"
    LingeringTunes = "LingeringTunes"
    FrostyResolve = "FrostyResolve"
    EternalRadiance = "EternalRadiance"
    MidnightVeil = "MidnightVeil"
    EmpyreanAnthem = "EmpyreanAnthem"
    TidebreakingCourage = "TidebreakingCourage"
    GustsOfWelkin = "GustsOfWelkin"
    WindwardPilgrimage = "WindwardPilgrimage"
    FlamingClawprint = "FlamingClawprint"
    DreamOfTheLost = "DreamOfTheLost"
    CrownOfValor = "CrownOfValor"
    LawOfHarmony = "LawOfHarmony"
    FlamewingsShadow = "FlamewingsShadow"
    ThreadOfSeveredFate = "ThreadOfSeveredFate"
    PactOfNeonlightLeap = "PactOfNeonlightLeap"
    HaloOfStarryRadiance = "HaloOfStarryRadiance"
    RiteOfGildedRevelation = "RiteOfGildedRevelation"
    TrailblazingStar = "TrailblazingStar"
    ChromaticFoam = "ChromaticFoam"
    SoundOfTrueName = "SoundOfTrueName"
    WishesOfQuietSnowfall = "WishesOfQuietSnowfall"
    ReelOfSplicedMemories = "ReelOfSplicedMemories"
    ShadowOfShatteredDreams = "ShadowOfShatteredDreams"

    # ------- Login -------
    Login = "Login"

    # ------- Map -------
    FastTravel = "FastTravel"
    EnableNavigation = "EnableNavigation"
    SwitchMap = "SwitchMap"
    RoyaFrostlands = "RoyaFrostlands"
    Rinascita = "Rinascita"
    TheBlackShores = "TheBlackShores"
    Huanglong = "Huanglong"
    Jinzhou = "Jinzhou"
    JinzhouCity = "JinzhouCity"
    Mengzhou = "Mengzhou"

    # ------- Notice -------
    Confirm = "Confirm"
    Restart = "Restart"
    Exit = "Exit"
    CollectSupplies = "CollectSupplies"
    ItemsObtained = "ItemsObtained"
    TapTheBlankAreaToClose = "TapTheBlankAreaToClose"
    SelectARevivalItem = "SelectARevivalItem"
    DoNotShowAgain = "DoNotShowAgain"
    LuniteSubscriptionReward = "LuniteSubscriptionReward"

    # ------- Dialogue -------
    Absorb = "Absorb"
    ClaimRewards = "ClaimRewards"
    ChallengeAgain = "ChallengeAgain"

    # ------- Terminal -------
    # sidebar
    Terminal = "Terminal"
    Birthday = "Birthday"
    SOL3Phase = "SOL3Phase"
    UnionLevel = "UnionLevel"
    UnionEXP = "UnionEXP"
    # item
    Events = "Events"
    TerminalPioneerPodcast = "TerminalPioneerPodcast"
    Team = "Team"
    DataBank = "DataBank"
    Guidebook = "Guidebook"
    Map = "Map"
    Mail = "Mail"

    # ------- Data Bank -------
    TargetedMerge = "TargetedMerge"
    StandardMerge = "StandardMerge"
    PleaseSelectAtLeast5Echoes = "PleaseSelectAtLeast5Echoes"
    DataMergeCount = "DataMergeCount"

    # ------- Guidebook -------
    Activity = "Activity"
    MaterialsSpots = "MaterialsSpots"
    RecurringChallenges = "RecurringChallenges"
    PathOfGrowth = "PathOfGrowth"
    EnemyTracing = "EnemyTracing"
    Milestones = "Milestones"

    ## ------- Guidebook Common -------
    CannotPerformThisActionDuringBattle = "CannotPerformThisActionDuringBattle"
    DoubleDropChancesToday = "DoubleDropChancesToday"
    GuidebookMengzhou = "GuidebookMengzhou"
    GuidebookLahaiRoi = "GuidebookLahaiRoi"
    GuidebookRinascita = "GuidebookRinascita"
    GuidebookJinzhou = "GuidebookJinzhou"

    ## ------- Guidebook Activity -------
    ActivityDaily = "ActivityDaily"
    ActivityWeekly = "ActivityWeekly"
    ActivityPts = "ActivityPts"
    WeeklyActivityPts = "WeeklyActivityPts"
    ActivityClaim = "ActivityClaim"

    ## ------- Guidebook MaterialsSpots -------
    ForgeryChallenge = "ForgeryChallenge"
    SimulationChallenge = "SimulationChallenge"
    BossChallenge = "BossChallenge"
    TacetSuppression = "TacetSuppression"
    WeeklyChallenge = "WeeklyChallenge"
    NightmarePurification = "NightmarePurification"
    TacetDiscordNest = "TacetDiscordNest"

    ### ------- Guidebook MaterialsSpots ForgeryChallenge -------
    WingfallChasm = "WingfallChasm"
    SilentChasm = "SilentChasm"
    SplitChasm = "SplitChasm"
    ErodedChasm = "ErodedChasm"
    AshenChasm = "AshenChasm"
    FallenSanctum = "FallenSanctum"
    LessonInSunset = "LessonInSunset"
    StrickenSanctum = "StrickenSanctum"
    LessonInVoid = "LessonInVoid"
    LessonInEmbers = "LessonInEmbers"
    GardenOfSalvation = "GardenOfSalvation"
    AbyssOfInitiation = "AbyssOfInitiation"
    GardenOfAdoration = "GardenOfAdoration"
    AbyssOfSacrifice = "AbyssOfSacrifice"
    AbyssOfConfession = "AbyssOfConfession"
    FlamingRemnants = "FlamingRemnants"
    MistyForest = "MistyForest"
    ErodedRuins = "ErodedRuins"
    MoonlitGroves = "MoonlitGroves"
    MarigoldWoods = "MarigoldWoods"
    # weapon
    Sword = "Sword"
    Rectifier = "Rectifier"
    Broadblade = "Broadblade"
    Gauntlets = "Gauntlets"
    Pistols = "Pistols"
    EnterTheForgeryChallenge = "EnterTheForgeryChallenge"
    Level = "Level"
    Match = "Match"
    SoloChallenge = "SoloChallenge"
    DefeatTheEnemiesWithinTimeLimit = "DefeatTheEnemiesWithinTimeLimit"
    ForgeryChallengeComplete = "ForgeryChallengeComplete"
    ForgeryClaim = "ForgeryClaim"
    ForgeryClaimX2 = "ForgeryClaimX2"
    ForgeryRestart = "ForgeryRestart"
    ForgeryExit = "ForgeryExit"

    ### ------- Guidebook MaterialsSpots TacetSuppression -------
    WesternFangPeaksTacetField = "WesternFangPeaksTacetField"
    EasternXuanPeaksTacetField = "EasternXuanPeaksTacetField"
    TacetFieldSolisiaLanding = "TacetFieldSolisiaLanding"
    TacetFieldFrostlandsTransitPort = "TacetFieldFrostlandsTransitPort"
    TacetFieldMountGjallar = "TacetFieldMountGjallar"
    TacetFieldMawburrowDesert = "TacetFieldMawburrowDesert"
    TacetFieldStagnantRun = "TacetFieldStagnantRun"
    TacetField = "TacetField"
    EchoSet = "EchoSet"
    DefeatTheTdsInTheTacetField = "DefeatTheTdsInTheTacetField"
    TacetFieldChallengeComplete = "TacetFieldChallengeComplete"
    TacetFieldClaim = "TacetFieldClaim"
    TacetFieldClaimX2 = "TacetFieldClaimX2"
    TacetFieldNoticeChallengeComplete = "TacetFieldNoticeChallengeComplete"
    TacetFieldConfirm = "TacetFieldConfirm"
    TacetFieldRestart = "TacetFieldRestart"
    TacetFieldExit = "TacetFieldExit"

    ### ------- Guidebook MaterialsSpots WeeklyChallenge -------
    WeeklyChallengeWeeklyChallenge = "WeeklyChallengeWeeklyChallenge"
    RemainingWeeklyAttempts = "RemainingWeeklyAttempts"
    LimitedTimeEarlyAccess = "LimitedTimeEarlyAccess"
    ArrivingAtTheDestination = "ArrivingAtTheDestination"
    # 周本关卡名
    CourtOfShackledSouls = "CourtOfShackledSouls"
    SeedOfIllusoryOrigin = "SeedOfIllusoryOrigin"
    GateOfTheLostStar = "GateOfTheLostStar"
    CinderniteApocalypse = "CinderniteApocalypse"
    TheWheelOfBrokenFate = "TheWheelOfBrokenFate"
    BeyondTheCrimsonCurtain = "BeyondTheCrimsonCurtain"
    TheFatedConfrontation = "TheFatedConfrontation"
    StatueOfTheCrownless = "StatueOfTheCrownless"
    ChaoticJuncture = "ChaoticJuncture"
    BellOfArchaicChants = "BellOfArchaicChants"
    # 前端用关卡名不好认，使用boss名
    WeeklyBossThousandPuppetPavilion = "WeeklyBossThousandPuppetPavilion"
    WeeklyBossDenia = "WeeklyBossDenia"
    WeeklyBossSigillum = "WeeklyBossSigillum"
    WeeklyBossThrenodianLeviathan = "WeeklyBossThrenodianLeviathan"
    WeeklyBossFleurdelys = "WeeklyBossFleurdelys"
    WeeklyBossHecate = "WeeklyBossHecate"
    WeeklyBossJue = "WeeklyBossJue"
    WeeklyBossCrownless = "WeeklyBossCrownless"
    WeeklyBossScarAberrantNightmare = "WeeklyBossScarAberrantNightmare"
    WeeklyBossBellBorneGeochelone = "WeeklyBossBellBorneGeochelone"
    # instance
    EnterTheSonoroSphere = "EnterTheSonoroSphere"
    WeeklySuggestedLv = "WeeklySuggestedLv"
    WeeklyRemainingAttempts = "WeeklyRemainingAttempts"
    WeeklySoloChallenge = "WeeklySoloChallenge"
    YourCurrentSol3Phase = "YourCurrentSol3Phase"
    WeeklyDefeatTheEnemy = "WeeklyDefeatTheEnemy"
    WeeklyClaimRewards = "WeeklyClaimRewards"
    WeeklyConfirm = "WeeklyConfirm"
    WeeklyCancel = "WeeklyCancel"
    WeeklyRestart = "WeeklyRestart"
    WeeklyExit = "WeeklyExit"
    YouHaveReachedTheChallengeLimit = "YouHaveReachedTheChallengeLimit"

    ### ------- Guidebook MaterialsSpots TacetDiscordNest -------
    TacetDiscordNestTacetDiscordNest = "TacetDiscordNestTacetDiscordNest"
    # LahaiRoi = "LahaiRoi"
    SouthernYuanHillsTacetDiscordNest = "SouthernYuanHillsTacetDiscordNest"
    StarblindCrashsiteTacetDiscordNest = "StarblindCrashsiteTacetDiscordNest"
    RebirthUplandsTacetDiscordNest = "RebirthUplandsTacetDiscordNest"
    StagnantRunTacetDiscordNest = "StagnantRunTacetDiscordNest"
    TacetDiscordDefeated = "TacetDiscordDefeated"
    Go = "Go"
    Challenge = "Challenge"

    # ------- Team -------
    QuickSetup = "QuickSetup"
    Deployed = "Deployed"
    Deploy = "Deploy"
    ResonatorDowned = "ResonatorDowned"
    # instance
    StartChallenge = "StartChallenge"

    # ------- Mail -------
    Mailbox = "Mailbox"
    MailClaimAll = "MailClaimAll"

    # ------- Pioneer Podcast -------
    PioneerPodcast = "PioneerPodcast"
    PioneerPodcastUnavailable = "PioneerPodcastUnavailable"
    PodcastTasks = "PodcastTasks"
    PioneerPodcastClaimAll = "PioneerPodcastClaimAll"
    PioneerPodcastConfirm = "PioneerPodcastConfirm"

    # ------- (Home) TacetDiscordNest -------
    ClearTheTacetDiscordNest = "ClearTheTacetDiscordNest"
    TacetDiscordNestCleared = "TacetDiscordNestCleared"
    ClearTheTacetDiscordNestMengzhou = "ClearTheTacetDiscordNestMengzhou"
    TacetDiscordNestClearedMengzhou = "TacetDiscordNestClearedMengzhou"

    # ------- View -------
    ViewClaimRewards = "ViewClaimRewards"
    ViewClaimRewardsConfirm = "ViewClaimRewardsConfirm"
    ViewClaimRewardsCancel = "ViewClaimRewardsCancel"

    CrownlessResonanceCord = "CrownlessResonanceCord"

    ViewFight = "ViewFight"

    ViewChallengeComplete = "ViewChallengeComplete"
    ViewChallengeFailed = "ViewChallengeFailed"

    ViewBreakFree = "ViewBreakFree"

    ViewLeaveInstanceNote = "ViewLeaveInstanceNote"
    ViewLeaveInstanceConfirm = "ViewLeaveInstanceConfirm"
    ViewLeaveInstanceRestart = "ViewLeaveInstanceRestart"

    ViewLeaveInstance2Notice = "ViewLeaveInstance2Notice"
    ViewLeaveInstance2Confirm = "ViewLeaveInstance2Confirm"
    ViewLeaveInstance2Cancel = "ViewLeaveInstance2Cancel"
    ViewLeaveInstance2Restart = "ViewLeaveInstance2Restart"
    ViewLeaveInstance2Leave = "ViewLeaveInstance2Leave"

    ViewForgeryChallengeExit = "ViewForgeryChallengeExit"
    ViewForgeryChallengeRestart = "ViewForgeryChallengeRestart"

    ViewTacetSuppressionChallengeComplete = "ViewTacetSuppressionChallengeComplete"
    ViewTacetSuppressionConfirm = "ViewTacetSuppressionConfirm"
    ViewTacetSuppressionExit = "ViewTacetSuppressionExit"
    ViewTacetSuppressionCancel = "ViewTacetSuppressionCancel"
    ViewTacetSuppressionRestart = "ViewTacetSuppressionRestart"
    ViewTacetSuppressionClaimRewards = "ViewTacetSuppressionClaimRewards"
    ViewTacetSuppressionClaim = "ViewTacetSuppressionClaim"
    ViewTacetSuppressionClaimX2 = "ViewTacetSuppressionClaimX2"


I18N_TEXT = {
    # ------- game window title -------
    I18nText.WutheringWaves: {
        Language.ZH: "鸣潮  ",
        Language.EN: "Wuthering Waves  ",
    },

    # ------- Resonator -------
    I18nText.Rover: {
        Language.ZH: RegexStr(r"^漂泊者$", raw="漂泊者"),
        Language.EN: RegexStr(flex_ws(r"^Rover$"), raw="Rover"),
    },
    # I18nText.Generic: {
    #     Language.ZH: RegexStr(r"^Generic$", raw="Generic"),
    #     Language.EN: RegexStr(flex_ws(r"^Generic$"), raw="Generic"),
    # },
    # I18nText.Null: {
    #     Language.ZH: RegexStr(r"^Null$", raw="Null"),
    #     Language.EN: RegexStr(flex_ws(r"^Null$"), raw="Null"),
    # },
    I18nText.Encore: {
        Language.ZH: RegexStr(r"^安可$", raw="安可"),
        Language.EN: RegexStr(flex_ws(r"^Encore$"), raw="Encore"),
    },
    I18nText.Verina: {
        Language.ZH: RegexStr(r"^维里奈$", raw="维里奈"),
        Language.EN: RegexStr(flex_ws(r"^Verina$"), raw="Verina"),
    },
    I18nText.Calcharo: {
        Language.ZH: RegexStr(r"^卡卡罗$", raw="卡卡罗"),
        Language.EN: RegexStr(flex_ws(r"^Calcharo$"), raw="Calcharo"),
    },
    I18nText.Lingyang: {
        Language.ZH: RegexStr(r"^凌阳$", raw="凌阳"),
        Language.EN: RegexStr(flex_ws(r"^Lingyang$"), raw="Lingyang"),
    },
    I18nText.Jianxin: {
        Language.ZH: RegexStr(r"^鉴心$", raw="鉴心"),
        Language.EN: RegexStr(flex_ws(r"^Jianxin$"), raw="Jianxin"),
    },
    I18nText.Yangyang: {
        Language.ZH: RegexStr(r"^秧秧$", raw="秧秧"),
        Language.EN: RegexStr(flex_ws(r"^Yangyang$"), raw="Yangyang"),
    },
    I18nText.Baizhi: {
        Language.ZH: RegexStr(r"^白芷$", raw="白芷"),
        Language.EN: RegexStr(flex_ws(r"^Baizhi$"), raw="Baizhi"),
    },
    I18nText.Chixia: {
        Language.ZH: RegexStr(r"^炽霞$", raw="炽霞"),
        Language.EN: RegexStr(flex_ws(r"^Chixia$"), raw="Chixia"),
    },
    I18nText.Sanhua: {
        Language.ZH: RegexStr(r"^散华$", raw="散华"),
        Language.EN: RegexStr(flex_ws(r"^Sanhua$"), raw="Sanhua"),
    },
    I18nText.Aalto: {
        Language.ZH: RegexStr(r"^秋水$", raw="秋水"),
        Language.EN: RegexStr(flex_ws(r"^Aalto$"), raw="Aalto"),
    },
    I18nText.Danjin: {
        Language.ZH: RegexStr(r"^丹瑾$", raw="丹瑾"),
        Language.EN: RegexStr(flex_ws(r"^Danjin$"), raw="Danjin"),
    },
    I18nText.Mortefi: {
        Language.ZH: RegexStr(r"^莫特斐$", raw="莫特斐"),
        Language.EN: RegexStr(flex_ws(r"^Mortefi$"), raw="Mortefi"),
    },
    I18nText.Yuanwu: {
        Language.ZH: RegexStr(r"^渊武$", raw="渊武"),
        Language.EN: RegexStr(flex_ws(r"^Yuanwu$"), raw="Yuanwu"),
    },
    I18nText.Taoqi: {
        Language.ZH: RegexStr(r"^桃祈$", raw="桃祈"),
        Language.EN: RegexStr(flex_ws(r"^Taoqi$"), raw="Taoqi"),
    },
    I18nText.Jiyan: {
        Language.ZH: RegexStr(r"^忌炎$", raw="忌炎"),
        Language.EN: RegexStr(flex_ws(r"^Jiyan$"), raw="Jiyan"),
    },
    I18nText.Yinlin: {
        Language.ZH: RegexStr(r"^吟霖$", raw="吟霖"),
        Language.EN: RegexStr(flex_ws(r"^Yinlin$"), raw="Yinlin"),
    },
    I18nText.Jinhsi: {
        Language.ZH: RegexStr(r"^今汐$", raw="今汐"),
        Language.EN: RegexStr(flex_ws(r"^Jinhsi$"), raw="Jinhsi"),
    },
    I18nText.Changli: {
        Language.ZH: RegexStr(r"^长离$", raw="长离"),
        Language.EN: RegexStr(flex_ws(r"^Changli$"), raw="Changli"),
    },
    I18nText.Zhezhi: {
        Language.ZH: RegexStr(r"^折枝$", raw="折枝"),
        Language.EN: RegexStr(flex_ws(r"^Zhezhi$"), raw="Zhezhi"),
    },
    I18nText.XiangliYao: {
        Language.ZH: RegexStr(r"^相里要$", raw="相里要"),
        Language.EN: RegexStr(flex_ws(r"^Xiangli Yao$"), raw="Xiangli Yao"),
    },
    I18nText.Shorekeeper: {
        Language.ZH: RegexStr(r"^守岸人$", raw="守岸人"),
        Language.EN: RegexStr(flex_ws(r"^Shorekeeper$"), raw="Shorekeeper"),
    },
    I18nText.Youhu: {
        Language.ZH: RegexStr(r"^釉瑚$", raw="釉瑚"),
        Language.EN: RegexStr(flex_ws(r"^Youhu$"), raw="Youhu"),
    },
    I18nText.Camellya: {
        Language.ZH: RegexStr(r"^椿$", raw="椿"),
        Language.EN: RegexStr(flex_ws(r"^Camellya$"), raw="Camellya"),
    },
    I18nText.Lumi: {
        Language.ZH: RegexStr(r"^灯灯$", raw="灯灯"),
        Language.EN: RegexStr(flex_ws(r"^Lumi$"), raw="Lumi"),
    },
    I18nText.Carlotta: {
        Language.ZH: RegexStr(r"^珂莱塔$", raw="珂莱塔"),
        Language.EN: RegexStr(flex_ws(r"^Carlotta$"), raw="Carlotta"),
    },
    I18nText.Roccia: {
        Language.ZH: RegexStr(r"^洛可可$", raw="洛可可"),
        Language.EN: RegexStr(flex_ws(r"^Roccia$"), raw="Roccia"),
    },
    I18nText.Phoebe: {
        Language.ZH: RegexStr(r"^菲比$", raw="菲比"),
        Language.EN: RegexStr(flex_ws(r"^Phoebe$"), raw="Phoebe"),
    },
    I18nText.Brant: {
        Language.ZH: RegexStr(r"^布兰特$", raw="布兰特"),
        Language.EN: RegexStr(flex_ws(r"^Brant$"), raw="Brant"),
    },
    I18nText.Cantarella: {
        Language.ZH: RegexStr(r"^坎特蕾拉$", raw="坎特蕾拉"),
        Language.EN: RegexStr(flex_ws(r"^Cantarella$"), raw="Cantarella"),
    },
    I18nText.Zanni: {
        Language.ZH: RegexStr(r"^赞妮$", raw="赞妮"),
        Language.EN: RegexStr(flex_ws(r"^Zanni$"), raw="Zanni"),
    },
    I18nText.Ciaccona: {
        Language.ZH: RegexStr(r"^夏空$", raw="夏空"),
        Language.EN: RegexStr(flex_ws(r"^Ciaccona$"), raw="Ciaccona"),
    },
    I18nText.Cartethyia: {
        Language.ZH: RegexStr(r"^卡提希娅$", raw="卡提希娅"),
        Language.EN: RegexStr(flex_ws(r"^Cartethyia$"), raw="Cartethyia"),
    },
    I18nText.Lupa: {
        Language.ZH: RegexStr(r"^露帕$", raw="露帕"),
        Language.EN: RegexStr(flex_ws(r"^Lupa$"), raw="Lupa"),
    },
    I18nText.Phrolova: {
        Language.ZH: RegexStr(r"^弗洛洛$", raw="弗洛洛"),
        Language.EN: RegexStr(flex_ws(r"^Phrolova$"), raw="Phrolova"),
    },
    I18nText.Augusta: {
        Language.ZH: RegexStr(r"^奥古斯塔$", raw="奥古斯塔"),
        Language.EN: RegexStr(flex_ws(r"^Augusta$"), raw="Augusta"),
    },
    I18nText.Iuno: {
        Language.ZH: RegexStr(r"^尤诺$", raw="尤诺"),
        Language.EN: RegexStr(flex_ws(r"^[Il]uno$"), raw="Iuno"),
    },
    I18nText.Galbrena: {
        Language.ZH: RegexStr(r"^嘉贝莉娜$", raw="嘉贝莉娜"),
        Language.EN: RegexStr(flex_ws(r"^Galbrena$"), raw="Galbrena"),
    },
    I18nText.Qiuyuan: {
        Language.ZH: RegexStr(r"^仇远$", raw="仇远"),
        Language.EN: RegexStr(flex_ws(r"^Qiuyuan$"), raw="Qiuyuan"),
    },
    I18nText.Chisa: {
        Language.ZH: RegexStr(r"^千.?$", raw="千咲"),
        Language.EN: RegexStr(flex_ws(r"^Chisa$"), raw="Chisa"),
    },
    I18nText.Buling: {
        Language.ZH: RegexStr(r"^卜灵$", raw="卜灵"),
        Language.EN: RegexStr(flex_ws(r"^Buling$"), raw="Buling"),
    },
    I18nText.Lynae: {
        Language.ZH: RegexStr(r"^琳奈$", raw="琳奈"),
        Language.EN: RegexStr(flex_ws(r"^Lynae$"), raw="Lynae"),
    },
    I18nText.Mornye: {
        Language.ZH: RegexStr(r"^莫宁$", raw="莫宁"),
        Language.EN: RegexStr(flex_ws(r"^Mornye$"), raw="Mornye"),
    },
    I18nText.Aemeath: {
        Language.ZH: RegexStr(r"^爱弥斯$", raw="爱弥斯"),
        Language.EN: RegexStr(flex_ws(r"^Aemeath$"), raw="Aemeath"),
    },
    I18nText.LuukHerssen: {
        Language.ZH: RegexStr(r"陆.*?赫斯$", raw="陆·赫斯"),
        Language.EN: RegexStr(flex_ws(r"^Luuk.*?Herssen$"), raw="Luuk Herssen"),
    },
    I18nText.Sigrika: {
        Language.ZH: RegexStr(r"^西格莉卡$", raw="西格莉卡"),
        Language.EN: RegexStr(flex_ws(r"^Sigrika$"), raw="Sigrika"),
    },
    I18nText.Hiyuki: {
        Language.ZH: RegexStr(r"^绯雪$", raw="绯雪"),
        Language.EN: RegexStr(flex_ws(r"^Hiyuki$"), raw="Hiyuki"),
    },
    I18nText.Denia: {
        Language.ZH: RegexStr(r"^达妮娅$", raw="达妮娅"),
        Language.EN: RegexStr(flex_ws(r"^Denia$"), raw="Denia"),
    },
    I18nText.Lucy: {
        Language.ZH: RegexStr(r"^露西$", raw="露西"),
        Language.EN: RegexStr(flex_ws(r"^Lucy$"), raw="Lucy"),
    },
    I18nText.Rebecca: {
        Language.ZH: RegexStr(r"^丽贝卡$", raw="丽贝卡"),
        Language.EN: RegexStr(flex_ws(r"^Rebecca$"), raw="Rebecca"),
    },
    I18nText.Lucilla: {
        Language.ZH: RegexStr(r"^洛瑟.?$", raw="洛瑟菈"),
        Language.EN: RegexStr(flex_ws(r"^Lucilla$"), raw="Lucilla"),
    },
    I18nText.YangyangXuanling: {
        Language.ZH: RegexStr(r"^秧秧.*?玄翎$", raw="秧秧·玄翎"),
        Language.EN: RegexStr(flex_ws(r"^YangyangXuanling$"), raw="YangyangXuanling"),
    },
    I18nText.Suisui: {
        Language.ZH: RegexStr(r"^穗穗$", raw="穗穗"),
        Language.EN: RegexStr(flex_ws(r"^Suisui$"), raw="Suisui"),
    },
    I18nText.Suoming: {
        Language.ZH: RegexStr(r"^锁[暝冥]$", raw="锁暝"),
        Language.EN: RegexStr(flex_ws(r"^Suoming$"), raw="Suoming"),
    },
    I18nText.Jingran: {
        Language.ZH: RegexStr(r"^景燃$", raw="景燃"),
        Language.EN: RegexStr(flex_ws(r"^Jingran$"), raw="Jingran"),
    },
    I18nText.Qingxiao: {
        Language.ZH: RegexStr(r"^清宵$", raw="清宵"),
        Language.EN: RegexStr(flex_ws(r"^Qingxiao$"), raw="Qingxiao"),
    },
    I18nText.Hsin: {
        Language.ZH: RegexStr(r"^心$", raw="心"),
        Language.EN: RegexStr(flex_ws(r"^Hsin$"), raw="Hsin"),
    },

    # ------- Task -------
    I18nText.DailyTask: {
        Language.ZH: RegexStr(r"DailyTask", raw="DailyTask"),
        Language.EN: RegexStr(r"DailyTask", raw="DailyTask"),
    },
    I18nText.BossRushTask: {
        Language.ZH: RegexStr(r"BossRushTask", raw="BossRushTask"),
        Language.EN: RegexStr(r"BossRushTask", raw="BossRushTask"),
    },
    I18nText.EchoMergeTask: {
        Language.ZH: RegexStr(r"EchoMergeTask", raw="EchoMergeTask"),
        Language.EN: RegexStr(r"EchoMergeTask", raw="EchoMergeTask"),
    },
    I18nText.StoryTask: {
        Language.ZH: RegexStr(r"StoryTask", raw="StoryTask"),
        Language.EN: RegexStr(r"StoryTask", raw="StoryTask"),
    },
    I18nText.PickupTask: {
        Language.ZH: RegexStr(r"PickupTask", raw="PickupTask"),
        Language.EN: RegexStr(r"PickupTask", raw="PickupTask"),
    },
    I18nText.SoarToTheBeatMacroReplayTask: {
        Language.ZH: RegexStr(r"SoarToTheBeatMacroReplayTask", raw="SoarToTheBeatMacroReplayTask"),
        Language.EN: RegexStr(r"SoarToTheBeatMacroReplayTask", raw="SoarToTheBeatMacroReplayTask"),
    },
    I18nText.SoarToTheBeatMacroRecordTask: {
        Language.ZH: RegexStr(r"SoarToTheBeatMacroRecordTask", raw="SoarToTheBeatMacroRecordTask"),
        Language.EN: RegexStr(r"SoarToTheBeatMacroRecordTask", raw="SoarToTheBeatMacroRecordTask"),
    },

    # ------- Enemy Tracing -------
    I18nText.EnemyDreamless: {
        Language.ZH: RegexStr(r"^无妄者$", raw="无妄者"),
        Language.EN: RegexStr(flex_ws(r"^Dreamless$"), raw="Dreamless"),
    },
    I18nText.EnemyFallacyOfNoReturn: {
        Language.ZH: RegexStr(r"^无归的谬误$", raw="无归的谬误"),
        Language.EN: RegexStr(flex_ws(r"^Fallacy of No Return$"), raw="Fallacy of No Return"),
    },
    I18nText.EnemyLampylumenMyriad: {
        Language.ZH: RegexStr(r"^辉萤军势$", raw="辉萤军势"),
        Language.EN: RegexStr(flex_ws(r"^Lampylumen Myriad$"), raw="Lampylumen Myriad"),
    },
    I18nText.EnemyBellBorneGeochelone: {
        Language.ZH: RegexStr(r"^鸣钟之龟$", raw="鸣钟之龟"),
        Language.EN: RegexStr(flex_ws(r"^Bell.Borne Geochelone$"), raw="Bell-Borne Geochelone"),
    },
    I18nText.EnemyInfernoRider: {
        Language.ZH: RegexStr(r"^燎照之骑$", raw="燎照之骑"),
        Language.EN: RegexStr(flex_ws(r"^Inferno Rider$"), raw="Inferno Rider"),
    },
    I18nText.EnemyImpermanenceHeron: {
        Language.ZH: RegexStr(r"^无常凶鹭$", raw="无常凶鹭"),
        Language.EN: RegexStr(flex_ws(r"^Impermanence Heron$"), raw="Impermanence Heron"),
    },
    I18nText.EnemyMechAbomination: {
        Language.ZH: RegexStr(r"^聚械机偶$", raw="聚械机偶"),
        Language.EN: RegexStr(flex_ws(r"^Mech Abomination$"), raw="Mech Abomination"),
    },
    I18nText.EnemyMourningAix: {
        Language.ZH: RegexStr(r"^哀声鸷$", raw="哀声鸷"),
        Language.EN: RegexStr(flex_ws(r"^Mourning Aix$"), raw="Mourning Aix"),
    },
    I18nText.EnemyThunderingMephis: {
        Language.ZH: RegexStr(r"^朔雷之鳞$", raw="朔雷之鳞"),
        Language.EN: RegexStr(flex_ws(r"^Thundering Mephis$"), raw="Thundering Mephis"),
    },
    I18nText.EnemyTempestMephis: {
        Language.ZH: RegexStr(r"^云闪之鳞$", raw="云闪之鳞"),
        Language.EN: RegexStr(flex_ws(r"^Tempest Mephis$"), raw="Tempest Mephis"),
    },
    I18nText.EnemyFeilianBeringal: {
        Language.ZH: RegexStr(r"^飞廉之猩$", raw="飞廉之猩"),
        Language.EN: RegexStr(flex_ws(r"^Feilian Beringal$"), raw="Feilian Beringal"),
    },
    I18nText.EnemyCrownless: {
        Language.ZH: RegexStr(r"^无冠者$", raw="无冠者"),
        Language.EN: RegexStr(flex_ws(r"^Crownless$"), raw="Crownless"),
    },
    I18nText.EnemyJue: {
        Language.ZH: RegexStr(r"^角$", raw="角"),
        Language.EN: RegexStr(flex_ws(r"^Ju.$"), raw="Jué"),
    },
    I18nText.EnemySentryConstruct: {
        Language.ZH: RegexStr(r"^异构武装$", raw="异构武装"),
        Language.EN: RegexStr(flex_ws(r"^Sentry Construct$"), raw="Sentry Construct"),
    },
    I18nText.EnemyHecate: {
        Language.ZH: RegexStr(r"^赫卡.$", raw="赫卡忒"),
        Language.EN: RegexStr(flex_ws(r"^Hecate$"), raw="Hecate"),
    },
    I18nText.EnemyLorelei: {
        Language.ZH: RegexStr(r"^罗蕾莱$", raw="罗蕾莱"),
        Language.EN: RegexStr(flex_ws(r"^Lorelei$"), raw="Lorelei"),
    },
    I18nText.EnemyDragonOfDirge: {
        Language.ZH: RegexStr(r"^叹息古龙$", raw="叹息古龙"),
        Language.EN: RegexStr(flex_ws(r"^Dragon of Dirge$"), raw="Dragon of Dirge"),
    },
    I18nText.EnemyNightmareFeilianBeringal: {
        Language.ZH: RegexStr(r"^梦.*?飞廉之猩$", raw="梦魇飞廉之猩"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Feilian Beringal$"), raw="Nightmare: Feilian Beringal"),
    },
    I18nText.EnemyNightmareImpermanenceHeron: {
        Language.ZH: RegexStr(r"^梦.*?无常凶鹭$", raw="梦魇无常凶鹭"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Impermanence Heron$"), raw="Nightmare: Impermanence Heron"),
    },
    I18nText.EnemyNightmareTempestMephis: {
        Language.ZH: RegexStr(r"^梦.*?云闪之鳞$", raw="梦魇云闪之鳞"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?TempestMephis$"), raw="Nightmare: Tempest Mephis"),
    },
    I18nText.EnemyNightmareThunderingMephis: {
        Language.ZH: RegexStr(r"^梦.*?朔雷之鳞$", raw="梦魇朔雷之鳞"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Thundering Mephis$"), raw="Nightmare: Thundering Mephis"),
    },
    I18nText.EnemyNightmareCrownless: {
        Language.ZH: RegexStr(r"^梦.*?无冠者$", raw="梦魇无冠者"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Crownless$"), raw="Nightmare: Crownless"),
    },
    I18nText.EnemyNightmareInfernoRider: {
        Language.ZH: RegexStr(r"^梦.*?燎照之骑$", raw="梦魇燎照之骑"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Inferno Rider$"), raw="Nightmare: Inferno Rider"),
    },
    I18nText.EnemyNightmareMourningAix: {
        Language.ZH: RegexStr(r"^梦.*?[哀袁]声.?$", raw="梦魇哀声鸷"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Mourning Aix$"), raw="Nightmare: Mourning Aix"),
    },
    I18nText.EnemyNightmareLampylumenMyriad: {
        Language.ZH: RegexStr(r"^梦.*?辉.军势$", raw="梦魇辉萤军势"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Lampylumen Myriad$"), raw="Nightmare: Lampylumen Myriad"),
    },
    I18nText.EnemyFleurdelys: {
        Language.ZH: RegexStr(r"^芙露德莉斯$", raw="芙露德莉斯"),
        Language.EN: RegexStr(flex_ws(r"^Fleurdelys$"), raw="Fleurdelys"),
    },
    I18nText.EnemyNightmareKelpie: {
        Language.ZH: RegexStr(r"^梦.*?凯尔匹$", raw="梦魇凯尔匹"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Kelpie$"), raw="Nightmare: Kelpie"),
    },
    I18nText.EnemyLionessOfGlory: {
        Language.ZH: RegexStr(r"^荣耀狮像$", raw="荣耀狮像"),
        Language.EN: RegexStr(flex_ws(r"^Lioness of Glory$"), raw="Lioness of Glory"),
    },
    I18nText.EnemyNightmareHecate: {
        Language.ZH: RegexStr(r"^梦.*?赫卡.?$", raw="梦魇赫卡忒"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.*?Hecate$"), raw="Nightmare: Hecate"),
    },
    I18nText.EnemyFenrico: {
        Language.ZH: RegexStr(r"^芬莱克$", raw="芬莱克"),
        Language.EN: RegexStr(flex_ws(r"^Fenrico$"), raw="Fenrico"),
    },
    I18nText.EnemyLadyOfTheSea: {
        Language.ZH: RegexStr(r"^海之女$", raw="海之女"),
        Language.EN: RegexStr(flex_ws(r"^Lady of the Sea$"), raw="Lady of the Sea"),
    },
    I18nText.EnemyTheFalseSovereign: {
        Language.ZH: RegexStr(r"^伪作的神王$", raw="伪作的神王"),
        Language.EN: RegexStr(flex_ws(r"^The False Sovereign$"), raw="The False Sovereign"),
    },
    I18nText.EnemyThrenodianLeviathan: {
        Language.ZH: RegexStr(r"^鸣式.*?利维亚坦$", raw="鸣式利维亚坦"),
        Language.EN: RegexStr(flex_ws(r"^Threnodian.*?Leviathan$"), raw="Threnodian: Leviathan"),
    },
    I18nText.EnemyHyvatia: {
        Language.ZH: RegexStr(r"^海维夏$", raw="海维夏"),
        Language.EN: RegexStr(flex_ws(r"^Hyvatia$"), raw="Hyvatia"),
    },
    I18nText.EnemyReactorHusk: {
        Language.ZH: RegexStr(r"^炉芯机骸$", raw="炉芯机骸"),
        Language.EN: RegexStr(flex_ws(r"^Reactor Husk$"), raw="Reactor Husk"),
    },
    I18nText.EnemySigillum: {
        Language.ZH: RegexStr(r"^辛吉勒姆$", raw="辛吉勒姆"),
        Language.EN: RegexStr(flex_ws(r"^Sigillum$"), raw="Sigillum"),
    },
    I18nText.EnemyNamelessExplorer: {
        Language.ZH: RegexStr(r"^无铭探索者$", raw="无铭探索者"),
        Language.EN: RegexStr(flex_ws(r"^Nameless Explorer$"), raw="Nameless Explorer"),
    },
    I18nText.EnemyDenia: {
        Language.ZH: RegexStr(r"^达妮娅$", raw="达妮娅"),
        Language.EN: RegexStr(flex_ws(r"^Denia$"), raw="Denia"),
    },
    I18nText.EnemyNightmareAdamSmasher: {
        Language.ZH: RegexStr(r"^梦.?亚当.?重锤$", raw="梦魇亚当·重锤"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare.? Adam Smasher$"), raw="Nightmare: Adam Smasher"),
    },
    I18nText.EnemyMyriadSnareRustfireChassis: {
        Language.ZH: RegexStr(r"^万.?牢.?朽躯$", raw="万囮牢·朽躯"),
        Language.EN: RegexStr(flex_ws(r"^Myriad Snare.? Rustfire Chassis$"), raw="Myriad Snare: Rustfire Chassis"),
    },

    # ------- Sonata -------
    I18nText.FreezingFrost: {
        Language.ZH: RegexStr(r"^凝夜白霜$", raw="凝夜白霜"),
        Language.EN: RegexStr(flex_ws(r"^Freezing Frost$"), raw="Freezing Frost"),
    },
    I18nText.MoltenRift: {
        Language.ZH: RegexStr(r"^熔山裂谷$", raw="熔山裂谷"),
        Language.EN: RegexStr(flex_ws(r"^Molten Rift$"), raw="Molten Rift"),
    },
    I18nText.VoidThunder: {
        Language.ZH: RegexStr(r"^彻空冥雷$", raw="彻空冥雷"),
        Language.EN: RegexStr(flex_ws(r"^Void Thunder$"), raw="Void Thunder"),
    },
    I18nText.SierraGale: {
        Language.ZH: RegexStr(r"^啸谷长风$", raw="啸谷长风"),
        Language.EN: RegexStr(flex_ws(r"^Sierra Gale$"), raw="Sierra Gale"),
    },
    I18nText.CelestialLight: {
        Language.ZH: RegexStr(r"^浮星祛暗$", raw="浮星祛暗"),
        Language.EN: RegexStr(flex_ws(r"^Celestial Light$"), raw="Celestial Light"),
    },
    I18nText.HavocEclipse: {
        Language.ZH: RegexStr(r"^沉日劫明$", raw="沉日劫明"),
        Language.EN: RegexStr(flex_ws(r"^Havoc Eclipse$"), raw="Havoc Eclipse"),
    },
    I18nText.RejuvenatingGlow: {
        Language.ZH: RegexStr(r"^隐世回光$", raw="隐世回光"),
        Language.EN: RegexStr(flex_ws(r"^Rejuvenating Glow$"), raw="Rejuvenating Glow"),
    },
    I18nText.MoonlitClouds: {
        Language.ZH: RegexStr(r"^轻云出月$", raw="轻云出月"),
        Language.EN: RegexStr(flex_ws(r"^Moonlit Clouds$"), raw="Moonlit Clouds"),
    },
    I18nText.LingeringTunes: {
        Language.ZH: RegexStr(r"^不绝余音$", raw="不绝余音"),
        Language.EN: RegexStr(flex_ws(r"^Lingering Tunes$"), raw="Lingering Tunes"),
    },
    I18nText.FrostyResolve: {
        Language.ZH: RegexStr(r"^凌冽决断之心$", raw="凌冽决断之心"),
        Language.EN: RegexStr(flex_ws(r"^Frosty Resolve$"), raw="Frosty Resolve"),
    },
    I18nText.EternalRadiance: {
        Language.ZH: RegexStr(r"^此间永驻之光$", raw="此间永驻之光"),
        Language.EN: RegexStr(flex_ws(r"^Eternal Radiance$"), raw="Eternal Radiance"),
    },
    I18nText.MidnightVeil: {
        Language.ZH: RegexStr(r"^幽夜隐匿之帷$", raw="幽夜隐匿之帷"),
        Language.EN: RegexStr(flex_ws(r"^Midnight Veil$"), raw="Midnight Veil"),
    },
    I18nText.EmpyreanAnthem: {
        Language.ZH: RegexStr(r"^高天共奏之曲$", raw="高天共奏之曲"),
        Language.EN: RegexStr(flex_ws(r"^Empyrean Anthem$"), raw="Empyrean Anthem"),
    },
    I18nText.TidebreakingCourage: {
        Language.ZH: RegexStr(r"^无惧浪涛之勇$", raw="无惧浪涛之勇"),
        Language.EN: RegexStr(flex_ws(r"^Tidebreaking Courage$"), raw="Tidebreaking Courage"),
    },
    I18nText.GustsOfWelkin: {
        Language.ZH: RegexStr(r"^流云逝尽之空$", raw="流云逝尽之空"),
        Language.EN: RegexStr(flex_ws(r"^Gusts of Welkin$"), raw="Gusts of Welkin"),
    },
    I18nText.WindwardPilgrimage: {
        Language.ZH: RegexStr(r"^愿戴荣光之旅$", raw="愿戴荣光之旅"),
        Language.EN: RegexStr(flex_ws(r"^Windward Pilgrimage$"), raw="Windward Pilgrimage"),
    },
    I18nText.FlamingClawprint: {
        Language.ZH: RegexStr(r"^奔狼燎原之焰$", raw="奔狼燎原之焰"),
        Language.EN: RegexStr(flex_ws(r"^Flaming Clawprint$"), raw="Flaming Clawprint"),
    },
    I18nText.DreamOfTheLost: {
        Language.ZH: RegexStr(r"^失序彼岸之梦$", raw="失序彼岸之梦"),
        Language.EN: RegexStr(flex_ws(r"^Dream of the Lost$"), raw="Dream of the Lost"),
    },
    I18nText.CrownOfValor: {
        Language.ZH: RegexStr(r"^荣斗铸锋之冠$", raw="荣斗铸锋之冠"),
        Language.EN: RegexStr(flex_ws(r"^Crown of Valor$"), raw="Crown of Valor"),
    },
    I18nText.LawOfHarmony: {
        Language.ZH: RegexStr(r"^息界同调之律$", raw="息界同调之律"),
        Language.EN: RegexStr(flex_ws(r"^Law of Harmony$"), raw="Law of Harmony"),
    },
    I18nText.FlamewingsShadow: {
        Language.ZH: RegexStr(r"^焚羽猎魔之影$", raw="焚羽猎魔之影"),
        Language.EN: RegexStr(flex_ws(r"^Flamewing's Shadow$"), raw="Flamewing's Shadow"),
    },
    I18nText.ThreadOfSeveredFate: {
        Language.ZH: RegexStr(r"^命理崩毁之弦$", raw="命理崩毁之弦"),
        Language.EN: RegexStr(flex_ws(r"^Thread of Severed Fate$"), raw="Thread of Severed Fate"),
    },
    I18nText.PactOfNeonlightLeap: {
        Language.ZH: RegexStr(r"^逆光跃彩之约$", raw="逆光跃彩之约"),
        Language.EN: RegexStr(flex_ws(r"^Pact of Neonlight Leap$"), raw="Pact of Neonlight Leap"),
    },
    I18nText.HaloOfStarryRadiance: {
        Language.ZH: RegexStr(r"^星构寻辉之环$", raw="星构寻辉之环"),
        Language.EN: RegexStr(flex_ws(r"^Halo of Starry Radiance$"), raw="Halo of Starry Radiance"),
    },
    I18nText.RiteOfGildedRevelation: {
        Language.ZH: RegexStr(r"^流金溯真之式$", raw="流金溯真之式"),
        Language.EN: RegexStr(flex_ws(r"^Rite of Gilded Revelation$"), raw="Rite of Gilded Revelation"),
    },
    I18nText.TrailblazingStar: {
        Language.ZH: RegexStr(r"^长路启航之星$", raw="长路启航之星"),
        Language.EN: RegexStr(flex_ws(r"^Trailblazing Star$"), raw="Trailblazing Star"),
    },
    I18nText.ChromaticFoam: {
        Language.ZH: RegexStr(r"^斑驳粉饰之沫$", raw="斑驳粉饰之沫"),
        Language.EN: RegexStr(flex_ws(r"^Chromatic Foam$"), raw="Chromatic Foam"),
    },
    I18nText.SoundOfTrueName: {
        Language.ZH: RegexStr(r"^听唤语义之愿$", raw="听唤语义之愿"),
        Language.EN: RegexStr(flex_ws(r"^Sound of True Name$"), raw="Sound of True Name"),
    },
    I18nText.WishesOfQuietSnowfall: {
        Language.ZH: RegexStr(r"^雪落无声之愿$", raw="雪落无声之愿"),
        Language.EN: RegexStr(flex_ws(r"^Wishes of Quiet Snowfall$"), raw="Wishes of Quiet Snowfall"),
    },
    I18nText.ReelOfSplicedMemories: {
        Language.ZH: RegexStr(r"^剪心辑梦之影$", raw="剪心辑梦之影"),
        Language.EN: RegexStr(flex_ws(r"^Reel of Spliced Memories$"), raw="Reel of Spliced Memories"),
    },
    I18nText.ShadowOfShatteredDreams: {
        Language.ZH: RegexStr(r"^碎梦亡鬼之魇$", raw="碎梦亡鬼之魇"),
        Language.EN: RegexStr(flex_ws(r"^Shadow of Shattered Dreams$"), raw="Shadow of Shattered Dreams"),
    },

    # ------- Login -------
    I18nText.Login: {
        Language.ZH: r"^登录$",
        Language.EN: flex_ws(r"^Login$"),
    },

    # ------- Map -------
    I18nText.FastTravel: {
        Language.ZH: r"^快速旅行$",
        Language.EN: flex_ws(r"^Fast Travel$"),
    },
    I18nText.EnableNavigation: {
        Language.ZH: r"^导航追踪$",
        Language.EN: flex_ws(r"^Enable Navigation$"),
    },
    I18nText.SwitchMap: {
        Language.ZH: RegexStr(r"^切换地图$", raw="切换地图"),
        Language.EN: RegexStr(flex_ws(r"^Switch Map$"), raw="Switch Map"),
    },
    I18nText.Huanglong: {
        Language.ZH: RegexStr(r"^.?珑$", raw="瑝珑"),
        Language.EN: RegexStr(flex_ws(r"^Huanglong$"), raw="Huanglong"),
    },
    I18nText.Jinzhou: {
        Language.ZH: RegexStr(r"^今州$", raw="今州"),
        Language.EN: RegexStr(flex_ws(r"^Jinzhou$"), raw="Jinzhou"),
    },
    I18nText.JinzhouCity: {
        Language.ZH: RegexStr(r"^今州城$", raw="今州城"),
        Language.EN: RegexStr(flex_ws(r"^Jinzhou$"), raw="Jinzhou"),
    },
    I18nText.Mengzhou: {
        Language.ZH: RegexStr(r"^梦州$", raw="梦州"),
        Language.EN: RegexStr(flex_ws(r"^Mengzhou$"), raw="Mengzhou"),
    },
    I18nText.TheBlackShores: {
        Language.ZH: RegexStr(r"^黑海岸$", raw="黑海岸"),
        Language.EN: RegexStr(flex_ws(r"^The Black Shores$"), raw="The Black Shores"),
    },
    I18nText.Rinascita: {
        Language.ZH: RegexStr(r"^黎那汐塔$", raw="黎那汐塔"),
        Language.EN: RegexStr(flex_ws(r"^Rinascita$"), raw="Rinascita"),
    },
    I18nText.RoyaFrostlands: {
        Language.ZH: RegexStr(r"^罗伊冰原$", raw="罗伊冰原"),
        Language.EN: RegexStr(flex_ws(r"^Roya Frostlands$"), raw="Roya Frostlands"),
    },

    # ------- Notice -------
    I18nText.Confirm: {
        Language.ZH: RegexStr(r"^确认$", raw="确认"),
        Language.EN: RegexStr(flex_ws(r"^Confirm$"), raw="Confirm"),
    },
    I18nText.Restart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Restart$"), raw="Restart"),
    },
    I18nText.Exit: {
        Language.ZH: RegexStr(r"^离开$", raw="离开"),
        Language.EN: RegexStr(flex_ws(r"^Exit$"), raw="Exit"),
    },
    I18nText.CollectSupplies: {
        Language.ZH: RegexStr(r"^收取物资$", raw="收取物资"),
        Language.EN: RegexStr(flex_ws(r"^Collect Supplies$"), raw="Collect Supplies"),
    },
    I18nText.ItemsObtained: {
        Language.ZH: RegexStr(r"^获得$", raw="获得"),
        Language.EN: RegexStr(flex_ws(r"^Items Obtained$"), raw="Items Obtained"),
    },
    I18nText.TapTheBlankAreaToClose: {
        Language.ZH: RegexStr(r"^点击空白区域关闭$", raw="点击空白区域关闭"),
        Language.EN: RegexStr(flex_ws(r"^Tap the blank area to close$"), raw="Tap the blank area to close"),
    },
    I18nText.SelectARevivalItem: {
        Language.ZH: RegexStr(r"^选择复苏物品$", raw="选择复苏物品"),
        Language.EN: RegexStr(flex_ws(r"^Select a Revival Item$"), raw="Select a Revival Item"),
    },
    I18nText.DoNotShowAgain: {
        Language.ZH: RegexStr(r"^本次登录不再提示$", raw="本次登录不再提示"),
        Language.EN: RegexStr(flex_ws(r"^Do not show again$"), raw="Do not show again"),
    },
    I18nText.LuniteSubscriptionReward: {
        Language.ZH: RegexStr(r"点击领取今日月相观测卡奖励", raw="点击领取今日月相观测卡奖励"),
        Language.EN: RegexStr(
            flex_ws(r"Tap to claim today|Lunite Subscription reward"),
            raw="Tap to claim today's LuniteSubscription reward"
        )
    },

    # ------- Dialogue -------
    I18nText.Absorb: {
        Language.ZH: RegexStr(r"^吸收$", raw="吸收"),
        Language.EN: RegexStr(flex_ws(r"^Absorb$"), raw="Absorb"),
    },
    I18nText.ClaimRewards: {
        Language.ZH: RegexStr(r"^领取奖励$", raw="领取奖励"),
        Language.EN: RegexStr(flex_ws(r"^Claim Rewards$"), raw="Claim Rewards"),
    },
    I18nText.ChallengeAgain: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Challenge Again$"), raw="Challenge Again"),
    },

    # ------- Terminal -------
    I18nText.Terminal: {
        Language.ZH: RegexStr(r"^终端$", raw="终端"),
        Language.EN: RegexStr(flex_ws(r"^Terminal$"), raw="Terminal"),
    },
    I18nText.Birthday: {
        Language.ZH: RegexStr(r"^生日$", raw="生日"),
        Language.EN: RegexStr(flex_ws(r"^Birthday$"), raw="Birthday"),
    },
    I18nText.SOL3Phase: {
        Language.ZH: RegexStr(r"^索拉等级$", raw="索拉等级"),
        Language.EN: RegexStr(flex_ws(r"^SOL3 Phase$"), raw="SOL3 Phase"),
    },
    I18nText.UnionLevel: {
        Language.ZH: RegexStr(r"^联觉等级$", raw="联觉等级"),
        Language.EN: RegexStr(flex_ws(r"^Union Level$"), raw="Union Level"),
    },
    I18nText.UnionEXP: {
        Language.ZH: RegexStr(r"^联觉经验$", raw="联觉经验"),
        Language.EN: RegexStr(flex_ws(r"^Union EXP$"), raw="Union EXP"),
    },
    I18nText.Events: {
        Language.ZH: RegexStr(r"^活动$", raw="活动"),
        Language.EN: RegexStr(flex_ws(r"^Events$"), raw="Events"),
    },
    I18nText.TerminalPioneerPodcast: {
        Language.ZH: RegexStr(r"^先约电台$", raw="先约电台"),
        # 特殊，太长文字换行了
        Language.EN: RegexStr(flex_ws(r"^Pioneer|Podcast$"), raw="Pioneer Podcast"),
    },
    I18nText.Team: {
        Language.ZH: RegexStr(r"^编队$", raw="编队"),
        Language.EN: RegexStr(flex_ws(r"^Team$"), raw="Team"),
    },
    I18nText.DataBank: {
        Language.ZH: r"^数据坞$",
        Language.EN: flex_ws(r"^Data Bank$"),
    },
    I18nText.Guidebook: {
        Language.ZH: RegexStr(r"^索拉指南$", raw="索拉指南"),
        Language.EN: RegexStr(flex_ws(r"^Guidebook$"), raw="Guidebook$"),
    },
    I18nText.Map: {
        Language.ZH: RegexStr(r"^地图$", raw="地图"),
        Language.EN: RegexStr(flex_ws(r"^Map$"), raw="Map"),
    },
    I18nText.Mail: {
        Language.ZH: RegexStr(r"^邮件$", raw="邮件"),
        Language.EN: RegexStr(flex_ws(r"^Mail$"), raw="Mail"),
    },

    # ------- Pioneer Podcast -------
    I18nText.PioneerPodcast: {
        Language.ZH: RegexStr(r"^先约电台$", raw="先约电台"),
        Language.EN: RegexStr(flex_ws(r"^Pioneer Podcast$"), raw="Pioneer Podcast"),
    },
    I18nText.PioneerPodcastUnavailable: {
        Language.ZH: RegexStr(r"先约电台.*?暂未开播", raw="当前先约电台各频道暂未开播"),
        Language.EN: RegexStr(
            flex_ws(r"Pioneer Podcast.*?unavailable"),
            raw="All channels on the Pioneer Podcast are currently unavailable"),
    },
    I18nText.PodcastTasks: {
        Language.ZH: RegexStr(r"^电台任务$", raw="电台任务"),
        Language.EN: RegexStr(flex_ws(r"^Podcast Tasks$"), raw="Podcast Tasks"),
    },
    I18nText.PioneerPodcastClaimAll: {
        Language.ZH: RegexStr(r"键领取$", raw="一键领取"),
        Language.EN: RegexStr(flex_ws(r"Claim All$"), raw="Claim All"),
    },
    I18nText.PioneerPodcastConfirm: {
        Language.ZH: RegexStr(r"^确定$", raw="确定"),
        Language.EN: RegexStr(flex_ws(r"Confirm$"), raw="Confirm"),
    },

    # ------- Data Bank -------
    I18nText.TargetedMerge: {
        Language.ZH: r"^定向融合$",
        Language.EN: flex_ws(r"^Targeted Merge$"),
    },
    I18nText.StandardMerge: {
        Language.ZH: r"^标准融合$",
        Language.EN: flex_ws(r"^Standard Merge$"),
    },
    I18nText.PleaseSelectAtLeast5Echoes: {
        Language.ZH: RegexStr(r"^请至少放入", raw="请至少放入", desc="请至少放入5个声骸"),
        Language.EN: RegexStr(
            flex_ws(r"^Please select at least"),
            raw="Please select at least",
            desc="Please select at least 5 Echoes"
        ),
    },
    I18nText.DataMergeCount: {
        Language.ZH: r"^数据融合次数",
        Language.EN: flex_ws(r"^Data Merge Count"),
    },

    # ------- Guidebook -------
    I18nText.Activity: {
        Language.ZH: RegexStr(r"^活跃行迹$", raw="活跃行迹"),
        Language.EN: RegexStr(flex_ws(r"^Activity$"), raw="Activity"),
    },
    I18nText.MaterialsSpots: {
        Language.ZH: RegexStr(r"^素材获取$", raw="素材获取"),
        Language.EN: RegexStr(flex_ws(r"^Materials Spots$"), raw="Materials Spots"),
    },
    I18nText.RecurringChallenges: {
        Language.ZH: r"^周期挑战$",
        Language.EN: flex_ws(r"^Recurring Challenges$"),
    },
    I18nText.PathOfGrowth: {
        Language.ZH: r"^强者之路$",
        Language.EN: flex_ws(r"^Path of Growth$"),
    },
    I18nText.EnemyTracing: {
        Language.ZH: r"^敌迹探寻$",
        Language.EN: flex_ws(r"^Enemy Tracing$"),
    },
    I18nText.Milestones: {
        Language.ZH: r"^漂泊日志$",
        Language.EN: flex_ws(r"^Milestones$"),
    },

    ## ------- Guidebook Common -------
    I18nText.CannotPerformThisActionDuringBattle: {
        Language.ZH: RegexStr(
            flex_ws(r"战斗中无法进行该操作"),
            raw="提示：战斗中无法进行该操作",
        ),
        Language.EN: RegexStr(
            flex_ws(r"^Cannot perform this action during battle"),
            raw="Cannot perform this action during battle",
        ),
    },
    I18nText.DoubleDropChancesToday: {
        Language.ZH: RegexStr(
            flex_ws(r"^今日剩余双倍奖励次数"),
            raw="今日剩余双倍奖励次数",
            desc="今日剩余双倍奖励次数: 3/3"
        ),
        Language.EN: RegexStr(
            flex_ws(r"^Double Drop Chances Today"),
            raw="Double Drop Chances Today",
            desc="Double Drop Chances Today: 3/3"
        ),
    },
    # 索拉指南内用到的地区
    I18nText.GuidebookMengzhou: {
        Language.ZH: RegexStr(r"梦州", raw="梦州", desc="瑝珑·梦州"),
        Language.EN: RegexStr(flex_ws(r"Mengzhou"), raw="Mengzhou", desc="Huanglong: Mengzhou"),
    },
    I18nText.GuidebookLahaiRoi: {
        Language.ZH: RegexStr(r"拉海洛", raw="拉海洛", desc="索拉里斯之极·拉海洛"),
        Language.EN: RegexStr(flex_ws(r"Lahai-Roi"), raw="Lahai-Roi", desc="Solaris's Pole: Lahai-Roi"),
    },
    I18nText.GuidebookRinascita: {
        Language.ZH: RegexStr(r"黎那汐塔", raw="黎那汐塔", desc="黎那汐塔"),
        Language.EN: RegexStr(flex_ws(r"Rinascita"), raw="Rinascita", desc="Rinascita"),
    },
    I18nText.GuidebookJinzhou: {
        Language.ZH: RegexStr(r"今州", raw="今州", desc="瑝珑·今州"),
        Language.EN: RegexStr(flex_ws(r"Jinzhou"), raw="Jinzhou", desc="Huanglong: Jinzhou"),
    },

    ## ------- Guidebook Activity -------
    I18nText.ActivityDaily: {
        Language.ZH: RegexStr(r"^活跃度$", raw="活跃度"),
        Language.EN: RegexStr(flex_ws(r"^Daily$"), raw="Daily"),
    },
    I18nText.ActivityWeekly: {
        Language.ZH: RegexStr(r"^周度游历$", raw="周度游历"),
        Language.EN: RegexStr(flex_ws(r"^Weekly$"), raw="Weekly"),
    },
    I18nText.ActivityPts: {
        Language.ZH: RegexStr(r"^活跃度$", raw="活跃度"),
        Language.EN: RegexStr(flex_ws(r"^Activity Pts$"), raw="Activity Pts"),
    },
    I18nText.WeeklyActivityPts: {
        Language.ZH: RegexStr(r"^游历值$", raw="游历值"),
        Language.EN: RegexStr(flex_ws(r"^Weekly Activity Pts$"), raw="Weekly Activity Pts"),
    },
    I18nText.ActivityClaim: {
        Language.ZH: RegexStr(r"^领取$", raw="领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim$"), raw="Claim"),
    },

    ## ------- Guidebook MaterialsSpots -------
    # 产出武器及技能材料
    I18nText.ForgeryChallenge: {
        Language.ZH: r"^凝素领域$",
        Language.EN: flex_ws(r"^Forgery Challenge$"),
    },
    # 产出经验材料
    I18nText.SimulationChallenge: {
        Language.ZH: r"^模拟领域$",
        Language.EN: flex_ws(r"^Simulation Challenge$"),
    },
    # 产出共鸣者突破材料
    I18nText.BossChallenge: {
        Language.ZH: r"^讨伐强敌$",
        Language.EN: flex_ws(r"^Boss Challenge$"),
    },
    # 产出声骸材料
    I18nText.TacetSuppression: {
        Language.ZH: r"^无音清剿$",
        Language.EN: flex_ws(r"^Tacet Suppression$"),
    },
    # 产出高级技能材料
    I18nText.WeeklyChallenge: {
        Language.ZH: r"^战歌重奏$",
        Language.EN: flex_ws(r"^Weekly Challenge$"),
    },
    # 产出梦魇声骸
    I18nText.NightmarePurification: {
        Language.ZH: RegexStr(r"^梦.?.?除$", raw="梦魇祓除"),
        Language.EN: RegexStr(flex_ws(r"^Nightmare Purification$"), raw="Nightmare Purification"),
    },
    # 产出声骸套件
    I18nText.TacetDiscordNest: {
        Language.ZH: RegexStr(r"^残象聚落$", raw="残象聚落"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Discord Nest$"), raw="Tacet Discord Nest"),
    },

    ### ------- Guidebook common -------
    I18nText.Go: {
        Language.ZH: RegexStr(r"^前往$", raw="前往"),
        Language.EN: RegexStr(flex_ws(r"^G[o0]$"), raw="Go"),
    },
    I18nText.Challenge: {
        Language.ZH: RegexStr(r"^直接挑战$", raw="直接挑战"),
        Language.EN: RegexStr(flex_ws(r"^Challenge$"), raw=r"Challenge"),
    },

    ### ------- Guidebook MaterialsSpots ForgeryChallenge -------
    I18nText.WingfallChasm: {
        Language.ZH: RegexStr(r"^.?翼云渊$", raw="陨翼云渊"),
        Language.EN: RegexStr(flex_ws(r"^Wingfall Chasm$"), raw=r"Wingfall Chasm"),
    },
    I18nText.SilentChasm: {
        Language.ZH: RegexStr(r"^静灭云渊$", raw="静灭云渊"),
        Language.EN: RegexStr(flex_ws(r"^Silent Chasm$"), raw=r"Silent Chasm"),
    },
    I18nText.SplitChasm: {
        Language.ZH: RegexStr(r"^裂斩云渊$", raw="裂斩云渊"),
        Language.EN: RegexStr(flex_ws(r"^Split Chasm$"), raw=r"Split Chasm"),
    },
    I18nText.ErodedChasm: {
        Language.ZH: RegexStr(r"^碎蚀云渊$", raw="碎蚀云渊"),
        Language.EN: RegexStr(flex_ws(r"^Eroded Chasm$"), raw=r"Eroded Chasm"),
    },
    I18nText.AshenChasm: {
        Language.ZH: RegexStr(r"^沉熄云渊$", raw="沉熄云渊"),
        Language.EN: RegexStr(flex_ws(r"^Ashen Chasm$"), raw=r"Ashen Chasm"),
    },
    I18nText.FallenSanctum: {
        Language.ZH: RegexStr(r"^荒.旧殿$", raw="荒萋旧殿"),
        Language.EN: RegexStr(flex_ws(r"^Fallen Sanctum$"), raw=r"Fallen Sanctum"),
    },
    I18nText.LessonInSunset: {
        Language.ZH: RegexStr(r"^残照终课$", raw="残照终课"),
        Language.EN: RegexStr(flex_ws(r"^Lesson in Sunset$"), raw=r"Lesson in Sunset"),
    },
    I18nText.StrickenSanctum: {
        Language.ZH: RegexStr(r"^灾逆旧殿$", raw="灾逆旧殿"),
        Language.EN: RegexStr(flex_ws(r"^Stricken Sanctum$"), raw=r"Stricken Sanctum"),
    },
    I18nText.LessonInVoid: {
        Language.ZH: RegexStr(r"^虚诞终课$", raw="虚诞终课"),
        Language.EN: RegexStr(flex_ws(r"^Lesson in Void$"), raw=r"Lesson in Void"),
    },
    I18nText.LessonInEmbers: {
        Language.ZH: RegexStr(r"^余.终课$", raw="余烬终课"),
        Language.EN: RegexStr(flex_ws(r"^Lesson in Embers$"), raw=r"Lesson in Embers"),
    },
    I18nText.GardenOfSalvation: {
        Language.ZH: RegexStr(r"^赦罪庭园$", raw="赦罪庭园"),
        Language.EN: RegexStr(flex_ws(r"^Garden of Salvation$"), raw=r"Garden of Salvation"),
    },
    I18nText.AbyssOfInitiation: {
        Language.ZH: RegexStr(r"^浸礼海渊$", raw="浸礼海渊"),
        Language.EN: RegexStr(flex_ws(r"^Abyss of Initiation$"), raw=r"Abyss of Initiation"),
    },
    I18nText.GardenOfAdoration: {
        Language.ZH: RegexStr(r"^赞颂庭园$", raw="赞颂庭园"),
        Language.EN: RegexStr(flex_ws(r"^Garden of Adoration$"), raw=r"Garden of Adoration"),
    },
    I18nText.AbyssOfSacrifice: {
        Language.ZH: RegexStr(r"^祝祭海渊$", raw="祝祭海渊"),
        Language.EN: RegexStr(flex_ws(r"^Abyss of Sacrifice$"), raw=r"Abyss of Sacrifice"),
    },
    I18nText.AbyssOfConfession: {
        Language.ZH: RegexStr(r"^告解海渊$", raw="告解海渊"),
        Language.EN: RegexStr(flex_ws(r"^Abyss of Confession$"), raw=r"Abyss of Confession"),
    },
    I18nText.FlamingRemnants: {
        Language.ZH: RegexStr(r"^熔毁废都$", raw="熔毁废都"),
        Language.EN: RegexStr(flex_ws(r"^Flaming Remnants$"), raw=r"Flaming Remnants"),
    },
    I18nText.MistyForest: {
        Language.ZH: RegexStr(r"^旋雾之森$", raw="旋雾之森"),
        Language.EN: RegexStr(flex_ws(r"^Misty Forest$"), raw=r"Misty Forest"),
    },
    I18nText.ErodedRuins: {
        Language.ZH: RegexStr(r"^侵蚀废都$", raw="侵蚀废都"),
        Language.EN: RegexStr(flex_ws(r"^Eroded Ruins$"), raw=r"Eroded Ruins"),
    },
    I18nText.MoonlitGroves: {
        Language.ZH: RegexStr(r"^流月之森$", raw="流月之森"),
        Language.EN: RegexStr(flex_ws(r"^Moonlit Groves$"), raw=r"Moonlit Groves"),
    },
    I18nText.MarigoldWoods: {
        Language.ZH: RegexStr(r"^欲燃之森$", raw="欲燃之森"),
        Language.EN: RegexStr(flex_ws(r"^Marigold Woods$"), raw=r"Marigold Woods"),
    },
    # weapon
    I18nText.Sword: {
        Language.ZH: RegexStr(r"迅刀$", raw="迅刀"),
        Language.EN: RegexStr(flex_ws(r"Sword$"), raw=r"Sword"),
    },
    I18nText.Rectifier: {
        Language.ZH: RegexStr(r"音感仪$", raw="音感仪"),
        Language.EN: RegexStr(flex_ws(r"Rectifier$"), raw=r"Rectifier"),
    },
    I18nText.Broadblade: {
        Language.ZH: RegexStr(r"长刃$", raw="长刃"),
        Language.EN: RegexStr(flex_ws(r"Broadblade$"), raw=r"Broadblade"),
    },
    I18nText.Gauntlets: {
        Language.ZH: RegexStr(r"臂铠$", raw="臂铠"),
        Language.EN: RegexStr(flex_ws(r"Gauntlets$"), raw=r"Gauntlets"),
    },
    I18nText.Pistols: {
        Language.ZH: RegexStr(r"佩枪$", raw="佩枪"),
        Language.EN: RegexStr(flex_ws(r"Pistols$"), raw=r"Pistols"),
    },
    # instance
    I18nText.EnterTheForgeryChallenge: {
        Language.ZH: RegexStr(r"^进入.?凝素领域", raw="进入「凝素领域」"),
        Language.EN: RegexStr(flex_ws(r"^Enter the .Forgery Challenge"), raw=r"Enter the \"Forgery Challenge\""),
    },
    I18nText.Level: {
        Language.ZH: RegexStr(r"等级\d[\do]", raw="等级", desc="等级40"),
        Language.EN: RegexStr(flex_ws(r"Level \d[\do]"), raw=r"Level", desc=r"Level40"),
    },
    I18nText.Match: {
        Language.ZH: RegexStr(r"^多人匹配$", raw="多人匹配"),
        Language.EN: RegexStr(flex_ws(r"^Match$"), raw=r"Match"),
    },
    I18nText.SoloChallenge: {
        Language.ZH: RegexStr(r"^单人挑战$", raw="单人挑战"),
        Language.EN: RegexStr(flex_ws(r"^Solo Challenge$"), raw=r"Solo Challenge"),
    },
    I18nText.DefeatTheEnemiesWithinTimeLimit: {
        Language.ZH: RegexStr(r"^限时击败敌人", raw="限时击败敌人", desc="限时击败敌人: 1/5"),
        Language.EN: RegexStr(
            flex_ws(r"^Defeat the enemies within time"), raw=r"Defeat the enemies within time limit"),
    },
    I18nText.ForgeryChallengeComplete: {
        Language.ZH: RegexStr(r"^挑战成功$", raw="挑战成功"),
        Language.EN: RegexStr(flex_ws(r"^Challenge Complete$"), raw=r"Challenge Complete"),
    },
    I18nText.ForgeryClaim: {
        Language.ZH: RegexStr(r"^单倍领取$", raw="单倍领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim$"), raw=r"Claim"),
    },
    I18nText.ForgeryClaimX2: {
        Language.ZH: RegexStr(r"^双倍领取$", raw="双倍领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim.?2$"), raw="Claim*2"),
    },
    I18nText.ForgeryRestart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Restart$"), raw="Restart"),
    },
    I18nText.ForgeryExit: {
        Language.ZH: RegexStr(r"^退出副本$", raw="退出副本"),
        Language.EN: RegexStr(flex_ws(r"^Exit$"), raw="Exit"),
    },

    ### ------- Guidebook MaterialsSpots TacetSuppression -------
    I18nText.WesternFangPeaksTacetField: {
        Language.ZH: RegexStr(r"^方.西峰无音区$", raw="方擎西峰无音区"),
        Language.EN: RegexStr(flex_ws(r"^Western Fang Peaks"), raw=r"Western Fang Peaks Tacet Field"),
    },
    I18nText.EasternXuanPeaksTacetField: {
        Language.ZH: RegexStr(r"^玄幽东岳无音区$", raw="玄幽东岳无音区"),
        Language.EN: RegexStr(flex_ws(r"^Eastern Xuan Peaks"), raw=r"Eastern Xuan Peaks Tacet Field"),
    },
    I18nText.TacetFieldSolisiaLanding: {
        Language.ZH: RegexStr(r"^落日.?屿无音区$", raw="落日堤屿无音区"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Field.*?Solisia"), raw=r"Tacet Field: Solisia Landing"),
    },
    I18nText.TacetFieldFrostlandsTransitPort: {
        Language.ZH: RegexStr(r"^冰原运输港无音区$", raw="冰原运输港无音区"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Field.*?Frostlands"), raw=r"Tacet Field: Frostlands Transit Port"),
    },
    I18nText.TacetFieldMountGjallar: {
        Language.ZH: RegexStr(r"^加拉尔冠阶无音区$", raw="加拉尔冠阶无音区"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Field.*?Mount"), raw=r"Tacet Field: Mount Gjallar"),
    },
    I18nText.TacetFieldMawburrowDesert: {
        Language.ZH: RegexStr(r"^隐.?深腹无音区$", raw="隐喙深腹无音区"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Field.*?Mawburrow"), raw=r"Tacet Field: Mawburrow Desert"),
    },
    I18nText.TacetFieldStagnantRun: {
        Language.ZH: RegexStr(r"^陷足流川无音区$", raw="陷足流川无音区"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Field.*?Stagnant"), raw=r"Tacet Field: Stagnant Run"),
    },
    I18nText.EchoSet: {
        Language.ZH: RegexStr(r"^声骸套装$", raw="声骸套装"),
        Language.EN: RegexStr(flex_ws(r"^Echo Set$"), raw=r"Echo Set"),
    },
    I18nText.TacetField: {
        Language.ZH: RegexStr(r"无音区", raw="无音区"),
        Language.EN: RegexStr(flex_ws(r"Tacet Field"), raw=r"Tacet Field"),
    },
    # 下面是进入无音区内的文本
    I18nText.DefeatTheTdsInTheTacetField: {
        Language.ZH: RegexStr(r"清?理无音区中涌现的残象", raw="清理无音区中涌现的残象"),
        Language.EN: RegexStr(flex_ws(r"Defeat the TDs in the"), raw=r"Defeat the TDs in the Tacet Field"),
    },
    I18nText.TacetFieldChallengeComplete: {
        Language.ZH: RegexStr(r"挑战达成", raw="挑战达成"),
        Language.EN: RegexStr(flex_ws(r"Challenge Complete"), raw=r"Challenge Complete"),
    },
    I18nText.TacetFieldClaim: {
        Language.ZH: RegexStr(r"^单倍领取$", raw="单倍领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim$"), raw=r"Claim"),
    },
    I18nText.TacetFieldClaimX2: {
        Language.ZH: RegexStr(r"^双倍领取$", raw="双倍领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim.?2$"), raw="Claim*2"),
    },
    I18nText.TacetFieldNoticeChallengeComplete: {
        Language.ZH: RegexStr(r"^挑战成功$", raw="挑战成功"),
        Language.EN: RegexStr(flex_ws(r"^Challenge Complete$"), raw=r"Challenge Complete"),
    },
    I18nText.TacetFieldConfirm: {
        Language.ZH: RegexStr(r"^确定$", raw="确定"),
        Language.EN: RegexStr(flex_ws(r"^Confirm$"), raw=r"Confirm"),
    },
    I18nText.TacetFieldRestart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Restart$"), raw="Restart"),
    },
    I18nText.TacetFieldExit: {
        Language.ZH: RegexStr(r"^退出副本$", raw="退出副本"),
        Language.EN: RegexStr(flex_ws(r"^Exit$"), raw="Exit"),
    },


    ### ------- Guidebook MaterialsSpots WeeklyChallenge -------
    I18nText.WeeklyChallengeWeeklyChallenge: {
        Language.ZH: RegexStr(r"战歌重奏", raw="战歌重奏", desc="xxxx·战歌重奏"),
        Language.EN: RegexStr(
            flex_ws(r"Weekly Challenge"),
            raw=r"Weekly Challenge",
            desc=r"Weekly Challenge: xxxx"),
    },
    I18nText.RemainingWeeklyAttempts: {
        Language.ZH: RegexStr(r"^本周剩余可收取次数", raw="本周剩余可收取次数", desc="本周剩余可收取次数: 3/3"),
        Language.EN: RegexStr(
            flex_ws(r"^Remaining Weekly Attempts"),
            raw=r"Remaining Weekly Attempts",
            desc=r"Remaining Weekly Attempts: 3/3"),
    },
    I18nText.LimitedTimeEarlyAccess: {
        Language.ZH: RegexStr(r"限时提前开放", raw="限时提前开放"),
        Language.EN: RegexStr(
            flex_ws(r"Limited-Time Early Access"), raw=r"Limited-Time Early Access")},
    I18nText.ArrivingAtTheDestination: {
        Language.ZH: RegexStr(r"^提前到达目标位置可能影响剧情体验", raw="提前到达目标位置可能影响剧情体验"),
        Language.EN: RegexStr(
            flex_ws(r"^Arriving at the destination"),
            raw=r"Arriving at the destination in advance may influence your story experience")
    },
    # 周本关卡名
    I18nText.CourtOfShackledSouls: {
        Language.ZH: RegexStr(r"^失坠困.?之庭", raw="失坠困咎之庭", desc="失坠困咎之庭·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"Court of Shackled Souls$"), raw=r"Court of Shackled Souls"),
    },
    I18nText.SeedOfIllusoryOrigin: {
        Language.ZH: RegexStr(r"^虚妄诞生之种", raw="虚妄诞生之种", desc="虚妄诞生之种·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"llusory Origin$"), raw=r"Seed of Illusory Origin"),
    },
    I18nText.GateOfTheLostStar: {
        Language.ZH: RegexStr(r"^星海迷途之扉", raw="星海迷途之扉", desc="星海迷途之扉·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"the Lost Star$"), raw=r"Gate of the Lost Star"),
    },
    I18nText.CinderniteApocalypse: {
        Language.ZH: RegexStr(r"^.夜天启之章", raw="烬夜天启之章", desc="烬夜天启之章·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"Cindernite Apocalypse$"), raw=r"Cindernite Apocalypse"),
    },
    I18nText.TheWheelOfBrokenFate: {
        Language.ZH: RegexStr(r"^命途断章之轮", raw="命途断章之轮", desc="命途断章之轮·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"Wheel of Broken Fate$"), raw=r"The Wheel of Broken Fate"),
    },
    I18nText.BeyondTheCrimsonCurtain: {
        Language.ZH: RegexStr(r"^彼世猩红之幕", raw="彼世猩红之幕", desc="彼世猩红之幕·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"the Crimson Curtain$"), raw=r"Beyond the Crimson Curtain"),
    },
    I18nText.TheFatedConfrontation: {
        Language.ZH: RegexStr(r"^时序命定之争", raw="时序命定之争", desc="时序命定之争·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"Fated Confrontation$"), raw=r"The Fated Confrontation"),
    },
    I18nText.StatueOfTheCrownless: {
        Language.ZH: RegexStr(r"^无冠巨像之心", raw="无冠巨像之心", desc="无冠巨像之心·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"Statue of the Crownless$"), raw=r"Statue of the Crownless"),
    },
    I18nText.ChaoticJuncture: {
        Language.ZH: RegexStr(r"^无序边境之火", raw="无序边境之火", desc="无序边境之火·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"Chaotic Juncture$"), raw=r"Chaotic Juncture"),
    },
    I18nText.BellOfArchaicChants: {
        Language.ZH: RegexStr(r"^昔日咏叹之钟", raw="昔日咏叹之钟", desc="昔日咏叹之钟·战歌重奏"),
        Language.EN: RegexStr(flex_ws(r"of Archaic Chants$"), raw=r"Bell of Archaic Chants"),
    },
    # 周本关卡boss名
    I18nText.WeeklyBossThousandPuppetPavilion: {
        Language.ZH: RegexStr(r"千傀重楼", raw="千傀重楼"),
        Language.EN: RegexStr(r"Thousand-Puppet Pavilion", raw="Thousand-Puppet Pavilion"),
    },
    I18nText.WeeklyBossDenia: {
        Language.ZH: RegexStr(r"达妮娅", raw="达妮娅"),
        Language.EN: RegexStr(r"Denia", raw="Denia"),
    },
    I18nText.WeeklyBossSigillum: {
        Language.ZH: RegexStr(r"辛吉勒姆", raw="辛吉勒姆"),
        Language.EN: RegexStr(r"Sigillum", raw="Sigillum"),
    },
    I18nText.WeeklyBossThrenodianLeviathan: {
        Language.ZH: RegexStr(r"鸣式·利维亚坦", raw="鸣式·利维亚坦"),
        Language.EN: RegexStr(r"Threnodian: Leviathan", raw="Threnodian: Leviathan"),
    },
    I18nText.WeeklyBossFleurdelys: {
        Language.ZH: RegexStr(r"芙露德莉斯", raw="芙露德莉斯"),
        Language.EN: RegexStr(r"Fleurdelys", raw="Fleurdelys"),
    },
    I18nText.WeeklyBossHecate: {
        Language.ZH: RegexStr(r"赫卡忒", raw="赫卡忒"),
        Language.EN: RegexStr(r"Hecate", raw="Hecate"),
    },
    I18nText.WeeklyBossJue: {
        Language.ZH: RegexStr(r"角", raw="角"),
        Language.EN: RegexStr(r"Jué", raw="Jué"),
    },
    I18nText.WeeklyBossCrownless: {
        Language.ZH: RegexStr(r"无妄者", raw="无妄者"),
        Language.EN: RegexStr(r"Dreamless", raw="Dreamless"),
    },
    I18nText.WeeklyBossScarAberrantNightmare: {
        Language.ZH: RegexStr(r"伤痕·异生梦魇", raw="伤痕·异生梦魇"),
        Language.EN: RegexStr(r"Scar: Aberrant Nightmare", raw=r"Scar: Aberrant Nightmare", desc="Chaotic Juncture"),
    },
    I18nText.WeeklyBossBellBorneGeochelone: {
        Language.ZH: RegexStr(r"鸣钟之龟", raw="鸣钟之龟"),
        Language.EN: RegexStr(r"Bell-Borne Geochelone", raw="Bell-Borne Geochelone"),
    },
    # instance
    I18nText.EnterTheSonoroSphere: {
        Language.ZH: RegexStr(r"^进入声之领域$", raw="进入声之领域"),
        Language.EN: RegexStr(flex_ws(r"^Enter the Sonoro Sphere$"), raw=r"Enter the Sonoro Sphere"),
    },
    I18nText.WeeklySuggestedLv: {
        Language.ZH: RegexStr(r"推荐等级.*\d+", raw="推荐等级", desc=r"推荐等级90"),
        Language.EN: RegexStr(flex_ws(r"Suggested.*\d+"), raw=r"Suggested", desc=r"Suggested Lv.90"),
    },
    I18nText.WeeklyRemainingAttempts: {
        Language.ZH: RegexStr(r"本周剩余可收取次数", raw="本周剩余可收取次数", desc="本周剩余可收取次数: 3/3"),
        Language.EN: RegexStr(
            flex_ws(r"Remaining Attempts"), raw=r"Remaining Attempts", desc=r"Remaining Attempts: 3/3"),
    },
    I18nText.WeeklySoloChallenge: {
        Language.ZH: RegexStr(r"^单人挑战$", raw="单人挑战"),
        Language.EN: RegexStr(flex_ws(r"^Solo Challenge$"), raw=r"Solo Challenge"),
    },
    I18nText.YourCurrentSol3Phase: {
        Language.ZH: RegexStr(r"^索拉等级与声之领", raw="索拉等级与声之领域推荐等级差距过大"),
        Language.EN: RegexStr(
            flex_ws(r"^Your current SOL3 Phase"),
            raw=r"Your current SOL3 Phase is significantly higher than the recommended level for this Sonoro Sphere"),
    },
    I18nText.WeeklyDefeatTheEnemy: {
        Language.ZH: RegexStr(r"击败", raw="击败", desc="击败敌人|击败辛吉勒姆"),
        Language.EN: RegexStr(
            flex_ws(r"eat the enemy|feat Sig"), raw=r"Defeat", desc=r"Defeat the enemy|Defeat Sigillum"),
    },
    I18nText.WeeklyClaimRewards: {
        Language.ZH: RegexStr(r"^领取奖励$", raw="领取奖励"),
        Language.EN: RegexStr(flex_ws(r"^Claim Rewards|Claim the rewards$"), raw=r"Claim Rewards"),
    },
    # F领取奖励弹出页面
    I18nText.WeeklyConfirm: {
        Language.ZH: RegexStr(r"^确认$", raw="确认"),
        Language.EN: RegexStr(flex_ws(r"^Confirm$"), raw="Confirm", desc="Replenish Waveplate"),
    },
    I18nText.WeeklyCancel: {
        Language.ZH: RegexStr(r"^取消$", raw="取消"),
        Language.EN: RegexStr(flex_ws(r"^Cancel$"), raw="Cancel", desc="Replenish Waveplate"),
    },
    # 消耗体力领取奖励后弹出页面
    I18nText.WeeklyRestart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Restart$"), raw="Restart"),
    },
    I18nText.WeeklyExit: {
        Language.ZH: RegexStr(r"^退出副本$", raw="退出副本"),
        Language.EN: RegexStr(flex_ws(r"^Exit$"), raw="Exit"),
    },
    # 领取奖励，但次数用尽时弹出页面的内容
    I18nText.YouHaveReachedTheChallengeLimit: {
        Language.ZH: RegexStr(r"^收取物资次数已达到上限", raw="收取物资次数已达到上限"),
        Language.EN: RegexStr(
            flex_ws(r"^You have reached the challenge limit"), raw="You have reached the challenge limit"),
    },

    ### ------- Guidebook MaterialsSpots TacetDiscordNest -------
    I18nText.TacetDiscordNestTacetDiscordNest: {
        Language.ZH: RegexStr(r"残象聚落", raw="残象聚落"),
        Language.EN: RegexStr(flex_ws(r"Tacet Discord Nest"), raw="Tacet Discord Nest"),
    },
    # I18nText.LahaiRoi: {
    #     Language.ZH: r"^拉海洛$",
    #     Language.EN: flex_ws(r"^Lahai-Roi$"),
    # },
    I18nText.SouthernYuanHillsTacetDiscordNest: {
        Language.ZH: RegexStr(r"^落渊南丘残象聚落$", raw="落渊南丘残象聚落"),
        Language.EN: RegexStr(flex_ws(r"^Southern Yuan Hills"), raw=r"Southern Yuan Hills Tacet Discord Nest"),
    },
    I18nText.StarblindCrashsiteTacetDiscordNest: {
        Language.ZH: RegexStr(r"^盲望之塌残象聚落$", raw="盲望之塌残象聚落"),
        Language.EN: RegexStr(flex_ws(r"^Starblind Crashsite"), raw=r"Starblind Crashsite Tacet Discord Nest"),
    },
    I18nText.RebirthUplandsTacetDiscordNest: {
        Language.ZH: RegexStr(r"^复生丘原残象聚落$", raw="复生丘原残象聚落"),
        Language.EN: RegexStr(flex_ws(r"^Rebirth Uplands"), raw=r"Rebirth Uplands Tacet Discord Nest"),
    },
    I18nText.StagnantRunTacetDiscordNest: {
        Language.ZH: RegexStr(r"^陷足流川残象聚落$", raw="陷足流川残象聚落"),
        Language.EN: RegexStr(flex_ws(r"^Stagnant Run"), raw=r"Stagnant Run Tacet Discord Nest"),
    },
    I18nText.TacetDiscordDefeated: {
        Language.ZH: RegexStr(r"^已击败残象.*\d.*", raw=r"已击败残象:0/48"),
        Language.EN: RegexStr(flex_ws(r"^Tacet Discords Defeated.*\d.*"), raw=r"Tacet Discords Defeated: 0/48"),
    },

    # ------- Team -------
    I18nText.QuickSetup: {
        Language.ZH: RegexStr(r"^快速编队", raw="快速编队"),
        Language.EN: RegexStr(flex_ws(r"Quick Setup"), raw="Quick Setup"),
    },
    I18nText.Deployed: {
        Language.ZH: RegexStr(r"^已出战", raw="已出战"),
        Language.EN: RegexStr(flex_ws(r"Deployed"), raw="Deployed"),
    },
    I18nText.Deploy: {
        Language.ZH: RegexStr(r"^出战", raw="出战"),
        Language.EN: RegexStr(flex_ws(r"Deploy"), raw="Deploy"),
    },
    I18nText.ResonatorDowned: {
        Language.ZH: RegexStr(r"^失去意识$", raw="失去意识"),
        Language.EN: RegexStr(flex_ws(r"^Resonator Downed$"), raw="Resonator Downed"),
    },
    # instance
    I18nText.StartChallenge: {
        Language.ZH: RegexStr(r"^.{0,1}开启挑战$", raw="开启挑战"),
        Language.EN: RegexStr(flex_ws(r"^.{0,2}tart Challenge$"), raw=r"Start Challenge"),
    },

    # ------- Mail -------
    I18nText.Mailbox: {
        Language.ZH: RegexStr(r"^全部邮件", raw="全部邮件"),
        Language.EN: RegexStr(flex_ws(r"Mailbox"), raw="Mailbox"),
    },
    I18nText.MailClaimAll: {
        Language.ZH: RegexStr(r"^全部领取", raw="全部领取"),
        Language.EN: RegexStr(flex_ws(r"Claim All"), raw="Claim All"),
    },

    # ------- (Overworld) TacetDiscordNest -------
    I18nText.ClearTheTacetDiscordNest: {
        Language.ZH: RegexStr(r"清?理聚落中的残象?", raw="清理聚落中的残象"),
        Language.EN: RegexStr(flex_ws(r"Clear the Tacet Discord Nest"), raw="Clear the Tacet Discord Nest"),
    },
    I18nText.TacetDiscordNestCleared: {
        Language.ZH: RegexStr(r"残?象聚落已清理?", raw="残象聚落已清理"),
        Language.EN: RegexStr(flex_ws(r"Tacet Discord Nest Cleared"), raw="Tacet Discord Nest Cleared"),
    },
    I18nText.ClearTheTacetDiscordNestMengzhou: {
        Language.ZH: RegexStr(r"(清.|剿)残象聚落?", raw="清剿残象聚落"),
        Language.EN: RegexStr(flex_ws(r"Clear the Tacet Discord Nest"), raw="Clear the Tacet Discord Nest"),
    },
    I18nText.TacetDiscordNestClearedMengzhou: {
        Language.ZH: RegexStr(r"残?象聚落已清剿?", raw="残象聚落已清剿"),
        Language.EN: RegexStr(flex_ws(r"Tacet Discord Nest Cleared"), raw="Tacet Discord Nest Cleared"),
    },

    # ------- View页面专用 -------
    # 这几个词在很多页面都有，而且名字有细微差异，不同语言间也有差异，很难统一，各功能单独维护自己的一份
    I18nText.ViewClaimRewards: {
        Language.ZH: RegexStr(r"^领取奖励$", raw="领取奖励"),
        Language.EN: RegexStr(flex_ws(r"^Claim Rewards|Claim the rewards$"), raw=r"Claim Rewards"),
    },
    I18nText.ViewClaimRewardsConfirm: {
        Language.ZH: RegexStr(r"^确认$", raw="确认"),
        Language.EN: RegexStr(flex_ws(r"^Confirm$"), raw="Confirm"),
    },
    I18nText.ViewClaimRewardsCancel: {
        Language.ZH: RegexStr(r"^取消$", raw="取消"),
        Language.EN: RegexStr(flex_ws(r"^Cancel$"), raw="Cancel"),
    },
    I18nText.CrownlessResonanceCord: {
        Language.ZH: RegexStr(r"^声弦$", raw="声弦"),
        Language.EN: RegexStr(flex_ws(r"^Resonance Cord$"), raw="Resonance Cord"),
    },
    I18nText.ViewFight: {
        Language.ZH: RegexStr(r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无.?之舌)|(.?越之矛)|(.?妄之爪)|爱欲之容|盖希诺姆|(愚执之.?)|背誓之脊|遗恨之指|异海归途|荣光的灰.?)", raw="击败"),
    },
    I18nText.ViewChallengeComplete: {
        Language.ZH: RegexStr(r"^(挑战达成|挑战成功)$", raw="挑战成功"),
        Language.EN: RegexStr(flex_ws(r"^Challenge Complete$"), raw="Challenge Complete"),
    },
    I18nText.ViewChallengeFailed: {
        Language.ZH: RegexStr(r"^挑战失败$", raw="挑战失败"),
        Language.EN: RegexStr(flex_ws(r"^Challenge Failed$"), raw="Challenge Failed"),
    },
    I18nText.ViewBreakFree: {
        Language.ZH: RegexStr(r"^交替点击进行挣脱$", raw="交替点击进行挣脱"),
        Language.EN: RegexStr(flex_ws(r"^Click alternately to break free$"), raw="Click alternately to break free"),
    },
    I18nText.ViewLeaveInstanceNote: {
        Language.ZH: RegexStr(r"^提示$", raw="提示"),
        Language.EN: RegexStr(flex_ws(r"Note"), raw="Note"),
    },
    I18nText.ViewLeaveInstanceConfirm: {
        Language.ZH: RegexStr(r"^确认$", raw="确认"),
        Language.EN: RegexStr(flex_ws(r"Confirm"), raw="Confirm"),
    },
    I18nText.ViewLeaveInstanceRestart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"Restart"), raw="Restart"),
    },
    I18nText.ViewLeaveInstance2Notice: {
        Language.ZH: RegexStr(r"^提示$", raw="提示"),
        Language.EN: RegexStr(flex_ws(r"^Notice$"), raw=r"Notice"),
    },
    I18nText.ViewLeaveInstance2Confirm: {
        Language.ZH: RegexStr(r"^确认$", raw="确认"),
        Language.EN: RegexStr(flex_ws(r"^Confirm$"), raw=r"Confirm"),
    },
    I18nText.ViewLeaveInstance2Cancel: {
        Language.ZH: RegexStr(r"^取消$", raw="取消"),
        Language.EN: RegexStr(flex_ws(r"^Cancel$"), raw=r"Cancel"),
    },
    I18nText.ViewLeaveInstance2Restart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"Restart"), raw="Restart"),
    },
    I18nText.ViewLeaveInstance2Leave: {
        Language.ZH: RegexStr(r"离开", raw="离开"),
        Language.EN: RegexStr(flex_ws(r"Leave"), raw="Leave"),
    },
    I18nText.ViewForgeryChallengeExit: {
        Language.ZH: RegexStr(r"^退出副本$", raw="退出副本"),
        Language.EN: RegexStr(flex_ws(r"^Exit$"), raw="Exit"),
    },
    I18nText.ViewForgeryChallengeRestart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Restart$"), raw="Restart"),
    },
    I18nText.ViewTacetSuppressionChallengeComplete: {
        Language.ZH: RegexStr(r"^挑战成功$", raw="挑战成功"),
        Language.EN: RegexStr(flex_ws(r"^Challenge Complete$"), raw=r"Challenge Complete"),
    },
    I18nText.ViewTacetSuppressionConfirm: {
        Language.ZH: RegexStr(r"^确定$", raw="确定"),
        Language.EN: RegexStr(flex_ws(r"^Confirm$"), raw=r"Confirm"),
    },
    I18nText.ViewTacetSuppressionExit: {
        Language.ZH: RegexStr(r"^退出副本$", raw="退出副本"),
        Language.EN: RegexStr(flex_ws(r"^Exit$"), raw="Exit"),
    },
    I18nText.ViewTacetSuppressionCancel: {
        Language.ZH: RegexStr(r"^取消$", raw="取消"),
        Language.EN: RegexStr(flex_ws(r"^Cancel$"), raw=r"Cancel"),
    },
    I18nText.ViewTacetSuppressionRestart: {
        Language.ZH: RegexStr(r"^重新挑战$", raw="重新挑战"),
        Language.EN: RegexStr(flex_ws(r"^Restart$"), raw="Restart"),
    },
    I18nText.ViewTacetSuppressionClaimRewards: {
        Language.ZH: RegexStr(r"^领取奖励$", raw="领取奖励"),
        Language.EN: RegexStr(flex_ws(r"^Claim Rewards|Claim the rewards$"), raw=r"Claim Rewards"),
    },
    I18nText.ViewTacetSuppressionClaim: {
        Language.ZH: RegexStr(r"^单倍领取$", raw="单倍领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim$"), raw=r"Claim"),
    },
    I18nText.ViewTacetSuppressionClaimX2: {
        Language.ZH: RegexStr(r"^双倍领取$", raw="双倍领取"),
        Language.EN: RegexStr(flex_ws(r"^Claim.?2$"), raw="Claim*2"),
    },




}


class I18nPage:
    """语义key"""
    Name = "name"
    Include = "include"
    Exclude = "exclude"
    Assets = "assets"
    # sub key
    Text = "text"
    Limit = "limit"

    class Terminal:
        PAGE = "Terminal"
        Terminal = "Terminal"
        Birthday = "Birthday"
        SOL3Phase = "SOL3Phase"
        UnionLevel = "UnionLevel"
        UnionEXP = "UnionEXP"

        Team = "Team"
        Events = "Events"
        DataBank = "DataBank"

    class Reward_LuniteSubscriptionReward:
        PAGE = "Reward_LuniteSubscriptionReward"
        Reward = "Reward"

    class Reward_ReceiveRewards:
        PAGE = "Reward_ReceiveRewards"
        ClaimRewards = "ClaimRewards"
        Confirm = "Confirm"
        Cancel = "Cancel"

    class Boss_Crownless_ResonanceCord:
        PAGE = "Boss_Crownless_ResonanceCord"
        ResonanceCord = "ResonanceCord"

    class Boss_Dreamless_Enter:
        PAGE = "Boss_Dreamless_Enter"
        Dreamless = "Dreamless"
        Heart = "Heart"
        Enter = "Enter"
        Confirm = "Confirm"
        FastTravel = "FastTravel"

    class Boss_Jue_Enter:
        PAGE = "Boss_Jue_Enter"
        Enter = "Enter"
        Confirm = "Confirm"

    class Boss_Hecate_Enter:
        PAGE = "Boss_Hecate_Enter"
        Enter = "Enter"
        Confirm = "Confirm"

    class Boss_RecommendedLevel:
        PAGE = "Boss_RecommendedLevel"
        RecommendedLevel = "RecommendedLevel"
        SoloChallenge = "SoloChallenge"
        ClaimsRemaining = "ClaimsRemaining"

    class Boss_StartChallenge:
        PAGE = "Boss_StartChallenge"
        QuickSetup = "QuickSetup"
        StartChallenge = "StartChallenge"

    class Fight_Fight:
        PAGE = "Fight_Fight"
        Fight = "Fight"
        Activity = "Activity"
        ChallengeCompleted = "ChallengeCompleted"

    class Fight_Absorption:
        PAGE = "Fight_Absorption"
        Absorb = "Absorb"
        ClaimRewards = "ClaimRewards"

    class Fight_ChallengeCompleted:
        PAGE = "Fight_ChallengeCompleted"
        ChallengeCompleted = "ChallengeCompleted"

    class Fight_ClickAlternatelyToBreakFree:
        PAGE = "Fight_ClickAlternatelyToBreakFree"
        ClickAlternatelyToBreakFree = "ClickAlternatelyToBreakFree"

    class Fight_BreachTimeRemaining:
        PAGE = "Fight_BreachTimeRemaining"
        BreachTimeRemaining = "BreachTimeRemaining"

    class UI_ESC_LeaveInstance:
        PAGE = "UI_ESC_LeaveInstance"
        Note = "Note"
        Confirm = "Confirm"
        Restart = "Restart"

    class Notice_LeaveInstance:
        PAGE = "Notice_LeaveInstance"
        Notice = "Notice"
        Leave = "Leave"
        Confirm = "Confirm"
        Cancel = "Cancel"

    class Notice_ForgeryChallengeComplete:
        PAGE = "Notice_ForgeryChallengeComplete"
        ChallengeComplete = "ChallengeComplete"
        Exit = "Exit"
        Restart = "Restart"

    class Notice_TacetSuppression:
        PAGE = "Notice_TacetSuppression"
        ChallengeComplete = "ChallengeComplete"
        Confirm = "Confirm"
        Exit = "Exit"
        Cancel = "Cancel"
        Restart = "Restart"

    class Notice_LoseConsciousness:
        PAGE = "Notice_LoseConsciousness"
        LoseConsciousness = "LoseConsciousness"
        Revive = "Revive"

    class Notice_SelectRevivalItem:
        PAGE = "Notice_SelectRevivalItem"
        SelectRevivalItem = "SelectRevivalItem"

    class Notice_Replenish_Waveplate:
        PAGE = "Notice_Replenish_Waveplate"
        ReplenishWaveplate = "Replenish_Waveplate"

    class Notice_BlankArea:
        PAGE = "Notice_BlankArea"
        BlankArea = "BlankArea"

    class Login_ClickLink:
        PAGE = "Login_ClickLink"
        ClickLink = "ClickLink"

    class Login_AccountLogin:
        PAGE = "Login_AccountLogin"
        Text = "Text"
        Login = "Login"
        ClickLink = "ClickLink"

    class Login_Disconnected:
        PAGE = "Login_Disconnected"
        Disconnected = "Disconnected"
        LoginTimeout = "LoginTimeout"
        Confirm = "Confirm"

    class SystemNotice_UpdateCompleteExit:
        PAGE = "SystemNotice_UpdateCompleteExit"
        UpdateComplete = "UpdateComplete"
        Exit = "Exit"

    class SystemNotice_UpdateCompleteConfirm:
        PAGE = "SystemNotice_UpdateCompleteConfirm"
        UpdateComplete = "UpdateComplete"
        Confirm = "Confirm"

    class SystemNotice_Confirm_DriverVersion:
        PAGE = "SystemNotice_Confirm_DriverVersion"
        DriverVersion = "DriverVersion"
        Confirm = "Confirm"

    class SystemNotice_NetworkTimeout:
        PAGE = "SystemNotice_NetworkTimeout"
        SystemNotice = "SystemNotice"
        NetworkTimeout = "NetworkTimeout"
        Confirm = "Confirm"


# ------------- Global Page --------------

I18N_PAGES = {

    # ----------- UI -----------

    I18nPage.Terminal.PAGE: {
        Language.ZH: {
            I18nPage.Name: "UI-终端",
            I18nPage.Include: {
                I18nPage.Terminal.Events: r"^活动$",
                # I18nPage.Terminal.Birthday: r"^生日$",
                I18nPage.Terminal.SOL3Phase: r"^索拉等级$",
                I18nPage.Terminal.UnionLevel: r"^联觉等级$",
                I18nPage.Terminal.UnionEXP: r"^联觉经验$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001.png"],
        },
        Language.EN: {
            I18nPage.Name: "UI-Terminal",
            I18nPage.Include: {
                I18nPage.Terminal.Events: flex_ws(r"^Events$"),
                # I18nPage.Terminal.Birthday: flex_ws(r"^Birthday$"),
                I18nPage.Terminal.SOL3Phase: flex_ws(r"^S[O0]L3 Phase$"),
                I18nPage.Terminal.UnionLevel: flex_ws(r"^Union Level$"),
                I18nPage.Terminal.UnionEXP: flex_ws(r"^Union EXP$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001_EN.png"],
        },
    },

    # ----------- Reward -----------

    I18nPage.Reward_LuniteSubscriptionReward.PAGE: {
        Language.ZH: {
            I18nPage.Name: "每日月卡奖励",
            I18nPage.Include: {
                I18nPage.Reward_LuniteSubscriptionReward.Reward: r"点击领取今日月相观测卡奖励",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["Reward_LuniteSubscriptionReward_001.png"],
        },
        Language.EN: {
            I18nPage.Name: "Lunite Subscription reward",
            I18nPage.Include: {
                I18nPage.Reward_LuniteSubscriptionReward.Reward: RegexStr(
                    flex_ws(r"Tap to claim today|Lunite Subscription reward"),
                    raw="Tap to claim today's LuniteSubscription reward"
                ),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001_EN.png"],
        },
    },

    I18nPage.Reward_ReceiveRewards.PAGE: {
        Language.ZH: {
            I18nPage.Name: "领取奖励",
            I18nPage.Include: {
                I18nPage.Reward_ReceiveRewards.ClaimRewards: r"^领取奖励$",
                I18nPage.Reward_ReceiveRewards.Confirm: r"^确认$",
                I18nPage.Reward_ReceiveRewards.Cancel: r"^取消$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Boss -----------

    I18nPage.Boss_Crownless_ResonanceCord.PAGE: {
        Language.ZH: {
            I18nPage.Name: "无冠者-声弦",
            I18nPage.Include: {
                I18nPage.Boss_Crownless_ResonanceCord.ResonanceCord: r"^声弦$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Crownless-ResonanceCord",
            I18nPage.Include: {
                I18nPage.Boss_Crownless_ResonanceCord.ResonanceCord: flex_ws(r"^Resonance Cord$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_Dreamless_Enter.PAGE: {
        Language.ZH: {
            I18nPage.Name: "无冠者之像·心脏",
            I18nPage.Include: {
                I18nPage.Boss_Dreamless_Enter.Dreamless: r"无冠者之像",
                I18nPage.Boss_Dreamless_Enter.Heart: r"心脏",
                I18nPage.Boss_Dreamless_Enter.Enter: r"进入",
            },
            I18nPage.Exclude: {
                I18nPage.Boss_Dreamless_Enter.Confirm: r"^确认$",
                I18nPage.Boss_Dreamless_Enter.FastTravel: r"快速旅行",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_Jue_Enter.PAGE: {
        Language.ZH: {
            I18nPage.Name: "角-时序之寰",
            I18nPage.Include: {
                I18nPage.Boss_Jue_Enter.Enter: r"进入时序之",
                I18nPage.Boss_Jue_Enter.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_Hecate_Enter.PAGE: {
        Language.ZH: {
            I18nPage.Name: "声之领域|梦魇领域|最终章",
            I18nPage.Include: {
                I18nPage.Boss_Hecate_Enter.Enter: r"^(进入声之领域|进入梦.?领域|进入.*最终章.*)$",
            },
            I18nPage.Exclude: {
                I18nPage.Boss_Hecate_Enter.Confirm: r"^确认$",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_RecommendedLevel.PAGE: {
        Language.ZH: {
            I18nPage.Name: "推荐等级",
            I18nPage.Include: {
                I18nPage.Boss_RecommendedLevel.RecommendedLevel: r"推荐等级",
                I18nPage.Boss_RecommendedLevel.SoloChallenge: r"单人挑战",
                I18nPage.Boss_RecommendedLevel.ClaimsRemaining: r"可收取次数",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_StartChallenge.PAGE: {
        Language.ZH: {
            I18nPage.Name: "开启挑战",
            I18nPage.Include: {
                I18nPage.Boss_StartChallenge.QuickSetup: r"^快速编队$",
                I18nPage.Boss_StartChallenge.StartChallenge: r"^开启挑战$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "StartChallenge",
            I18nPage.Include: {
                I18nPage.Boss_StartChallenge.QuickSetup: r"^QuickSetup$",
                I18nPage.Boss_StartChallenge.StartChallenge: r"^StartChallenge$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Fight -----------

    I18nPage.Fight_Fight.PAGE: {
        Language.ZH: {
            I18nPage.Name: "战斗画面",
            I18nPage.Include: {
                I18nPage.Fight_Fight.Fight: r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无.?之舌)|(.?越之矛)|(.?妄之爪)|爱欲之容|盖希诺姆|(愚执之.?)|背誓之脊|遗恨之指|异海归途|荣光的灰.?)",
            },
            I18nPage.Exclude: {
                I18nPage.Fight_Fight.Activity: r"^(活跃度|活跃行迹)$",
                I18nPage.Fight_Fight.ChallengeCompleted: r"^挑战成功$",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_Absorption.PAGE: {
        Language.ZH: {
            I18nPage.Name: "吸收",
            I18nPage.Include: {
                I18nPage.Fight_Absorption.Absorb: r"^吸收$",
            },
            I18nPage.Exclude: {
                I18nPage.Fight_Absorption.ClaimRewards: r"^领取奖励$",
            },
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Absorb",
            I18nPage.Include: {
                I18nPage.Fight_Absorption.Absorb: flex_ws(r"^Absorb$"),
            },
            I18nPage.Exclude: {
                I18nPage.Fight_Absorption.ClaimRewards: flex_ws(r"^Claim Rewards$"),
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_ChallengeCompleted.PAGE: {
        Language.ZH: {
            I18nPage.Name: "挑战成功",
            I18nPage.Include: {
                I18nPage.Fight_ChallengeCompleted.ChallengeCompleted: r"^挑战成功$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_ClickAlternatelyToBreakFree.PAGE: {
        Language.ZH: {
            I18nPage.Name: "交替点击进行挣脱",
            I18nPage.Include: {
                I18nPage.Fight_ClickAlternatelyToBreakFree.ClickAlternatelyToBreakFree: r"^交替点击进行挣脱$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Click alternately to break free",
            I18nPage.Include: {
                I18nPage.Fight_ClickAlternatelyToBreakFree.ClickAlternatelyToBreakFree: flex_ws(
                    r"^Click alternately to break free$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_BreachTimeRemaining.PAGE: {
        Language.ZH: {
            I18nPage.Name: "破解剩余时间",
            I18nPage.Include: {
                I18nPage.Fight_BreachTimeRemaining.BreachTimeRemaining: r"^破解剩余时间",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "BREACH TIME REMAINING",
            I18nPage.Include: {
                I18nPage.Fight_BreachTimeRemaining.BreachTimeRemaining: flex_ws(
                    r"^BREACH TIME REMAINING"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Notice -----------

    I18nPage.UI_ESC_LeaveInstance.PAGE: {
        Language.ZH: {
            I18nPage.Name: "UI-离开副本",
            I18nPage.Include: {
                I18nPage.UI_ESC_LeaveInstance.Note: r"^提示$",
                I18nPage.UI_ESC_LeaveInstance.Confirm: r"^确认$",
                I18nPage.UI_ESC_LeaveInstance.Restart: r"^重新挑战$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "UI-LeaveInstance",
            I18nPage.Include: {
                I18nPage.UI_ESC_LeaveInstance.Note: r"^Note$",
                I18nPage.UI_ESC_LeaveInstance.Confirm: r"^Confirm$",
                I18nPage.UI_ESC_LeaveInstance.Restart: r"^Restart$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_LeaveInstance_001_EN.png"],
        },
    },

    I18nPage.Notice_LeaveInstance.PAGE: {
        Language.ZH: {
            I18nPage.Name: "Notice-离开副本",  # 梦魇赫卡忒、凝素领域
            I18nPage.Include: {
                I18nPage.Notice_LeaveInstance.Notice: r"^提示$",
                I18nPage.Notice_LeaveInstance.Confirm: r"^确认$",
                I18nPage.Notice_LeaveInstance.Cancel: r"^取消$",
                I18nPage.Notice_LeaveInstance.Leave: r"离开",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Notice-LeaveInstance",
            I18nPage.Include: {
                I18nPage.Notice_LeaveInstance.Notice: r"^Notice$",
                I18nPage.Notice_LeaveInstance.Confirm: r"^Confirm$",
                I18nPage.Notice_LeaveInstance.Cancel: r"^(Cancel|Restart)$",
                I18nPage.Notice_LeaveInstance.Leave: r"Leave",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_ForgeryChallengeComplete.PAGE: {
        Language.ZH: {
            I18nPage.Name: "Notice-副本-挑战完成/失败",
            I18nPage.Include: {
                I18nPage.Notice_ForgeryChallengeComplete.ChallengeComplete: r"^(挑战完成|挑战成功|挑战失败)$",
                I18nPage.Notice_ForgeryChallengeComplete.Exit: r"^退出副本$",
                I18nPage.Notice_ForgeryChallengeComplete.Restart: r"^重新挑战$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Notice-Instance-ChallengeComplete/Failed",
            I18nPage.Include: {
                I18nPage.Notice_ForgeryChallengeComplete.ChallengeComplete: flex_ws(r"^(Challenge Complete|Challenge Failed)$"),
                I18nPage.Notice_ForgeryChallengeComplete.Exit: r"^Exit$",
                I18nPage.Notice_ForgeryChallengeComplete.Restart: r"^Restart$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_TacetSuppression.PAGE: {
        Language.ZH: {
            I18nPage.Name: "Notice-无音区-挑战成功",
            I18nPage.Include: {
                I18nPage.Notice_TacetSuppression.ChallengeComplete: r"^挑战成功$",
                I18nPage.Notice_TacetSuppression.Confirm: r"^确定$",
            },
            I18nPage.Exclude: {
                I18nPage.Notice_TacetSuppression.Exit: r"^退出副本$",
                I18nPage.Notice_TacetSuppression.Cancel: r"^取消$",
                I18nPage.Notice_TacetSuppression.Restart: r"^重新挑战$",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_LoseConsciousness.PAGE: {
        Language.ZH: {
            I18nPage.Name: "失去意识",
            I18nPage.Include: {
                I18nPage.Notice_LoseConsciousness.LoseConsciousness: r"失去意识",
                I18nPage.Notice_LoseConsciousness.Revive: r"复苏",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_SelectRevivalItem.PAGE: {
        Language.ZH: {
            I18nPage.Name: "选择复苏物品",
            I18nPage.Include: {
                I18nPage.Notice_SelectRevivalItem.SelectRevivalItem: r"选择复苏物品",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_Replenish_Waveplate.PAGE: {
        Language.ZH: {
            I18nPage.Name: "补充结晶波片",
            I18nPage.Include: {
                I18nPage.Notice_Replenish_Waveplate.ReplenishWaveplate: r"补充结晶波片",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_BlankArea.PAGE: {
        Language.ZH: {
            I18nPage.Name: "空白区域",
            I18nPage.Include: {
                I18nPage.Notice_BlankArea.BlankArea: r"空白区域",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Login -----------

    I18nPage.Login_ClickLink.PAGE: {
        Language.ZH: {
            I18nPage.Name: "点击连接",
            I18nPage.Include: {
                I18nPage.Login_ClickLink.ClickLink: r"^点击连接$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Tap to land in Solaris-3",
            I18nPage.Include: {
                # I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"Tap to land in Solaris-3"),
                I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"^Tap to land in Solaris*"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Login_AccountLogin.PAGE: {
        Language.ZH: {
            I18nPage.Name: "账户登录",
            I18nPage.Include: {
                I18nPage.Login_AccountLogin.Text: r"^(退出|公告|修复)$",
                I18nPage.Login_AccountLogin.Login: r"^登入$",
            },
            I18nPage.Exclude: {
                I18nPage.Login_AccountLogin.ClickLink: r"点击连接",
            },
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "AccountLogin",
            I18nPage.Include: {
                I18nPage.Login_AccountLogin.Text: r"^(Exit|Notice|Repair)$",
                I18nPage.Login_AccountLogin.Login: r"^Login$",
            },
            I18nPage.Exclude: {
                # I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"Tap to land in Solaris-3"),
                I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"^Tap to land in Solaris*"),
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Login_Disconnected.PAGE: {
        Language.ZH: {
            I18nPage.Name: "连接已断开",
            I18nPage.Include: {
                # 已与服务器断开连接，请尝试重新登录，如有疑问请联系客服
                I18nPage.Login_Disconnected.Disconnected: r"连接已断开",
                # I18nPage.Login_Disconnected.LoginTimeout: r"登录超时",
                I18nPage.Login_Disconnected.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- System Notice -----------

    I18nPage.SystemNotice_UpdateCompleteExit.PAGE: {
        Language.ZH: {
            I18nPage.Name: "更新完成，请重新启动游戏",
            I18nPage.Include: {
                I18nPage.SystemNotice_UpdateCompleteExit.UpdateComplete: r"更新完成.*请重新启动游戏",
                I18nPage.SystemNotice_UpdateCompleteExit.Exit: r"^退出$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.SystemNotice_UpdateCompleteConfirm.PAGE: {
        Language.ZH: {
            I18nPage.Name: "更新完成，游戏即将重启",
            I18nPage.Include: {
                I18nPage.SystemNotice_UpdateCompleteExit.UpdateComplete: RegexStr(
                    r"更新完成.*?游戏即将重启", raw=r"更新完成，游戏即将重启"),
                I18nPage.SystemNotice_UpdateCompleteConfirm.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.SystemNotice_Confirm_DriverVersion.PAGE: {
        Language.ZH: {
            I18nPage.Name: "检测到设备显卡驱动版本过旧",
            I18nPage.Include: {
                I18nPage.SystemNotice_Confirm_DriverVersion.DriverVersion: r"显卡驱动版本过旧",
                I18nPage.SystemNotice_Confirm_DriverVersion.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.SystemNotice_NetworkTimeout.PAGE: {
        Language.ZH: {
            I18nPage.Name: "系统提示-网络请求超时",
            I18nPage.Include: {
                I18nPage.SystemNotice_NetworkTimeout.SystemNotice: r"系统提示",
                I18nPage.SystemNotice_NetworkTimeout.NetworkTimeout: r"网络请求超时",
                I18nPage.SystemNotice_NetworkTimeout.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

}


# ------------- Echo Merge 声骸融合 --------------

class I18nPageEchoMerge(I18nPage):
    class DataBank:
        PAGE = "DataBank"
        DataBankInfo = "DataBankInfo"
        Rewards = "Rewards"

    # class DataBank_EchoGallery:
    #     PAGE = "DataBank_EchoGallery"
    #     EchoGallery = "EchoGallery"
    #
    # class DataBank_SonataGallery:
    #     PAGE = "DataBank_SonataGallery"
    #     SonataGallery = "SonataGallery"

    class DataMerge:
        PAGE = "DataMerge"
        DataMerge = "DataMerge"
        TargetedMerge = "TargetedMerge"
        StandardMerge = "StandardMerge"

    class StandardMerge_SelectAll:
        PAGE = "DataMerge_SelectAll"
        SelectAll = "SelectAll"
        DataMergeCount = "DataMergeCount"
        StandardMerge = "StandardMerge"

    class Notice_IncludesHighRarity:
        PAGE = "Notice_High_Rarity"
        Notice = "Notice"
        HighRarity = "HighRarity"
        DoNotShowAgain = "DoNotShowAgain"
        Confirm = "Confirm"

    class NewEcho:
        PAGE = "NewEcho"
        NewEcho = "NewEcho"

    # class DataBank_DataModify:
    #     PAGE = "DataBank_DataModify"
    #     DataModify = "DataModify"
    #
    # class DataBank_EchoManagement:
    #     PAGE = "DataBank_EchoManagement"
    #     EchoManagement = "EchoManagement"


I18N_PAGES_ECHO_MERGE = {
    I18nPage.Terminal.PAGE: {
        Language.ZH: {
            I18nPage.Name: "UI-终端",
            I18nPage.Include: {
                I18nPage.Terminal.Terminal: {
                    I18nPage.Text: r"^终端$",
                    I18nPage.Limit: AnchorBBox(
                        AnchorPoint(0, 0, Align.Top | Align.Left),
                        AnchorPoint(280, 90, Align.Top | Align.Left),
                    ).as_tuple(),
                },
                I18nPage.Terminal.Team: r"^编队$",
                I18nPage.Terminal.Events: r"^活动$",
                I18nPage.Terminal.DataBank: r"^数据坞$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001.png"],
        },
        Language.EN: {
            I18nPage.Name: "UI-Terminal",
            I18nPage.Include: {
                I18nPage.Terminal.Terminal: {
                    I18nPage.Text: r"^Terminal$",
                    I18nPage.Limit: AnchorBBox(
                        AnchorPoint(0, 0, Align.Top | Align.Left),
                        AnchorPoint(280, 90, Align.Top | Align.Left),
                    ).as_tuple(),
                },
                I18nPage.Terminal.Team: r"^Team$",
                I18nPage.Terminal.Events: r"^Events$",
                I18nPage.Terminal.DataBank: flex_ws(r"^Data Bank$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001_EN.png"],
        },
    },
    I18nPageEchoMerge.DataBank.PAGE: {
        Language.ZH: {
            I18nPage.Name: "数据坞",
            I18nPage.Include: {
                I18nPageEchoMerge.DataBank.DataBankInfo: r"^数据坞信息$",
                I18nPageEchoMerge.DataBank.Rewards: r"^奖励$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "DataBank",
            I18nPage.Include: {
                I18nPageEchoMerge.DataBank.DataBankInfo: flex_ws(r"^Data Bank Info$"),
                I18nPageEchoMerge.DataBank.Rewards: r"^Rewards$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },

    },
    I18nPageEchoMerge.DataMerge.PAGE: {
        Language.ZH: {
            I18nPage.Name: "数据坞-数据融合",
            I18nPage.Include: {
                I18nPageEchoMerge.DataMerge.TargetedMerge: r"定向融合$",
                I18nPageEchoMerge.DataMerge.StandardMerge: r"标准融合$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "DataBank-DataMerge",
            I18nPage.Include: {
                I18nPageEchoMerge.DataMerge.TargetedMerge: flex_ws(r"Targeted Merge$"),
                I18nPageEchoMerge.DataMerge.StandardMerge: flex_ws(r"Standard Merge$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },
    I18nPageEchoMerge.StandardMerge_SelectAll.PAGE: {
        Language.ZH: {
            I18nPage.Name: "标准融合-全选",
            I18nPage.Include: {
                I18nPageEchoMerge.StandardMerge_SelectAll.SelectAll: r"^全选",
                I18nPageEchoMerge.StandardMerge_SelectAll.StandardMerge: r"^标准融合$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "StandardMerge-SelectAll",
            I18nPage.Include: {
                I18nPageEchoMerge.StandardMerge_SelectAll.SelectAll: flex_ws(r"^Select All"),
                # I18nPageEchoMerge.StandardMerge_SelectAll.DataMergeCount: flex_ws(r"Data Merge Count"),
                I18nPageEchoMerge.StandardMerge_SelectAll.StandardMerge: flex_ws(r"^Standard Merge$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },
    I18nPageEchoMerge.Notice_IncludesHighRarity.PAGE: {
        Language.ZH: {
            I18nPage.Name: "提示-包含品质较高的声骸",
            I18nPage.Include: {
                I18nPageEchoMerge.Notice_IncludesHighRarity.Notice: r"^提示$",
                I18nPageEchoMerge.Notice_IncludesHighRarity.HighRarity: r"包含品质较高",
                I18nPageEchoMerge.Notice_IncludesHighRarity.DoNotShowAgain: r"本次登录不再提示",
                I18nPageEchoMerge.Notice_IncludesHighRarity.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Notice-IncludesHighRarity",
            I18nPage.Include: {
                I18nPageEchoMerge.Notice_IncludesHighRarity.Notice: flex_ws(r"^Notice$"),
                I18nPageEchoMerge.Notice_IncludesHighRarity.HighRarity: flex_ws(r"High Rarity"),
                I18nPageEchoMerge.Notice_IncludesHighRarity.DoNotShowAgain: flex_ws(r"Do not show again"),
                I18nPageEchoMerge.Notice_IncludesHighRarity.Confirm: flex_ws(r"^Confirm$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },
    I18nPageEchoMerge.NewEcho.PAGE: {
        Language.ZH: {
            I18nPage.Name: "获得声骸",
            I18nPage.Include: {
                I18nPageEchoMerge.NewEcho.NewEcho: r"获得声骸",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "NewEcho",
            I18nPage.Include: {
                I18nPageEchoMerge.NewEcho.NewEcho: flex_ws(r"New Echo"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

}


# ------------- Guidebook --------------

class I18nPageGuidebook(I18nPage):
    class Activity:
        pass

    class MaterialsSpots:
        PAGE = "MaterialsSpots"
        ForgeryChallenge = "ForgeryChallenge"
        SimulationChallenge = "SimulationChallenge"
        BossChallenge = "BossChallenge"
        TacetSuppression = "TacetSuppression"
        WeeklyChallenge = "WeeklyChallenge"
        NightmarePurification = "NightmarePurification"
        TacetDiscordNest = "TacetDiscordNest"

    class RecurringChallenges:
        pass

    class PathOfGrowth:
        pass

    class EnemyTracing:
        pass

    class Milestones:
        pass


I18N_PAGES_GUIDEBOOK = {
    I18nPageGuidebook.MaterialsSpots.PAGE: {
        Language.ZH: {
            I18nPage.Name: "素材获取",
            I18nPage.Include: {
                # 产出武器及技能材料
                I18nPageGuidebook.MaterialsSpots.ForgeryChallenge: r"^凝素领域$",
                # 产出经验材料
                I18nPageGuidebook.MaterialsSpots.SimulationChallenge: r"^模拟领域$",
                # 产出共鸣者突破材料
                I18nPageGuidebook.MaterialsSpots.BossChallenge: r"^讨伐强敌$",
                # 产出声骸材料
                I18nPageGuidebook.MaterialsSpots.TacetSuppression: r"^无音清剿$",
                # 产出高级技能材料
                I18nPageGuidebook.MaterialsSpots.WeeklyChallenge: r"^战歌重奏$",
                # 产出梦魇声骸
                I18nPageGuidebook.MaterialsSpots.NightmarePurification: r"^梦魇祓除$",
                # 产出声骸套件
                I18nPageGuidebook.MaterialsSpots.TacetDiscordNest: r"^残像聚落$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Language.EN: {
            I18nPage.Name: "Materials Spots",
            I18nPage.Include: {
                I18nPageGuidebook.MaterialsSpots.ForgeryChallenge: flex_ws(r"^Forgery Challenge$"),
                I18nPageGuidebook.MaterialsSpots.SimulationChallenge: flex_ws(r"^Simulation Challenge$"),
                I18nPageGuidebook.MaterialsSpots.BossChallenge: flex_ws(r"^Boss Challenge$"),
                I18nPageGuidebook.MaterialsSpots.TacetSuppression: flex_ws(r"^Tacet Suppression$"),
                I18nPageGuidebook.MaterialsSpots.WeeklyChallenge: flex_ws(r"^Weekly Challenge$"),
                I18nPageGuidebook.MaterialsSpots.NightmarePurification: flex_ws(r"^Nightmare Purification$"),
                I18nPageGuidebook.MaterialsSpots.TacetDiscordNest: flex_ws(r"^Tacet Discord Nest$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },

    },

}


class I18nView:
    Terminal = "Terminal"
    LuniteSubscriptionReward = "LuniteSubscriptionReward"
    ViewClaimRewards = "ViewClaimRewards"
    ViewFight = "ViewFight"
    Absorb = "Absorb"
    ViewChallengeComplete = "ViewChallengeComplete"
    ViewBreakFree = "ViewBreakFree"
    ViewLeaveInstance = "ViewLeaveInstance"
    ViewLeaveInstance2 = "ViewLeaveInstance2"
    ViewForgeryChallengeComplete = "ViewForgeryChallengeComplete"
    ViewTacetSuppressionComplete = "ViewTacetSuppressionComplete"
    ViewTacetSuppressionClaimRewards = "ViewTacetSuppressionClaimRewards"


class View:
    def __init__(self, *, name: str | None = None, child, assets: dict[Language, str] | None = None):
        self.name: str | None = name
        self.child = child
        self.assets = assets


class FeatureGroup(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"


class Feature:
    def __init__(
            self,
            key: str,
            *,
            roi: BBox | None = None,
            exclude: bool = False,
            group: str | None = None,
    ):
        """
        文本特征
        :param key: 文本标识key，表示这个词必须有
        :param roi: 文本位置
        :param exclude: 是否为反向词，为True表示这个词不能有
        :param group: 同组的为或关系，只要组里有一个满足就算对。后续可以直接用组key来拿到命中的文本key，不用逐个判断
        """
        self.key: str = key
        self.roi: BBox | None = roi
        self.exclude: bool = exclude
        self.group: str | None = group


I18N_PAGES_BOSS = {
    I18nView.Terminal: {
        Language.ZH: View(
            name="终端",
            child=[
                Feature(I18nText.Events),
                # Feature(I18nText.Birthday),
                Feature(I18nText.SOL3Phase),
                Feature(I18nText.UnionLevel),
                Feature(I18nText.UnionEXP),
            ],
        ),
        Language.EN: View(
            name="Terminal",
            child=[
                Feature(I18nText.Events),
                # Feature(I18nText.Birthday),
                Feature(I18nText.SOL3Phase),
                Feature(I18nText.UnionLevel),
                Feature(I18nText.UnionEXP),
            ],
        ),
    },

    I18nView.LuniteSubscriptionReward: {
        Language.ZH: View(
            name="每日月卡奖励",
            child=[
                Feature(I18nText.LuniteSubscriptionReward),
            ],
        ),
        Language.EN: View(
            name="Lunite Subscription reward",
            child=[
                Feature(I18nText.LuniteSubscriptionReward),
            ],
        ),
    },

    I18nView.ViewClaimRewards: {
        Language.ZH: View(
            name="领取奖励",
            child=[
                Feature(I18nText.ViewClaimRewards),
                Feature(I18nText.ViewClaimRewardsConfirm),
                Feature(I18nText.ViewClaimRewardsCancel),
            ],
        ),
    },

    I18nView.ViewFight: {
        Language.ZH: View(
            name="战斗画面",
            child=[
                Feature(I18nText.ViewFight),
                Feature(I18nText.Activity, exclude=True),
                Feature(I18nText.ActivityPts, exclude=True),
                Feature(I18nText.TacetFieldChallengeComplete, exclude=True),
                Feature(I18nText.TacetFieldNoticeChallengeComplete, exclude=True),
                Feature(I18nText.ForgeryChallengeComplete, exclude=True),
            ],
        ),
    },

    I18nView.Absorb: {
        Language.ZH: View(
            name="吸收",
            child=[
                Feature(I18nText.Absorb),
                Feature(I18nText.ClaimRewards, exclude=True),
            ],
        ),
        Language.EN: View(
            name="Absorb",
            child=[
                Feature(I18nText.Absorb),
                Feature(I18nText.ClaimRewards, exclude=True),
            ],
        ),
    },

    I18nView.ViewChallengeComplete: {
        Language.ZH: View(
            name="挑战成功",
            child=[
                Feature(I18nText.ViewChallengeComplete),
            ],
        ),
        Language.EN: View(
            name="Challenge Complete",
            child=[
                Feature(I18nText.ViewChallengeComplete),
            ],
        ),
    },

    I18nView.ViewBreakFree: {
        Language.ZH: View(
            name="交替点击进行挣脱",
            child=[
                Feature(I18nText.ViewBreakFree),
            ],
        ),
        Language.EN: View(
            name="Break Free",
            child=[
                Feature(I18nText.ViewBreakFree),
            ],
        ),
    },

    I18nView.ViewLeaveInstance: {
        Language.ZH: View(
            name="离开副本",
            child=[
                Feature(I18nText.ViewLeaveInstanceNote),
                Feature(I18nText.ViewLeaveInstanceConfirm),
                Feature(I18nText.ViewLeaveInstanceRestart),
            ],
        ),
        Language.EN: View(
            name="LeaveInstance",
            child=[
                Feature(I18nText.ViewLeaveInstanceNote),
                Feature(I18nText.ViewLeaveInstanceConfirm),
                Feature(I18nText.ViewLeaveInstanceRestart),
            ],
        ),
    },

    I18nView.ViewLeaveInstance2: {
        Language.ZH: View(
            name="离开副本2",
            child=[
                Feature(I18nText.ViewLeaveInstance2Notice),
                Feature(I18nText.ViewLeaveInstance2Confirm),
                Feature(I18nText.ViewLeaveInstance2Cancel, group=FeatureGroup.A),
                Feature(I18nText.ViewLeaveInstance2Restart, group=FeatureGroup.A),
                Feature(I18nText.ViewLeaveInstance2Leave),
            ],
        ),
        Language.EN: View(
            name="LeaveInstance2",
            child=[
                Feature(I18nText.ViewLeaveInstance2Notice),
                Feature(I18nText.ViewLeaveInstance2Confirm),
                Feature(I18nText.ViewLeaveInstance2Cancel, group=FeatureGroup.A),
                Feature(I18nText.ViewLeaveInstance2Restart, group=FeatureGroup.A),
                Feature(I18nText.ViewLeaveInstance2Leave),
            ],
        ),
    },

    I18nView.ViewForgeryChallengeComplete: {
        Language.ZH: View(
            name="凝素领域-挑战成功/失败",
            child=[
                Feature(I18nText.ViewChallengeComplete, group=FeatureGroup.A),
                Feature(I18nText.ViewChallengeFailed, group=FeatureGroup.A),
                Feature(I18nText.ViewForgeryChallengeExit),
                Feature(I18nText.ViewForgeryChallengeRestart),
            ],
        ),
        Language.EN: View(
            name="ForgeryChallenge-Complete/Failed",
            child=[
                Feature(I18nText.ViewChallengeComplete, group=FeatureGroup.A),
                Feature(I18nText.ViewChallengeFailed, group=FeatureGroup.A),
                Feature(I18nText.ViewForgeryChallengeExit),
                Feature(I18nText.ViewForgeryChallengeRestart),
            ],
        ),
    },

    I18nView.ViewTacetSuppressionComplete: {
        Language.ZH: View(
            name="无音清剿-挑战成功",
            child=[
                Feature(I18nText.ViewTacetSuppressionChallengeComplete),
                Feature(I18nText.ViewTacetSuppressionConfirm),
                Feature(I18nText.ViewTacetSuppressionExit, exclude=True),
                Feature(I18nText.ViewTacetSuppressionCancel, exclude=True),
                Feature(I18nText.ViewTacetSuppressionRestart, exclude=True),
            ],
        ),
        Language.EN: View(
            name="TacetSuppression-Complete",
            child=[
                Feature(I18nText.ViewTacetSuppressionChallengeComplete),
                Feature(I18nText.ViewTacetSuppressionConfirm),
                Feature(I18nText.ViewTacetSuppressionExit, exclude=True),
                Feature(I18nText.ViewTacetSuppressionCancel, exclude=True),
                Feature(I18nText.ViewTacetSuppressionRestart, exclude=True),
            ],
        ),
    },

    I18nView.ViewTacetSuppressionClaimRewards: {
        Language.ZH: View(
            name="无音清剿-领取奖励",
            child=[
                Feature(I18nText.ViewTacetSuppressionClaimRewards),
                Feature(I18nText.ViewTacetSuppressionClaim),
                Feature(I18nText.ViewTacetSuppressionClaimX2),
            ],
        ),
        Language.EN: View(
            name="TacetSuppression-ClaimRewards",
            child=[
                Feature(I18nText.ViewTacetSuppressionClaimRewards),
                Feature(I18nText.ViewTacetSuppressionClaim),
                Feature(I18nText.ViewTacetSuppressionClaimX2),
            ],
        ),
    },








}


class I18nTr:

    def __init__(self, lang: Language):
        self._lang = lang

    def __call__(self, text_key: str | list[str], lang: str | None = None):
        if text_key is None:
            return None
        if isinstance(text_key, str):
            return self.t(text_key, lang)
        return [self.t(key, lang) for key in text_key]

    def t(self, text_key: str, lang: str | None = None):
        if text_key is None:
            return None
        lang_map = I18N_TEXT.get(text_key)
        if not lang_map:
            return None
        return lang_map.get(lang if lang is not None else self._lang)
