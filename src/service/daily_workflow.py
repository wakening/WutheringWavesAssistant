import logging
import random
import re
import time
from typing import Optional

from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import Morph
from src.core.combat.combat_system import CombatSystem
from src.core.dungeon import Dungeon
from src.core.enemy import Enemy
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, Point
from src.core.i18n import I18nText, Language, I18nTr
from src.core.message import MsgType, MsgTaskStatus, MsgSource
from src.core.movement import Run, Walk
from src.core.pages import UIOp, GlobalPage
from src.core.resonator import Resonator, TeamMember
from src.core.resource import Icon, Resource
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup, LatchTaskFSM
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import (
    absorb_around_variant_blind, bbox_terminal_content, bbox_guidebook_content, move_and_scan_dialogue,
    match_remaining_attempts, linear_spacing, query_waveplate_guidebook, query_waveplate_claim_rewards,
    object_detection, bbox_hp_bar, bbox_guidebook_item, search_icon_guidebook, bbox_dialogue,
    bbox_guidebook_title, AsyncPickup, RoiEx, Slider,
)
from src.util import img_util, file_util
from src.util.img_sift_util import SIFTFeatureMatcher
from src.util.img_tile_util import TileGrid

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        ### ------- Guidebook MaterialCollection ForgeryChallenge -------
        self.wingfallChasmFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.WingfallChasm)
        self.silentChasmFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.SilentChasm)
        self.splitChasmFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.SplitChasm)
        self.erodedChasmFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.ErodedChasm)
        self.ashenChasmFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.AshenChasm)
        self.fallenSanctumFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.FallenSanctum)
        self.lessonInSunsetFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.LessonInSunset)
        self.strickenSanctumFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.StrickenSanctum)
        self.lessonInVoidFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.LessonInVoid)
        self.lessonInEmbersFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.LessonInEmbers)
        self.gardenOfSalvationFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.GardenOfSalvation)
        self.abyssOfInitiationFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.AbyssOfInitiation)
        self.gardenOfAdorationFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.GardenOfAdoration)
        self.abyssOfSacrificeFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.AbyssOfSacrifice)
        self.abyssOfConfessionFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.AbyssOfConfession)
        self.flamingRemnantsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.FlamingRemnants)
        self.mistyForestFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.MistyForest)
        self.erodedRuinsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.ErodedRuins)
        self.moonlitGrovesFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.MoonlitGroves)
        self.marigoldWoodsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.MarigoldWoods)

        ### ------- Guidebook MaterialCollection SimulationChallenge -------

        ### ------- Guidebook MaterialCollection BossChallenge -------
        self.enemyCalamityEffigyFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyCalamityEffigy)
        self.enemyMyriadSnareRustfireChassisFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyMyriadSnareRustfireChassis)
        self.enemyNightmareAdamSmasherFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyNightmareAdamSmasher)
        self.enemyNamelessExplorerFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyNamelessExplorer)
        self.enemyHyvatiaFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyHyvatia)
        self.enemyReactorHuskFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyReactorHusk)
        self.enemyLadyOfTheSeaFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyLadyOfTheSea)
        self.enemyTheFalseSovereignFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyTheFalseSovereign)
        self.enemyFenricoFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyFenrico)
        self.enemyLionessOfGloryFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyLionessOfGlory)
        self.enemyDragonOfDirgeFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyDragonOfDirge)
        self.enemyLoreleiFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyLorelei)
        self.enemySentryConstructFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemySentryConstruct)
        self.enemyFallacyOfNoReturnFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyFallacyOfNoReturn)
        self.enemyCrownlessFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyCrownless)
        self.enemyFeilianBeringalFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyFeilianBeringal)
        self.enemyTempestMephisFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyTempestMephis)
        self.enemyThunderingMephisFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyThunderingMephis)
        self.enemyMourningAixFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyMourningAix)
        self.enemyMechAbominationFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyMechAbomination)
        self.enemyImpermanenceHeronFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyImpermanenceHeron)
        self.enemyInfernoRiderFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyInfernoRider)
        self.enemyLampylumenMyriadFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EnemyLampylumenMyriad)

        ### ------- Guidebook MaterialCollection TacetSuppression -------
        self.tacetFieldHeartOfStillnessFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldHeartOfStillness)
        self.tacetFieldHeartOfFlamesFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldHeartOfFlames)
        self.westernFangPeaksTacetFieldFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.WesternFangPeaksTacetField)
        self.easternXuanPeaksTacetFieldFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.EasternXuanPeaksTacetField)
        self.tacetFieldSolisiaLandingFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldSolisiaLanding)
        self.tacetFieldFrostlandsTransitPortFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldFrostlandsTransitPort)
        self.tacetFieldMountGjallarFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldMountGjallar)
        self.tacetFieldMawburrowDesertFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldMawburrowDesert)
        self.tacetFieldStagnantRunFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldStagnantRun)
        self.tacetFieldMournfellCanyonFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldMournfellCanyon)
        self.tacetFieldBeohrWatersFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldBeohrWaters)
        self.tacetFieldRiccioliIslandsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldRiccioliIslands)
        self.tacetFieldFagaceaePeninsulaFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldFagaceaePeninsula)
        self.tacetFieldPenitentsEndFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldPenitentsEnd)
        self.tacetFieldCentralPlainsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldCentralPlains)
        self.tacetFieldDesorockHighlandIFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldDesorockHighlandI)
        self.tacetFieldTigersMawFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldTigersMaw)
        self.tacetFieldWhiningAixsMireFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldWhiningAixsMire)
        self.tacetFieldPortCityOfGuixuFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldPortCityOfGuixu)
        self.tacetFieldDesorockHighlandIIFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldDesorockHighlandII)
        self.tacetFieldDimForestFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TacetFieldDimForest)

        ### ------- Guidebook MaterialCollection WeeklyChallenge -------
        self.ordinanceOfTheInevitableFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.OrdinanceOfTheInevitable)
        self.courtOfShackledSoulsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.CourtOfShackledSouls)
        self.seedOfIllusoryOriginFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.SeedOfIllusoryOrigin)
        self.gateOfTheLostStarFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.GateOfTheLostStar)
        self.cinderniteApocalypseFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.CinderniteApocalypse)
        self.theWheelOfBrokenFateFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TheWheelOfBrokenFate)
        self.beyondTheCrimsonCurtainFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.BeyondTheCrimsonCurtain)
        self.theFatedConfrontationFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.TheFatedConfrontation)
        self.statueOfTheCrownlessFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.StatueOfTheCrownless)
        self.chaoticJunctureFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.ChaoticJuncture)
        self.bellOfArchaicChantsFSM: LatchTaskFSM = LatchTaskFSM(name=I18nText.BellOfArchaicChants)

        ### ------- Guidebook MaterialCollection NightmarePurification -------

        ### ------- Guidebook MaterialCollection TacetDiscordNest -------
        self.simulacrumNexusTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.SimulacrumNexusTacetDiscordNest)
        self.southernYuanHillsTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.SouthernYuanHillsTacetDiscordNest)
        self.starblindCrashsiteTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.StarblindCrashsiteTacetDiscordNest)
        self.rebirthUplandsTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.RebirthUplandsTacetDiscordNest)
        self.stagnantRunTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.StagnantRunTacetDiscordNest)

        ## ------- Guidebook Activity -------
        self.activityDailyFSM: TaskFSM = TaskFSM(name=I18nText.ActivityDaily)
        self.activityWeeklyFSM: TaskFSM = TaskFSM(name=I18nText.ActivityWeekly)

        ## ------- Guidebook MaterialCollection -------
        self.forgeryChallengeFSM: TaskFSMGroup = TaskFSMGroup(
            self.wingfallChasmFSM,
            self.silentChasmFSM,
            self.splitChasmFSM,
            self.erodedChasmFSM,
            self.ashenChasmFSM,
            self.fallenSanctumFSM,
            self.lessonInSunsetFSM,
            self.strickenSanctumFSM,
            self.lessonInVoidFSM,
            self.lessonInEmbersFSM,
            self.gardenOfSalvationFSM,
            self.abyssOfInitiationFSM,
            self.gardenOfAdorationFSM,
            self.abyssOfSacrificeFSM,
            self.abyssOfConfessionFSM,
            self.flamingRemnantsFSM,
            self.mistyForestFSM,
            self.erodedRuinsFSM,
            self.moonlitGrovesFSM,
            self.marigoldWoodsFSM,
            name=I18nText.ForgeryChallenge
        )
        self.simulationChallengeFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.SimulationChallenge)

        self.bossChallengeFSM: TaskFSMGroup = TaskFSMGroup(
            self.enemyCalamityEffigyFSM,
            self.enemyMyriadSnareRustfireChassisFSM,
            self.enemyNightmareAdamSmasherFSM,
            self.enemyNamelessExplorerFSM,
            self.enemyHyvatiaFSM,
            self.enemyReactorHuskFSM,
            self.enemyLadyOfTheSeaFSM,
            self.enemyTheFalseSovereignFSM,
            self.enemyFenricoFSM,
            self.enemyLionessOfGloryFSM,
            self.enemyDragonOfDirgeFSM,
            self.enemyLoreleiFSM,
            self.enemySentryConstructFSM,
            self.enemyFallacyOfNoReturnFSM,
            self.enemyCrownlessFSM,
            self.enemyFeilianBeringalFSM,
            self.enemyTempestMephisFSM,
            self.enemyThunderingMephisFSM,
            self.enemyMourningAixFSM,
            self.enemyMechAbominationFSM,
            self.enemyImpermanenceHeronFSM,
            self.enemyInfernoRiderFSM,
            self.enemyLampylumenMyriadFSM,
            name=I18nText.BossChallenge
        )

        self.tacetSuppressionFSM: TaskFSMGroup = TaskFSMGroup(
            self.tacetFieldHeartOfStillnessFSM,
            self.tacetFieldHeartOfFlamesFSM,
            self.westernFangPeaksTacetFieldFSM,
            self.easternXuanPeaksTacetFieldFSM,
            self.tacetFieldSolisiaLandingFSM,
            self.tacetFieldFrostlandsTransitPortFSM,
            self.tacetFieldMountGjallarFSM,
            self.tacetFieldMawburrowDesertFSM,
            self.tacetFieldStagnantRunFSM,
            self.tacetFieldMournfellCanyonFSM,
            self.tacetFieldBeohrWatersFSM,
            self.tacetFieldRiccioliIslandsFSM,
            self.tacetFieldFagaceaePeninsulaFSM,
            self.tacetFieldPenitentsEndFSM,
            self.tacetFieldCentralPlainsFSM,
            self.tacetFieldDesorockHighlandIFSM,
            self.tacetFieldTigersMawFSM,
            self.tacetFieldWhiningAixsMireFSM,
            self.tacetFieldPortCityOfGuixuFSM,
            self.tacetFieldDesorockHighlandIIFSM,
            self.tacetFieldDimForestFSM,
            name=I18nText.TacetSuppression
        )
        self.weeklyChallengeFSM: TaskFSMGroup = TaskFSMGroup(
            self.ordinanceOfTheInevitableFSM,
            self.courtOfShackledSoulsFSM,
            self.seedOfIllusoryOriginFSM,
            self.gateOfTheLostStarFSM,
            self.cinderniteApocalypseFSM,
            self.theWheelOfBrokenFateFSM,
            self.beyondTheCrimsonCurtainFSM,
            self.theFatedConfrontationFSM,
            self.statueOfTheCrownlessFSM,
            self.chaoticJunctureFSM,
            self.bellOfArchaicChantsFSM,
            name=I18nText.WeeklyChallenge
        )
        self.nightmarePurificationFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.NightmarePurification)
        self.tacetDiscordNestFSM: TaskFSMGroup = TaskFSMGroup(
            self.simulacrumNexusTacetDiscordNestFSM,
            self.southernYuanHillsTacetDiscordNestFSM,
            self.starblindCrashsiteTacetDiscordNestFSM,
            self.rebirthUplandsTacetDiscordNestFSM,
            self.stagnantRunTacetDiscordNestFSM,
            name=I18nText.TacetDiscordNest
        )

        # ------- Guidebook -------
        self.activityFSM: TaskFSMGroup = TaskFSMGroup(
            self.activityDailyFSM,
            self.activityWeeklyFSM,
            name=I18nText.Activity
        )
        self.materialCollectionFSM: TaskFSMGroup = TaskFSMGroup(
            self.forgeryChallengeFSM,
            self.simulationChallengeFSM,
            self.bossChallengeFSM,
            self.tacetSuppressionFSM,
            self.weeklyChallengeFSM,
            self.nightmarePurificationFSM,
            self.tacetDiscordNestFSM,
            name=I18nText.MaterialCollection
        )
        self.recurringChallengesFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.RecurringChallenges)
        self.pathOfGrowthFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.PathOfGrowth)
        self.enemyTracingFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.EnemyTracing)
        self.milestonesFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.Milestones)

        # ------- Root -------
        self.guidebookFSM: TaskFSMGroup = TaskFSMGroup(
            self.activityFSM,
            self.materialCollectionFSM,
            self.recurringChallengesFSM,
            self.pathOfGrowthFSM,
            self.enemyTracingFSM,
            self.milestonesFSM,
            name=I18nText.Guidebook
        )
        self.teamFSM: TaskFSM = TaskFSM(name=I18nText.Team)
        self.mailFSM: TaskFSM = TaskFSM(name=I18nText.Mail)
        self.pioneerPodcastFSM: TaskFSM = TaskFSM(name=I18nText.PioneerPodcast)

        self.rootFSM: TaskFSMGroup = TaskFSMGroup(
            self.guidebookFSM,
            self.teamFSM,
            self.mailFSM,
            self.pioneerPodcastFSM,
            name="Root"
        )

        # ---------------------------------------------------------------

        # ------- DoubleDrop -------
        self.doubleDropForgeryChallengeFSM: TaskFSM = TaskFSM(name="DoubleDropForgeryChallenge")
        self.doubleDropSimulationChallengeFSM: TaskFSM = TaskFSM(name="DoubleDropSimulationChallenge")
        self.doubleDropTacetSuppressionFSM: TaskFSM = TaskFSM(name="DoubleDropTacetSuppression")

        # runtime
        self.pattern = re.compile(r"[·_-]")

        # 战斗
        self.members = ["unknown", None, None]
        self.combat_system: CombatSystem = None


class NodeName:
    globalDispatcher = "globalDispatcher"
    rootDispatcher = "rootDispatcher"
    endNode = "endNode"

    # rootDispatcher
    doTeam = "doTeam"
    doGuidebook = "doGuidebook"
    doMail = "doMail"
    doPioneerPodcast = "doPioneerPodcast"

    # doTeam
    doTravelToResonanceNexus = "doTravelToResonanceNexus"

    # doGuidebook
    doActivity = "doActivity"
    doMaterialCollection = "doMaterialCollection"
    doRecurringChallenges = "doRecurringChallenges"
    doPathOfGrowth = "doPathOfGrowth"
    doEnemyTracing = "doEnemyTracing"
    doMilestones = "doMilestones"

    # doActivity
    doActivityDaily = "doActivityDaily"
    doActivityWeekly = "doActivityWeekly"
    doPhantasmaDreamlandRhapsody = "doPhantasmaDreamlandRhapsody"

    # doMaterialCollection
    doForgeryChallenge = "doForgeryChallenge"
    doSimulationChallenge = "doSimulationChallenge"
    doBossChallenge = "doBossChallenge"
    doTacetSuppression = "doTacetSuppression"
    doWeeklyChallenge = "doWeeklyChallenge"
    doNightmarePurification = "doNightmarePurification"
    doTacetDiscordNest = "doTacetDiscordNest"


@node(NodeName.endNode)
def endNode(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.rootFSM.is_finished:
        ctx.runtime.taskFSM.complete()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
        ctx.ipc.event_queue.put({
            "task": {"DailyTask": "finished"}
        }, block=True)
    else:
        ctx.runtime.taskFSM.fail()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.FAILED)
        ctx.ipc.event_queue.put({
            "task": {"DailyTask": "failed"}
        }, block=True)
    time.sleep(0.1)
    return True


@node(NodeName.globalDispatcher)
def globalDispatcher(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """检查是否在有效页面（如：终端），不在则esc尝试离开（副本等）"""
    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    page = GlobalPage(ctx)

    # 已在终端页
    if page.isTerminal(ui=ui):
        return I18nText.Terminal

    # 在全局预设中找出离开函数，尝试回到主页
    if page.action(ui=ui):
        ui.sleep(0.5)
        return None

    logger.info("Transferring")

    num = max(1, min(1.4, random.gauss(1.2, 0.08)))
    # 兜底规则，esc
    ui.esc().sleep(num)
    return None


@node(NodeName.rootDispatcher)
def rootDispatcher(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    if local.teamFSM.is_active:
        return I18nText.Team
    if local.guidebookFSM.is_active:
        return I18nText.Guidebook
    if local.mailFSM.is_active:
        return I18nText.Mail
    if local.pioneerPodcastFSM.is_active:
        return I18nText.TerminalPioneerPodcast

    if local.rootFSM.is_active:
        logger.warning("Unexpected root state")
    return None


@node(NodeName.doTravelToResonanceNexus)
def doTravelToResonanceNexus(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    """去往信标，用于复活队友、脱战等"""
    ui = UIOp(ctx)
    ui.snapshot()

    # 从终端进入地图
    if GlobalPage(ctx).isTerminal(ui=ui):
        if not ui.click_text(ctx.tr(I18nText.Map), RoiEx(ctx).terminal_content, delay=0.2, times=2, interval=0.3):
            ui.click_point(AnchorPoint(1197, 350, Align.Right | Align.Middle))
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.Map), delay=0.3, times=2, interval=0.3)):
                ui.esc().sleep(1)
                return False
    else:
        # 大世界进入地图
        ctx.control_service.map()

    # 等待切换地图
    if not ui.sleep(0.5).wait(10, 0.4).until(
            lambda: ui.snapshot().search(ctx.tr(I18nText.SwitchMap))):
        return False
    # 放大地图
    ui.click_point(AnchorPoint(1207, 241, Align.Right | Align.Middle), delay=0.8, times=2, interval=0.3)
    # 点击切换地图
    ui.click_text(ctx.tr(I18nText.SwitchMap), delay=0.2)

    # 选择瑝珑-今州
    regions_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(600, 0, Align.Right | Align.Top), AnchorPoint(925, 720, Align.Right | Align.Bottom)))
    for i in range(3):
        if i == 2:
            return False
        if not ui.sleep(0.3).wait().until(
                lambda: ui.snapshot().search(
                    ctx.tr([I18nText.Huanglong, I18nText.Mengzhou, I18nText.Jinzhou]), regions_roi)):
            logger.warning(f"Text not found: {ctx.tr(I18nText.Huanglong).raw}")
            return False
        ui.sleep(0.4).snapshot()  # 修复文字未显示完全就识别导致少字，等动画结束，重新识别
        if ui.search(ctx.tr([I18nText.Mengzhou, I18nText.Jinzhou])):
            ui.click_text(ctx.tr(I18nText.Mengzhou), regions_roi, delay=0.4, times=2, interval=0.2)
            ui.click_text(ctx.tr(I18nText.Jinzhou), regions_roi, delay=0.1, times=2, interval=0.2)
            break
        elif ui.click_text(ctx.tr(I18nText.Huanglong), regions_roi, delay=0.4):
            ui.sleep(0.35)
            continue
        return False

    # 选择今州城
    regions_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(915, 0, Align.Right | Align.Top), AnchorPoint(1280, 720, Align.Right | Align.Bottom)))
    if not ui.sleep(0.5).wait().until(
            lambda: ui.snapshot().click_text(
                ctx.tr(I18nText.JinzhouCity), regions_roi, delay=0.4, times=2, interval=0.2)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.JinzhouCity).raw}")
        return False

    # 点击今州城传送点
    tmpl_name = "8_0_-1.png"
    tmpl_img = img_util.read_img(Resource.Map.Huanglong.Jinzhou / "8_0_-1.png")
    scene_img = ui.sleep(0.8).grap()
    matcher = SIFTFeatureMatcher()
    feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
    result = matcher.match(scene_img, feature_data)
    if result is None:
        logger.warning("Feature match failed")
        return False
    # (466, 309)
    point = Point(433, 187)
    scene_point = matcher.feature_to_scene(result, (float(point.x), float(point.y)))
    logger.debug(f"模板点 {point} 映射到场景坐标: ({scene_point[0]:.1f}, {scene_point[1]:.1f})")
    ui.click(int(scene_point[0]), int(scene_point[1]))
    if not ui.sleep(0.5).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.FastTravel), delay=0.3, times=2, interval=0.3)):
        return False

    ui.sleep(2).wait_back_home()
    ui.sleep(1.0)
    return True


@node(NodeName.doTeam)
def doTeam(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool | None:
    """获取编队角色名"""
    if local.teamFSM.is_terminal:
        return True
    if local.teamFSM.status == TaskStatus.PENDING:
        local.teamFSM.start()

    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    # 终端
    if not GlobalPage(ctx).isTerminal(ui=ui):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Terminal).raw}")
        ui.esc().sleep(1)
        return None

    # 点击进入编队
    if not ui.click_text(ctx.tr(I18nText.Team), RoiEx(ctx).terminal_content, pk=PointKind.NEAR, delay=0.3):  # 不可多点
        logger.warning(f"Text not found: {ctx.tr(I18nText.Team).raw}")
        return False

    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(700, 625, Align.Right | Align.Bottom),
        AnchorPoint(1280, 720, Align.Right | Align.Bottom)
    ))
    if ui.sleep(0.8).wait().until(
            lambda: ui.snapshot().search(ctx.tr(I18nText.QuickSetup), roi) or ui.search(ctx.tr(
                [I18nText.CannotPerformThisActionDuringBattle, I18nText.CannotAdjustTheTeamLineupInTheCurrentState]))):
        if not ui.search(ctx.tr(I18nText.QuickSetup), roi):
            logger.info(f"Team locked")
            return False

    # 切换2D
    img = ui.sleep(0.4).grap()
    c3d = ColorRule().points(AnchorPoint(1081, 43, Align.Top | Align.Right)).colors(Color.bgr(195, 195, 195))
    c2d = ColorRule().points(AnchorPoint(1158, 43, Align.Top | Align.Right)).colors(Color.bgr(10, 8, 6))
    if c3d.match(img, ctx.scaler) and c2d.match(img, ctx.scaler):
        ui.click_point(AnchorPoint(1146, 43, Align.Top | Align.Right))
        if not ui.sleep(0.4).wait().until(lambda: ui.snapshot().search(ctx.tr(I18nText.QuickSetup), roi)):
            logger.info(f"Team locked")
            return False

    ui.sleep(0.3).snapshot()

    # 检查失去意识
    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top),
        AnchorPoint(1280, 450, Align.Right | Align.Middle)
    ))
    if ui.search(ctx.tr(I18nText.ResonatorDowned), roi):
        logger.info(f"resonator downed")
        if ui.esc().sleep(0.5).wait_back_home():
            ui.sleep(0.3)
        return False

    # 识别编队角色
    member_keys = TeamMember.get_members_by_text(ui)
    members = [local.pattern.sub("", ctx.tr(key).raw) if key else key for key in member_keys]
    logger.info(f"Team: {members}")
    if not members[0]:
        ui.esc().sleep(2)
        return None

    local.member_keys = member_keys
    local.members = members

    local.teamFSM.complete()
    ui.esc().sleep(1)
    return True


@node(NodeName.doGuidebook)
def doGuidebook(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """索拉指南"""
    if local.guidebookFSM.is_terminal:
        return None

    ui = UIOp(ctx)

    # 终端
    if GlobalPage(ctx).isTerminal(ui=ui.snapshot()):
        # 点击进入索拉指南
        if not ui.click_text(ctx.tr(I18nText.Guidebook), bbox_terminal_content(ctx),
                             pk=PointKind.NEAR, delay=0.2, times=2, interval=0.2):
            logger.warning(f"Text not found: {ctx.tr(I18nText.Guidebook).raw}")
            return None
    else:
        ctx.control_service.guidebook()

    # 左侧图标坐标
    activitySidebar = AnchorPoint(50, 128, Align.Top | Align.Left)
    # materialCollectionSidebar = [
    #     AnchorPoint(50, 218, Align.Top | Align.Left),
    #     AnchorPoint(50, 308, Align.Top | Align.Left),
    # ]
    # recurringChallengesSidebar = AnchorPoint(50, 308, Align.Top | Align.Left)
    # pathOfGrowthSidebar = AnchorPoint(50, 396, Align.Top | Align.Left)
    # enemyTracingSidebar = [
    #     AnchorPoint(50, 487, Align.Top | Align.Left),
    #     AnchorPoint(50, 578, Align.Top | Align.Left),
    #     AnchorPoint(50, 396, Align.Top | Align.Left),
    # ]
    # milestonesSidebar = AnchorPoint(50, 578, Align.Top | Align.Left)

    # 进入索拉指南后，默认是 活跃度 或 素材获取页
    activity = ctx.tr(I18nText.Activity)
    materialCollection = ctx.tr(I18nText.MaterialCollection)
    recurringChallenges = ctx.tr(I18nText.RecurringChallenges)
    pathOfGrowth = ctx.tr(I18nText.PathOfGrowth)
    enemyTracing = ctx.tr(I18nText.EnemyTracing)
    milestones = ctx.tr(I18nText.Milestones)

    titles = [activity, materialCollection, recurringChallenges, pathOfGrowth, enemyTracing, milestones]
    roiex = RoiEx(ctx)

    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(titles, roiex.guidebook_title)):
        logger.warning(f"Page not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    def _click_icon(_icon, _keyword):
        icon_point = None
        for _ in range(2):
            if icon_point := search_icon_guidebook(ctx, icon=_icon):
                break
            ui.sleep(0.3)
        if not icon_point:
            logger.warning(f"{_keyword.raw} icon not found")
            return False
        # 点击侧边栏图标
        ui.click_point(icon_point, times=2, interval=0.3)
        if not ui.sleep(0.2).wait().until(lambda: ui.snapshot().search(_keyword, roiex.guidebook_title)):
            return False
        return True

    # 根据任务的开启状态分发任务
    if local.materialCollectionFSM.is_active:
        if not ui.search(materialCollection, roiex.guidebook_title) and not _click_icon(
                Icon.materialCollection(), materialCollection):
            return None
        ui.sleep(0.3)
        return I18nText.MaterialCollection
    if local.recurringChallengesFSM.is_active:
        # 周期挑战
        return I18nText.RecurringChallenges
    if local.pathOfGrowthFSM.is_active:
        return I18nText.PathOfGrowth
    if local.enemyTracingFSM.is_active:
        return I18nText.EnemyTracing
    if local.milestonesFSM.is_active:
        return I18nText.Milestones
    if local.activityFSM.is_active:
        # 活跃行迹
        tab_text = ctx.tr([I18nText.ActivityDaily, I18nText.ActivityWeekly])
        if not ui.search(activity, roiex.guidebook_title) or not ui.search(tab_text):
            ui.click_point(activitySidebar, times=2, interval=0.3)
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().search(activity, roiex.guidebook_title) and ui.search(tab_text)):
                return None
        ui.sleep(0.3)
        return I18nText.Activity

    return None


@node(NodeName.doActivity)
def doActivity(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """活跃行迹"""
    if local.activityDailyFSM.is_active:
        return I18nText.ActivityDaily
    if local.activityWeeklyFSM.is_active:
        return I18nText.ActivityWeekly
    return None


@node(NodeName.doActivityDaily)
def doActivityDaily(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    """活跃度"""
    if local.activityDailyFSM.is_terminal:
        return True
    in_progress = local.activityDailyFSM.status == TaskStatus.IN_PROGRESS
    if local.activityDailyFSM.status == TaskStatus.PENDING:
        local.activityDailyFSM.start()

    ui = UIOp(ctx)
    ui.snapshot()

    def _fail_return():
        # ui.esc().sleep(1)
        if in_progress:
            local.activityDailyFSM.fail()
            return True
        return False

    # 校验是否在活跃度页面
    if not ui.search(ctx.tr(I18nText.Activity), bbox_guidebook_title(ctx)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Activity).raw}")
        return _fail_return()

    # 上方活跃度、周度游历标签文字
    roi_tab = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Top | Align.Left), AnchorPoint(610, 130, Align.Top | Align.Left)))
    # 左下角活跃度、游历值文字
    roi_bottom_activity_pts = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 575, Align.Bottom | Align.Left), AnchorPoint(400, 720, Align.Bottom | Align.Left)))

    # 可能在 活跃度 或 周度游历，切换到标签页
    if not ui.search(ctx.tr(I18nText.ActivityPts), roi_bottom_activity_pts):
        if not ui.click_text(ctx.tr(I18nText.ActivityDaily), roi_tab, delay=0.3, times=2, interval=0.3):
            return _fail_return()
        if not ui.wait().until(lambda: ui.snapshot().search(ctx.tr(I18nText.ActivityPts), roi_bottom_activity_pts)):
            return _fail_return()

    # 领取活跃点
    claim_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(1020, 130, Align.Right | Align.Top),
        AnchorPoint(1280, 586, Align.Right | Align.Bottom))
    )
    res_claim = ui.search(ctx.tr(I18nText.ActivityClaim), claim_roi)
    if not res_claim:
        res_claim = ui.sleep(0.3).snapshot().search(ctx.tr(I18nText.ActivityClaim), claim_roi)
    if res_claim:
        res_claim.sort(key=lambda p: p.y1)
        ui.click_bbox(res_claim, delay=0.3)
        ui.sleep(0.5).wait().until(
            lambda: not ui.snapshot().search(ctx.tr(I18nText.ActivityClaim), claim_roi))

    # 领取活跃点奖励
    result = __doClaimActivityPts(ctx, local, 6, 20)

    if not result:
        return _fail_return()
    # 不管活跃度满没满都算完成
    local.activityDailyFSM.complete()
    return True


@node(NodeName.doActivityWeekly)
def doActivityWeekly(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[bool]:
    """周度游历"""
    if local.activityWeeklyFSM.is_terminal:
        return True
    in_progress = local.activityWeeklyFSM.status == TaskStatus.IN_PROGRESS
    if local.activityWeeklyFSM.status == TaskStatus.PENDING:
        local.activityWeeklyFSM.start()

    ui = UIOp(ctx)
    ui.snapshot()

    def _fail_return():
        # ui.esc().sleep(1)
        if in_progress:
            local.activityWeeklyFSM.fail()
        return True

    # 校验是否在活跃度页面
    if not ui.search(ctx.tr(I18nText.Activity), bbox_guidebook_title(ctx)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Activity).raw}")
        return _fail_return()

    # 上方活跃度、周度游历标签文字
    roi_tab = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Top | Align.Left), AnchorPoint(610, 130, Align.Top | Align.Left)))
    # 左下角活跃度、游历值文字
    roi_bottom_activity_pts = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 575, Align.Bottom | Align.Left), AnchorPoint(400, 720, Align.Bottom | Align.Left)))

    # 可能在 活跃度 或 周度游历，切换到标签页
    if ui.search(ctx.tr(I18nText.ActivityPts), roi_bottom_activity_pts) or not ui.search(
            ctx.tr(I18nText.WeeklyActivityPts), roi_bottom_activity_pts):
        if not ui.click_text(ctx.tr(I18nText.ActivityWeekly), roi_tab, delay=0.3, times=2, interval=0.3):
            return _fail_return()
        if not ui.wait().until(
                lambda: ui.snapshot().search(ctx.tr(I18nText.WeeklyActivityPts), roi_bottom_activity_pts)):
            return _fail_return()

    # 领取活跃点奖励
    res_claim = __doClaimActivityPts(ctx, local, 7, 1000)

    # 点击幻梦游园·狂想
    if not ui.wait().until(lambda: ui.snapshot().click_text(
            ctx.tr(I18nText.PhantasmaDreamlandRhapsody), delay=0.2, times=2, interval=0.2)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.PhantasmaDreamlandRhapsody).raw}")
        return _fail_return()

    # 等待游戏主页
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot()
                    and ui.search(ctx.tr(I18nText.PdrDreamGallery))
                    and ui.search(ctx.tr(I18nText.PdrWeeklyActivityPts))):
        logger.warning(f"Text not found: {ctx.tr(I18nText.PdrDreamGallery).raw}")
        return _fail_return()

    # 检查游历值
    pts_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top),
        AnchorPoint(235, 200, Align.Left | Align.Top)
    ))
    if ui.sleep(0.3).snapshot().search(ctx.tr(I18nText.PdrLimitReached), pts_roi):
        logger.info(f"Weekly Activity Pts: {ctx.tr(I18nText.PdrLimitReached).raw}")
        if res_claim:
            local.activityWeeklyFSM.complete()
            return True
        return _fail_return()

    # 刷幻梦游园·狂想
    return False


def __doClaimActivityPts(ctx: NodeContext, local: TaskLocal, num_points: int, increment: int) -> bool:
    """领取活跃点奖励"""

    ui = UIOp(ctx)

    max_pts = (num_points - 1) * increment
    # 0-100两端对齐等分布局
    # 331 502 673 844 1015 1186
    pts0 = ctx.scaler.as_point(AnchorPoint(331, 639, Align.Left | Align.Bottom))
    pts100 = ctx.scaler.as_point(AnchorPoint(1186, 639, Align.Right | Align.Bottom))
    # 采样点，中心点右上角灰色区域（领取活跃度后）内的点
    pts100_sp = ctx.scaler.as_point(AnchorPoint(1187, 633, Align.Right | Align.Bottom))

    pts_sp_x = linear_spacing(pts0.x, pts100.x, num_points, pts100_sp.x - pts100.x)
    pts_sp = [Point(x, pts100_sp.y) for x in pts_sp_x]
    logger.debug(f"pts_sp: {pts_sp}")

    yellow = Color.bgr(164, 231, 254)
    grey = Color.bgr(106, 105, 101)

    img = ui.sleep(0.3).grap()

    # 检查100活跃点是否为灰色已领取
    if ColorRule().points(pts_sp[num_points - 1]).colors(grey).match(img):
        logger.info(rf"Activity Pts >= {max_pts}")
        return True

    tap_close = ctx.tr([I18nText.TapTheBlankAreaToClose, I18nText.TapTheBlankAreaToContinue])

    # 检查100活跃点是否为黄色待领取
    if ColorRule().points(pts_sp[num_points - 1]).colors(yellow).match(img):
        ui.click_point(pts_sp[num_points - 1], times=3, interval=0.25)
        if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().click_text(tap_close, times=2, interval=0.2)):
            return False
        ui.sleep(0.3)
        logger.info(rf"Activity Pts >= {max_pts}")
        return True

    # 遍历，找出黄色的活跃点，点击领取
    idx = 0
    for i in range(len(pts_sp) - 1, -1, -1):
        if i == 0:
            break
        # 检查活跃点是否为黄色待领取
        if ColorRule().points(pts_sp[i]).colors(yellow).match(img):
            ui.click_point(pts_sp[i], times=3, interval=0.25)
            if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().click_text(tap_close, times=2, interval=0.2)):
                return False
            ui.sleep(0.3)
            idx = i
            break
        # 检查活跃点是否为灰色已领取
        if ColorRule().points(pts_sp[i]).colors(grey).match(img):
            idx = i
            break

    # 计算当前活跃度
    cur_pts = idx * increment
    logger.debug(f"cur_pts: {cur_pts}")
    if cur_pts == max_pts:
        logger.info(rf"Activity Pts: {cur_pts} >= {max_pts}")
    else:
        logger.warning(rf"Activity Pts: {cur_pts}")

    return True


@node(NodeName.doPhantasmaDreamlandRhapsody)
def doPhantasmaDreamlandRhapsody(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    """幻梦游园·狂想"""
    from src.core import message
    from src.core.runtime import RuntimeConfig
    from src.service.phantasma_dreamland_rhapsody_workflow import PhantasmaDreamlandRhapsodyWorkflow

    pctx = ctx
    spec = ctx.spec
    ipc = ctx.ipc
    event = ctx.runtime.stop_event
    container = ctx._container
    source = MsgSource.DAILY_TASK

    # 创建新的上下文
    ctx = NodeContext()
    ctx.spec = spec
    ctx.ipc = ipc
    ctx.runtime.stop_event = event
    ctx.runtime.cfg = RuntimeConfig(spec.user_config)
    ctx.runtime.send = message.make_sender(ipc.proc_queue, source, spec.task_id)

    ctx._container = container

    wf = PhantasmaDreamlandRhapsodyWorkflow(ctx)
    wf.embedding = True
    wf.execute()
    return True


@node(NodeName.doMaterialCollection)
def doMaterialCollection(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    # TODO 双倍流程？
    if local.weeklyChallengeFSM.is_active:
        return I18nText.WeeklyChallenge
    if local.forgeryChallengeFSM.is_active:
        return I18nText.ForgeryChallenge
    if local.simulationChallengeFSM.is_active:
        return I18nText.SimulationChallenge
    if local.bossChallengeFSM.is_active:
        return I18nText.BossChallenge
    if local.tacetSuppressionFSM.is_active:
        return I18nText.TacetSuppression
    # if local.weeklyChallengeFSM.is_active:
    #     return I18nText.WeeklyChallenge
    if local.nightmarePurificationFSM.is_active:
        return I18nText.NightmarePurification
    if local.tacetDiscordNestFSM.is_active:
        return I18nText.TacetDiscordNest
    return None


@node(NodeName.doForgeryChallenge)
def doForgeryChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.forgeryChallengeFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    roiex = RoiEx(ctx)
    ui.activate().sleep(0.1)

    # fsm的name = 副本id
    for fsm in local.forgeryChallengeFSM.children:
        # 检查当前副本状态
        if fsm.status.is_terminal:
            continue
        if not fsm.start():
            break
        dungeon = Dungeon.ForgeryChallenge.get(fsm.name)
        if not dungeon:
            logger.warning(f"Dungeon '{ctx.tr(fsm.name).raw}' not found")
            break
        dungeon_name = ctx.tr(dungeon.id)
        cost = dungeon.waveplate or 40

        def _fail():
            ui.esc().sleep(1.2)
            if fsm.is_terminal:
                return True
            if fsm.count == 0:
                fsm.fail()
                return True
            return False

        try:
            # 点击凝素领域
            if not ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.ForgeryChallenge), roiex.guidebook_menu,
                                                     pk=PointKind.RANDOM, times=2, interval=0.2)
                            and ui.search(ctx.tr(I18nText.SortByWeaponType), roiex.guidebook_content)):
                return _fail()

            # 检查体力
            cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
            if cur_waveplate is None or waveplate_crystal is None:
                return _fail()
            # 体力不足
            if cur_waveplate < cost:
                fsm.complete()
                return True

            # 今日剩余双倍奖励次数: 3/3
            # 无实际作用，仅用于页面上设置双倍次数未用完时，发送桌面通知
            result = ui.search(ctx.tr(I18nText.DoubleDropChancesToday))
            if result and local.doubleDropForgeryChallengeFSM.status == TaskStatus.NOT_REQUIRED:
                logger.warning("there are double drop chances today")
            elif local.doubleDropForgeryChallengeFSM.is_active:
                if local.doubleDropForgeryChallengeFSM.status == TaskStatus.PENDING:
                    local.doubleDropForgeryChallengeFSM.start()
                if result:
                    remain, max_remain = match_remaining_attempts(result)
                    if remain is None or not max_remain:
                        local.doubleDropForgeryChallengeFSM.fail()
                    elif remain == 0:
                        local.doubleDropForgeryChallengeFSM.complete()
                else:
                    local.doubleDropForgeryChallengeFSM.complete()

            # 滑动寻找入口
            is_start_challenge = False
            slider_points = Slider.points(ui.grap())
            for i, p in enumerate(slider_points):
                if i > 0:
                    logger.debug(f"Scroll point: {p}")
                    ui.click_point(p, times=2, interval=0.2)
                    ui.sleep(0.2).snapshot()
                else:
                    ui.snapshot()
                if not (dungeon_text := ui.search(dungeon_name, roiex.guidebook_content)):
                    continue
                if not (
                challenge_list := ui.search(ctx.tr([I18nText.Challenge, I18nText.Go]), roiex.guidebook_content)):
                    continue
                challenge_list.sort(key=lambda x: x.y1)
                if dungeon_text[0].y1 > challenge_list[-1].y2:
                    continue
                if not (challenge_text := next((cl for cl in challenge_list if dungeon_text[0].y1 < cl.y2), None)):
                    return _fail()
                # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
                if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
                    continue

                # 点击直接挑战
                ui.sleep(0.2)
                for _ in range(2):
                    # 若ui太卡，点快了没跳转，再试一次
                    ui.click_bbox(challenge_text, delay=0.3, times=2, interval=0.1)
                    if ui.sleep(1).wait(3).until(
                            lambda: not ui.snapshot().search(ctx.tr(I18nText.ForgeryChallenge), roiex.guidebook_menu)):
                        break

                # 点击单人挑战
                if not ui.sleep(0.3).wait().until(
                        lambda: ui.snapshot().search(ctx.tr(I18nText.EnableNavigation))
                                or ui.search(ctx.tr(I18nText.Match))
                                and ui.click_text(ctx.tr(I18nText.SoloChallenge), delay=0.4)):
                    return _fail()

                # 副本未解锁
                if ui.search(ctx.tr(I18nText.EnableNavigation)):
                    logger.warning(f"Unlock dungeon: {dungeon_name.raw}")
                    fsm.fail()
                    return _fail()

                is_start_challenge = True
                break

            # 没找到副本
            if not is_start_challenge:
                logger.warning(f"Dungeon not found: {dungeon_name.raw}")
                return _fail()

            # 点击开始挑战
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.StartChallenge), delay=0.3, times=2,
                                                     interval=0.3)):
                return _fail()

            quest_roi = ctx.scaler.as_bbox(AnchorBBox(
                AnchorPoint(0, 0, Align.Left | Align.Top), AnchorPoint(400, 720, Align.Left | Align.Bottom)))

            # 循环刷
            max_challenge = 12
            for i in range(max_challenge):
                if i == max_challenge - 1:
                    return _fail()

                # 确认已进入副本
                if not ui.sleep(3 if i > 0 else 0.1).wait(25, 0.5).until(
                        lambda: ui.is_on_homepage()
                                and ui.snapshot().search(ctx.tr(I18nText.StartChallenge), quest_roi)):
                    return _fail()

                # 开始挑战
                if not move_and_scan_dialogue(ctx, ctx.tr(I18nText.StartChallenge), 15):
                    return _fail()
                ui.pick_up(2, 0.2).sleep(0.3)

                # 打
                combat_system = CombatSystem(ctx.control_service, ctx.img_service)
                combat_system.set_resonators(local.members, is_print=False)
                combat_system.is_async = True
                combat_system.check_boss_hp = False
                combat_system.auto_pickup = False

                timeout = 10 * 60
                no_text_count = 3
                no_text_max = no_text_count
                deadline = time.monotonic() + timeout

                while ui.is_set() or time.monotonic() < deadline:
                    if no_text_count < 0:
                        break
                    combat_system.start(3.5)
                    ui.sleep(1.5)
                    ui.snapshot()
                    if ui.is_on_homepage():
                        # 挑战成功
                        if ui.search(ctx.tr(I18nText.ForgeryChallengeComplete)):
                            break
                        # 限时击败敌人
                        if ui.search(ctx.tr(I18nText.DefeatTheEnemiesWithinTimeLimit)):
                            logger.debug("战斗中")
                            no_text_count = no_text_max
                            continue
                        else:
                            logger.debug(f"Text not found: {ctx.tr(I18nText.DefeatTheEnemiesWithinTimeLimit).raw}")
                        no_text_count -= 1

                    if page_key := GlobalPage(ctx).action(ui=ui):
                        if page_key == GlobalPage.InternetDisconnecting:
                            combat_system.stop(join=True)
                            return False

                combat_system.stop(join=True)

                ui.sleep(0.6).snapshot()
                # 检查复苏弹窗
                if ui.search(ctx.tr(I18nText.SelectARevivalItem)):
                    ui.esc().sleep(0.5)
                elif ui.search(ctx.tr(I18nText.ForgeryClaim)):
                    logger.info("Challenge Complete")
                    logger.debug(f"Found text: {ctx.tr(I18nText.ForgeryClaim)}")
                    ui.sleep(0.3)
                else:
                    combat_system.exit_special_state(Morph.Prefer)
                    ui.sleep(0.3)
                    logger.info("Challenge Complete")

                    # 寻找领取奖励交互点
                    if not object_detection(ctx, search_reward=True, timeout=25):
                        ui.esc()
                        if ui.sleep(0.3).wait().until(
                                lambda: ui.snapshot().click_text(
                                    ctx.tr(I18nText.Restart), delay=0.3, times=2, interval=0.3)):
                            continue
                        return _fail()

                    # 领取奖励
                    if not ui.pick_up(2, 0.2).sleep(0.3).wait().until(
                            lambda: ui.snapshot().search(ctx.tr(I18nText.ForgeryClaim))):
                        return _fail()

                # 获取体力值
                cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

                if cur_waveplate is None or waveplate_crystal is None:
                    return _fail()
                if cur_waveplate < cost:
                    fsm.complete()
                    return True
                # 根据体力选择双倍单倍
                if cur_waveplate >= cost * 2:
                    claim = I18nText.ForgeryClaimX2
                    cur_waveplate -= cost * 2
                else:
                    claim = I18nText.ForgeryClaim
                    cur_waveplate -= cost
                if not ui.click_text(ctx.tr(claim), delay=0.4):
                    return _fail()

                # 此处仅打印日志用，打印剩余次数
                match_remaining_attempts(ui.search(ctx.tr(I18nText.DoubleDropChancesToday)))

                # 根据体力选择重新挑战还是离开
                if ui.sleep(0.3).wait().until(
                        lambda: ui.snapshot().search(ctx.tr([I18nText.ForgeryExit, I18nText.ForgeryRestart]))):
                    if cur_waveplate >= cost:
                        if ui.click_text(ctx.tr(I18nText.ForgeryRestart), delay=0.3, times=2, interval=0.3):
                            continue
                        else:
                            return _fail()
                    else:
                        ui.click_text(ctx.tr(I18nText.ForgeryExit), delay=0.3, times=2, interval=0.3)
                else:
                    if cur_waveplate >= cost:
                        return _fail()
                fsm.complete()
                return True

            if not fsm.is_terminal:
                fsm.fail()
        except (KeyboardInterrupt, StopError) as e:
            raise e
        except Exception as e:
            logger.exception(e)

    # 未知异常兜底，标记失败
    for fsm in local.forgeryChallengeFSM.children:
        if fsm.status == TaskStatus.PENDING:
            fsm.start()
            fsm.fail()
        elif fsm.status in [TaskStatus.IN_PROGRESS, TaskStatus.WAITING]:
            fsm.fail()
    return False


@node(NodeName.doSimulationChallenge)
def doSimulationChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


@node(NodeName.doBossChallenge)
def doBossChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.bossChallengeFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    roiex = RoiEx(ctx)

    # fsm的name = 副本id
    for fsm in local.bossChallengeFSM.children:
        # 检查当前副本状态
        if fsm.status.is_terminal:
            continue
        if not fsm.start():
            break
        dungeon = Dungeon.BossChallenge.get(fsm.name)
        if not dungeon:
            logger.warning(f"Dungeon '{ctx.tr(fsm.name).raw}' not found")
            break
        dungeon_name = ctx.tr(dungeon.id)
        cost = dungeon.waveplate or 60

        if not dungeon.enemy_id or not Enemy.from_id(dungeon.enemy_id):
            logger.warning(f"Enemy '{dungeon.enemy_id}' not found")
            break
        enemy = Enemy.from_id(dungeon.enemy_id)
        logger.info(f"{dungeon_name.raw}")

        def _fail():
            ui.esc().sleep(1.2)
            if fsm.is_terminal:
                return True
            if fsm.count == 0:
                fsm.fail()
                return True
            return False

        try:
            # 点击讨伐强敌
            if not ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.BossChallenge), roiex.guidebook_menu,
                                                     pk=PointKind.RANDOM, times=2, interval=0.2)
                            and ui.search(ctx.tr(I18nText.FilterToViewRewardsForEachPhase), roiex.guidebook_content)):
                return _fail()

            # 检查体力
            cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
            if cur_waveplate is None or waveplate_crystal is None:
                return False
            if cur_waveplate < cost:
                fsm.complete()
                return True

            # 滑动寻找入口
            is_start_challenge = False
            slider_points = Slider.points(ui.grap())
            for i, p in enumerate(slider_points):
                if i > 0:
                    logger.debug(f"Scroll point: {p}")
                    ui.click_point(p, times=2, interval=0.2)
                    ui.sleep(0.2).snapshot()
                else:
                    ui.snapshot()
                if not (dungeon_text := ui.search(dungeon_name, roiex.guidebook_content)):
                    continue
                if not (
                challenge_list := ui.search(ctx.tr([I18nText.Challenge, I18nText.Go]), roiex.guidebook_content)):
                    continue
                challenge_list.sort(key=lambda x: x.y1)
                if dungeon_text[0].y1 > challenge_list[-1].y2:
                    continue
                if not (challenge_text := next((cl for cl in challenge_list if dungeon_text[0].y1 < cl.y2), None)):
                    return _fail()
                # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
                if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
                    continue

                # 点击直接挑战
                ui.click_bbox(challenge_text, delay=0.4, times=2, interval=0.1)

                # 点击提示弹窗
                # 有提示时不能选队伍，直接进入副本
                # 没提示时进入队伍选择
                if not ui.sleep(0.2).wait().until(
                        lambda: ui.snapshot().search(ctx.tr(I18nText.ArrivingAtTheDestination))
                                and ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3, times=2, interval=0.2)
                                or ui.search(ctx.tr(I18nText.QuickSetup))
                                and ui.click_text(ctx.tr(I18nText.StartChallenge), times=3, interval=0.3)):
                    return _fail()

                is_start_challenge = True
                break

            # 没找到副本
            if not is_start_challenge:
                logger.warning(f"Dungeon not found: {dungeon_name.raw}")
                return _fail()

            # 循环刷
            max_challenge = 9
            for i in range(max_challenge):
                if i == max_challenge - 1:
                    return _fail()

                # 确认已进入副本
                if not ui.sleep(3 if i == 0 else 0.1).wait(15, 0.2).until(lambda: ui.is_on_homepage()):
                    return _fail()
                logger.info("已进入副本")
                if dungeon.id == I18nText.SeedOfIllusoryOrigin:
                    for _ in range(3):
                        ctx.control_service.dash_dodge()
                        ui.sleep(0.2)
                    ctx.control_service.attack()
                    ui.sleep(0.6)

                combat_system = CombatSystem(ctx.control_service, ctx.img_service)
                combat_system.set_resonators(local.members, is_print=False)
                combat_system.is_async = True
                combat_system.check_boss_hp = True
                combat_system.auto_pickup = False
                combat_system.exit_special_state(Morph.Forced)

                # 打
                timeout = 10 * 60
                no_text_count = 3
                no_text_max = no_text_count
                deadline = time.monotonic() + timeout

                while ui.is_set() or time.monotonic() < deadline:
                    if no_text_count < 0:
                        break
                    combat_system.start(3.5)
                    ui.sleep(1.5)
                    ui.snapshot()
                    if ui.is_on_homepage():
                        # 领取奖励
                        stop_text = [I18nText.WeeklyClaimRewards]
                        if enemy.quick_boss_meta.stop_text:
                            stop_text.extend(enemy.quick_boss_meta.stop_text)
                        if ui.search(ctx.tr(stop_text)):
                            logger.debug("Weekly Claim Rewards")
                            break
                        # 击败敌人
                        if ui.search(ctx.tr(enemy.quick_boss_meta.battle_text)):
                            logger.debug("Fight fight!")
                            no_text_count = no_text_max
                            continue
                        else:
                            logger.debug(f"Text not found: {ctx.tr(I18nText.WeeklyDefeatTheEnemy).raw}")
                        no_text_count -= 1

                    if page_key := GlobalPage(ctx).action(ui=ui):
                        if page_key == GlobalPage.InternetDisconnecting:
                            combat_system.stop(join=True)
                            return False

                combat_system.stop(join=True)

                notice_keywords = ctx.tr([I18nText.WeeklyConfirm, I18nText.WeeklyExit])
                ui.sleep(0.5).snapshot()

                # 检查复苏弹窗
                if ui.search(ctx.tr(I18nText.SelectARevivalItem)):
                    ui.esc().sleep(0.5)
                elif ui.search(notice_keywords):
                    logger.debug(f"Found text: {notice_keywords}")
                    logger.info("Challenge Complete")
                    ui.sleep(0.3)
                else:
                    combat_system.exit_special_state(Morph.Prefer)
                    ui.sleep(0.3)

                    logger.info("Challenge Complete")

                    # 寻找领取奖励交互点
                    if not object_detection(ctx, search_reward=True, timeout=40):
                        if ui.esc().sleep(0.5).wait().until(
                                lambda: ui.snapshot().click_text(ctx.tr([I18nText.WeeklyRestart, I18nText.WeeklyExit]))):
                            if ui.click_text(ctx.tr(I18nText.WeeklyRestart), delay=0.4, times=2, interval=0.2):
                                continue
                            ui.click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4, times=2, interval=0.2)
                        return _fail()

                    # 领取奖励
                    if not ui.pick_up(2, 0.2).sleep(0.5).wait().until(
                            lambda: ui.snapshot().search(notice_keywords)):
                        return _fail()

                cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

                if cur_waveplate is None or waveplate_crystal is None:
                    return _fail()
                if cur_waveplate < cost:
                    fsm.complete()
                    return True

                cur_waveplate -= cost
                if not ui.click_text(ctx.tr(I18nText.WeeklyConfirm), delay=0.3):
                    return _fail()

                ui.sleep(1)
                # 容错，判断是否有体力不足是否继续弹窗
                if ui.snapshot().search(ctx.tr([I18nText.WeeklyCancel, I18nText.DoNotShowAgain])):
                    ui.click_text(ctx.tr(I18nText.DoNotShowAgain), delay=0.3)
                    ui.click_text(ctx.tr(I18nText.WeeklyCancel), delay=0.2)
                    fsm.complete()
                    return True

                if cur_waveplate >= cost:
                    if ui.wait().until(
                            lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyRestart), delay=0.4, times=2, interval=0.2)):
                        continue
                    return _fail()

                ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4, times=2, interval=0.2))
                fsm.complete()
                if ui.sleep(2).wait_back_home():
                    ui.sleep(0.5)
                return True

            if not fsm.is_terminal:
                fsm.fail()
        except (KeyboardInterrupt, StopError) as e:
            raise e
        except Exception as e:
            logger.exception(e)

    # 未知异常兜底，标记失败
    for fsm in local.bossChallengeFSM.children:
        if fsm.status == TaskStatus.PENDING:
            fsm.start()
            fsm.fail()
        elif fsm.status in [TaskStatus.IN_PROGRESS, TaskStatus.WAITING]:
            fsm.fail()
    return False

@node(NodeName.doTacetSuppression)
def doTacetSuppression(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.tacetSuppressionFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    roiex = RoiEx(ctx)

    # fsm的name = 副本id
    for fsm in local.tacetSuppressionFSM.children:
        # 检查当前副本状态
        if fsm.status.is_terminal:
            continue
        if not fsm.start():
            break
        dungeon = Dungeon.TacetSuppression.get(fsm.name)
        if not dungeon:
            logger.warning(f"Dungeon '{ctx.tr(fsm.name).raw}' not found")
            break
        dungeon_name = ctx.tr(dungeon.id)
        cost = dungeon.waveplate or 60

        def _fail():
            ui.esc().sleep(1.2)
            if fsm.is_terminal:
                return True
            if fsm.count == 0:
                fsm.fail()
                return True
            return False

        try:
            # 点击无音清剿
            if not ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.TacetSuppression), roiex.guidebook_menu,
                                                     pk=PointKind.RANDOM, times=2, interval=0.2)
                            and ui.search(ctx.tr(I18nText.EchoSet), roiex.guidebook_content)):
                return _fail()

            # 检查体力
            cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
            if cur_waveplate is None or waveplate_crystal is None:
                return _fail()
            # 体力不足
            if cur_waveplate < cost:
                fsm.complete()
                return True

            # 今日剩余双倍奖励次数: 3/3
            # 无实际作用，仅用于页面上设置双倍次数未用完时，发送桌面通知
            result = ui.search(ctx.tr(I18nText.DoubleDropChancesToday))
            if result and local.doubleDropTacetSuppressionFSM.status == TaskStatus.NOT_REQUIRED:
                logger.warning("there are double drop chances today")
            elif local.doubleDropTacetSuppressionFSM.is_active:
                if local.doubleDropTacetSuppressionFSM.status == TaskStatus.PENDING:
                    local.doubleDropTacetSuppressionFSM.start()
                if result:
                    remain, max_remain = match_remaining_attempts(result)
                    if remain is None or not max_remain:
                        local.doubleDropTacetSuppressionFSM.fail()
                    elif remain == 0:
                        local.doubleDropTacetSuppressionFSM.complete()
                else:
                    local.doubleDropTacetSuppressionFSM.complete()

            # 滑动寻找入口
            is_start_challenge = False
            slider_points = Slider.points(ui.grap())
            for i, p in enumerate(slider_points):
                if i > 0:
                    logger.debug(f"Scroll point: {p}")
                    ui.click_point(p, times=2, interval=0.2)
                    ui.sleep(0.2).snapshot()
                else:
                    ui.snapshot()
                if not (dungeon_text := ui.search(dungeon_name, roiex.guidebook_content)):
                    continue
                if not (challenge_list := ui.search(ctx.tr([I18nText.Challenge, I18nText.Go]), roiex.guidebook_content)):
                    continue
                challenge_list.sort(key=lambda x: x.y1)
                if dungeon_text[0].y1 > challenge_list[-1].y2:
                    continue
                if not (challenge_text := next((cl for cl in challenge_list if dungeon_text[0].y1 < cl.y2), None)):
                    return _fail()
                # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
                if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
                    continue

                # 点击直接挑战
                ui.sleep(0.2)
                for _ in range(2):
                    # 若ui太卡，点快了没跳转，再试一次
                    ui.click_bbox(challenge_text, delay=0.3, times=2, interval=0.1)
                    if ui.sleep(1).wait(3).until(
                            lambda: not ui.snapshot().search(ctx.tr(I18nText.TacetSuppression), roiex.guidebook_menu)):
                        break

                # 点击开始挑战
                if not ui.sleep(0.3).wait().until(
                        lambda: ui.snapshot().search(ctx.tr([I18nText.EnableNavigation, I18nText.Track]))
                                or ui.search(ctx.tr(I18nText.QuickSetup))
                                and ui.click_text(ctx.tr(I18nText.StartChallenge), delay=0.3, times=3, interval=0.3)):
                    return _fail()

                # 副本未解锁
                if ui.search(ctx.tr([I18nText.EnableNavigation, I18nText.Track])):
                    logger.warning(f"Unlock dungeon: {dungeon_name.raw}")
                    fsm.fail()
                    return _fail()

                is_start_challenge = True
                break

            # 没找到副本
            if not is_start_challenge:
                logger.warning(f"Dungeon not found: {dungeon_name.raw}")
                return _fail()

            # 循环刷
            max_challenge = 9
            for i in range(max_challenge):
                if i == max_challenge - 1:
                    return _fail()

                # 进入副本
                if ui.sleep(0.5).wait_back_home():
                    ui.sleep(1.0)
                else:
                    return _fail()

                # 检查战斗文本
                keyword = ctx.tr([I18nText.DefeatTheTdsInTheTacetField, I18nText.TacetField])
                if not ui.snapshot().search(keyword):
                    if ui.esc().sleep(0.3).wait().until(
                            lambda: ui.snapshot().click_text(ctx.tr(I18nText.Restart), delay=0.3, times=2, interval=0.3)):
                        continue
                    return _fail()

                # 直接打，打起来才会有文字提示
                combat_system = CombatSystem(ctx.control_service, ctx.img_service)
                combat_system.set_resonators(local.members, is_print=False)
                combat_system.is_async = True
                combat_system.check_boss_hp = False
                combat_system.auto_pickup = False
                combat_system.exit_special_state(Morph.Forced)

                timeout = 10 * 60
                no_text_count = 3
                no_text_max = no_text_count
                deadline = time.monotonic() + timeout

                while ui.is_set() or time.monotonic() < deadline:
                    if no_text_count < 0:
                        break
                    combat_system.start(3.5)
                    ui.sleep(1.5)
                    ui.snapshot()
                    if ui.is_on_homepage():
                        # 挑战达成
                        if ui.search(ctx.tr(I18nText.TacetFieldChallengeComplete)):
                            break
                        # 清理无音区中涌现的残象
                        if ui.search(keyword):
                            logger.debug("战斗中")
                            no_text_count = no_text_max
                            continue
                        else:
                            logger.debug(f"Text not found: {ctx.tr(I18nText.TacetField).raw}")
                        no_text_count -= 1

                    if page_key := GlobalPage(ctx).action(ui=ui):
                        if page_key == GlobalPage.InternetDisconnecting:
                            combat_system.stop(join=True)
                            return False

                combat_system.stop(join=True)

                ui.sleep(0.6).snapshot()
                # 检查复苏弹窗
                if ui.search(ctx.tr(I18nText.SelectARevivalItem)):
                    ui.esc().sleep(0.5)
                elif ui.search(ctx.tr(I18nText.TacetFieldClaim)):
                    logger.info("Challenge Complete")
                    logger.debug(f"Found text: {ctx.tr(I18nText.TacetFieldClaim)}")
                    ui.sleep(0.3)
                else:
                    combat_system.exit_special_state(Morph.Prefer)
                    ui.sleep(0.3)
                    logger.info("Challenge Complete")

                    # 寻找领取奖励交互点
                    if not object_detection(ctx, search_reward=True, timeout=25):
                        ui.esc()
                        if ui.sleep(0.3).wait().until(
                                lambda: ui.snapshot().click_text(
                                    ctx.tr(I18nText.Restart), delay=0.3, times=2, interval=0.3)):
                            continue
                        return _fail()

                    # 领取奖励
                    if not ui.pick_up(2, 0.2).sleep(0.3).wait().until(
                            lambda: ui.snapshot().search(ctx.tr(I18nText.TacetFieldClaim))):
                        return _fail()

                # 获取体力值
                cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

                if cur_waveplate is None or waveplate_crystal is None:
                    return _fail()
                if cur_waveplate < cost:
                    fsm.complete()
                    return True
                # 根据体力选择双倍单倍
                if cur_waveplate >= cost * 2:
                    claim = I18nText.TacetFieldClaimX2
                    cur_waveplate -= cost * 2
                else:
                    claim = I18nText.TacetFieldClaim
                    cur_waveplate -= cost
                if not ui.click_text(ctx.tr(claim), delay=0.4):
                    return _fail()

                # 此处仅打印日志用，打印剩余次数
                match_remaining_attempts(ui.search(ctx.tr(I18nText.DoubleDropChancesToday)))

                # # 点击确认弹窗
                # if not ui.sleep(0.5).wait().until(
                #         lambda: ui.snapshot().click_text(ctx.tr(I18nText.TacetFieldConfirm), delay=0.3)):
                #     return _fail()

                ui.sleep(1)
                # 容错，判断是否有体力不足是否继续弹窗
                if ui.snapshot().search(ctx.tr([I18nText.WeeklyCancel, I18nText.DoNotShowAgain])):
                    if ui.click_text(ctx.tr(I18nText.DoNotShowAgain), delay=0.2):
                        ui.sleep(0.1)
                    if ui.click_text(ctx.tr(I18nText.WeeklyCancel), delay=0.2):
                        ui.sleep(0.4)
                        fsm.complete()
                        return True

                # 根据体力选择重新挑战还是离开
                if ui.sleep(0.3).wait().until(
                        lambda: ui.snapshot().search(ctx.tr([I18nText.TacetFieldExit, I18nText.TacetFieldRestart]))):
                    if cur_waveplate >= cost:
                        if ui.click_text(ctx.tr(I18nText.TacetFieldRestart), delay=0.3, times=2, interval=0.3):
                            continue
                        else:
                            return _fail()
                    else:
                        ui.click_text(ctx.tr(I18nText.TacetFieldExit), delay=0.3, times=2, interval=0.3)
                else:
                    if cur_waveplate >= cost:
                        return _fail()
                fsm.complete()
                return True

            if not fsm.is_terminal:
                fsm.complete()
                return True
        except (KeyboardInterrupt, StopError) as e:
            raise e
        except Exception as e:
            logger.exception(e)

    # 未知异常兜底，标记失败
    for fsm in local.tacetSuppressionFSM.children:
        if fsm.status == TaskStatus.PENDING:
            fsm.start()
            fsm.fail()
        elif fsm.status in [TaskStatus.IN_PROGRESS, TaskStatus.WAITING]:
            fsm.fail()
    return False


@node(NodeName.doWeeklyChallenge)
def doWeeklyChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.weeklyChallengeFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    roiex = RoiEx(ctx)

    # fsm的name = 副本id
    for fsm in local.weeklyChallengeFSM.children:
        # 检查当前副本状态
        if fsm.status.is_terminal:
            continue
        if not fsm.start():
            break
        dungeon = Dungeon.WeeklyChallenge.get(fsm.name)
        if not dungeon:
            logger.warning(f"Dungeon '{ctx.tr(fsm.name).raw}' not found")
            break
        dungeon_name = ctx.tr(dungeon.id)
        cost = dungeon.waveplate or 60

        if not dungeon.enemy_id or not Enemy.from_id(dungeon.enemy_id):
            logger.warning(f"Enemy '{dungeon.enemy_id}' not found")
            break
        enemy = Enemy.from_id(dungeon.enemy_id)
        logger.info(f"{dungeon_name.raw}['{ctx.tr(enemy.id).raw}']")

        def _fail():
            ui.esc().sleep(1.2)
            if fsm.is_terminal:
                return True
            if fsm.count == 0:
                fsm.fail()
                return True
            return False

        try:
            # 点击战歌重奏
            if not ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyChallenge), roiex.guidebook_menu,
                                                     pk=PointKind.RANDOM, times=2, interval=0.2)
                            and ui.search(ctx.tr(I18nText.FilterToViewRewardsForEachPhase), roiex.guidebook_content)):
                return _fail()

            # 检查体力
            cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
            if cur_waveplate is None or waveplate_crystal is None:
                return False
            if cur_waveplate < cost:
                fsm.complete()
                return True

            # 本周剩余可收取次数: 3/3
            result = ui.sleep(0.2).wait().until(
                lambda: ui.snapshot().search(ctx.tr(I18nText.RemainingWeeklyAttempts), bbox_guidebook_content(ctx)))
            remain, max_remain = match_remaining_attempts(result)
            if remain is None or not max_remain:
                return _fail()
            if remain == 0:
                fsm.complete()
                return True

            # 滑动寻找入口
            is_start_challenge = False
            slider_points = Slider.points(ui.grap())
            for i, p in enumerate(slider_points):
                if i > 0:
                    logger.debug(f"Scroll point: {p}")
                    ui.click_point(p, times=2, interval=0.2)
                    ui.sleep(0.2).snapshot()
                else:
                    ui.snapshot()
                if not (dungeon_text := ui.search(dungeon_name, roiex.guidebook_content)):
                    continue
                if not (
                challenge_list := ui.search(ctx.tr([I18nText.Challenge, I18nText.Go]), roiex.guidebook_content)):
                    continue
                challenge_list.sort(key=lambda x: x.y1)
                if dungeon_text[0].y1 > challenge_list[-1].y2:
                    continue
                if not (challenge_text := next((cl for cl in challenge_list if dungeon_text[0].y1 < cl.y2), None)):
                    return _fail()
                # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
                if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
                    continue

                # 点击直接挑战
                ui.click_bbox(challenge_text, delay=0.4, times=2, interval=0.1)

                def _wait_solo_challenge():
                    ui.snapshot()
                    if ui.click_text(ctx.tr(I18nText.SoloChallenge), delay=0.4):
                        return True
                    if ui.snapshot().search(ctx.tr(I18nText.ArrivingAtTheDestination)):
                        ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3)
                    return False

                # 点击提示弹窗
                if not ui.sleep(0.2).wait(6).until(_wait_solo_challenge):
                    return _fail()

                is_start_challenge = True
                break

            # 没找到副本
            if not is_start_challenge:
                logger.warning(f"Dungeon not found: {dungeon_name.raw}")
                return _fail()

            # 点击开始挑战
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.StartChallenge), delay=0.3, times=2,
                                                     interval=0.3)):
                return _fail()

            # 循环刷
            max_challenge = 9
            for i in range(max_challenge):
                if i == max_challenge - 1:
                    return _fail()

                # 确认已进入副本
                if not ui.sleep(3 if i == 0 else 0.1).wait(15, 0.2).until(lambda: ui.is_on_homepage()):
                    return _fail()
                logger.info("已进入副本")
                if dungeon.id == I18nText.SeedOfIllusoryOrigin:
                    for _ in range(3):
                        ctx.control_service.dash_dodge()
                        ui.sleep(0.2)
                    ctx.control_service.attack()
                    ui.sleep(0.6)

                combat_system = CombatSystem(ctx.control_service, ctx.img_service)
                combat_system.set_resonators(local.members, is_print=False)
                combat_system.is_async = True
                combat_system.check_boss_hp = True
                combat_system.auto_pickup = False
                combat_system.exit_special_state(Morph.Forced)

                # 打
                timeout = 10 * 60
                no_text_count = 3
                no_text_max = no_text_count
                deadline = time.monotonic() + timeout

                while ui.is_set() or time.monotonic() < deadline:
                    if no_text_count < 0:
                        break
                    combat_system.start(3.5)
                    ui.sleep(1.5)
                    ui.snapshot()
                    if ui.is_on_homepage():
                        # 领取奖励
                        stop_text = [I18nText.WeeklyClaimRewards]
                        if enemy.quick_boss_meta.stop_text:
                            stop_text.extend(enemy.quick_boss_meta.stop_text)
                        if ui.search(ctx.tr(stop_text)):
                            logger.debug("Weekly Claim Rewards")
                            break
                        # 击败敌人
                        if ui.search(ctx.tr(enemy.quick_boss_meta.battle_text)):
                            logger.debug("Fight fight!")
                            no_text_count = no_text_max
                            continue
                        else:
                            logger.debug(f"Text not found: {ctx.tr(I18nText.WeeklyDefeatTheEnemy).raw}")
                        no_text_count -= 1

                    if page_key := GlobalPage(ctx).action(ui=ui):
                        if page_key == GlobalPage.InternetDisconnecting:
                            combat_system.stop(join=True)
                            return False

                combat_system.stop(join=True)

                notice_keywords = ctx.tr([I18nText.WeeklyConfirm, I18nText.WeeklyExit])
                ui.sleep(0.5).snapshot()

                # 检查复苏弹窗
                if ui.search(ctx.tr(I18nText.SelectARevivalItem)):
                    ui.esc().sleep(0.5)
                elif ui.search(notice_keywords):
                    logger.debug(f"Found text: {notice_keywords}")
                    logger.info("Challenge Complete")
                    ui.sleep(0.3)
                else:
                    combat_system.exit_special_state(Morph.Prefer)
                    ui.sleep(0.3)

                    logger.info("Challenge Complete")

                    # 寻找领取奖励交互点
                    if not object_detection(ctx, search_reward=True, timeout=40):
                        if ui.esc().sleep(0.5).wait().until(
                                lambda: ui.snapshot().click_text(ctx.tr([I18nText.WeeklyRestart, I18nText.WeeklyExit]))):
                            if ui.click_text(ctx.tr(I18nText.WeeklyRestart), delay=0.4, times=2, interval=0.2):
                                continue
                            ui.click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4, times=2, interval=0.2)
                        return _fail()

                    # 领取奖励
                    if not ui.pick_up(2, 0.2).sleep(0.5).wait().until(
                            lambda: ui.snapshot().search(notice_keywords)):
                        return _fail()

                # 此处仅打印日志用，打印剩余次数
                match_remaining_attempts(ui.search(ctx.tr(I18nText.DoubleDropChancesToday)))

                # 检查是否达到次数上限
                if ui.search(ctx.tr(I18nText.YouHaveReachedTheChallengeLimit)):
                    logger.info(f"{ctx.tr(I18nText.YouHaveReachedTheChallengeLimit).raw}")
                    fsm.complete()
                    if ui.click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4):
                        if ui.sleep(2).wait_back_home():
                            ui.sleep(0.5)
                        else:
                            return _fail()
                    else:
                        logger.warning(f"Text not found: {ctx.tr(I18nText.WeeklyExit).raw}")
                    return True

                cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

                if cur_waveplate is None or waveplate_crystal is None:
                    return _fail()
                if cur_waveplate < cost:
                    fsm.complete()
                    return True

                cur_waveplate -= cost
                if not ui.click_text(ctx.tr(I18nText.WeeklyConfirm), delay=0.3):
                    return _fail()

                ui.sleep(1)
                # 容错，判断是否有体力不足是否继续弹窗
                if ui.snapshot().search(ctx.tr([I18nText.WeeklyCancel, I18nText.DoNotShowAgain])):
                    ui.click_text(ctx.tr(I18nText.DoNotShowAgain), delay=0.3)
                    ui.click_text(ctx.tr(I18nText.WeeklyCancel), delay=0.2)
                    fsm.complete()
                    return True

                if cur_waveplate >= cost:
                    if ui.wait().until(
                            lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyRestart), delay=0.4, times=2, interval=0.2)):
                        continue
                    return _fail()

                ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4, times=2, interval=0.2))
                fsm.complete()
                if ui.sleep(2).wait_back_home():
                    ui.sleep(0.5)
                return True

            if not fsm.is_terminal:
                fsm.fail()
        except (KeyboardInterrupt, StopError) as e:
            raise e
        except Exception as e:
            logger.exception(e)

    # 未知异常兜底，标记失败
    for fsm in local.weeklyChallengeFSM.children:
        if fsm.status == TaskStatus.PENDING:
            fsm.start()
            fsm.fail()
        elif fsm.status in [TaskStatus.IN_PROGRESS, TaskStatus.WAITING]:
            fsm.fail()
    return False


@node(NodeName.doNightmarePurification)
def doNightmarePurification(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


@node(NodeName.doTacetDiscordNest)
def doTacetDiscordNest(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.tacetDiscordNestFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    tacets = [
        I18nText.SimulacrumNexusTacetDiscordNest,
        I18nText.SouthernYuanHillsTacetDiscordNest,
        I18nText.StarblindCrashsiteTacetDiscordNest,
        I18nText.RebirthUplandsTacetDiscordNest,
        # I18nText.StagnantRunTacetDiscordNest,
    ]
    tacets_fsm = [
        local.simulacrumNexusTacetDiscordNestFSM,
        local.southernYuanHillsTacetDiscordNestFSM,
        local.starblindCrashsiteTacetDiscordNestFSM,
        local.rebirthUplandsTacetDiscordNestFSM,
        # local.stagnantRunTacetDiscordNestFSM,
    ]
    tacets_route = [
        [Run.forward(2.5)],
        [Run.forward(4.5)],
        [Run.right(0.25), Run.forward(3.3)],
        [Run.forward(2.5)],
        # [Run.forward(5.5)],
    ]

    try:
        scrollbar = ctx.scaler.as_point(AnchorPoint(458, 636, Align.Top | Align.Left))
        logger.debug(f"scrollbar point: {scrollbar}")

        # 点击残像聚落
        def _wait_content():
            if ui.snapshot().search(
                    ctx.tr(I18nText.SonataSetFilter), bbox_guidebook_content(ctx)):
                return True
            if not ui.click_text(
                    ctx.tr(I18nText.TacetDiscordNest), bbox_guidebook_item(ctx), pk=PointKind.RANDOM, times=2,
                    interval=0.1):
                ui.sleep(0.2).click_point(scrollbar, times=2, interval=0.1).sleep(0.3)
            return False

        # 确认已进入残像聚落
        if not ui.wait().until(_wait_content):
            for fsm in tacets_fsm:
                if fsm.status == TaskStatus.PENDING:
                    fsm.start()
                    fsm.fail()
                elif fsm.status in [TaskStatus.IN_PROGRESS, TaskStatus.WAITING]:
                    fsm.fail()
            return False

        progress_pattern = r"(\d{1,2}).*?(\d{1,2})"
        keywords = ctx.tr([*tacets, I18nText.Go]) + [progress_pattern]
        # 获取聚落列表
        textboxes = ui.snapshot().search(keywords, bbox_guidebook_content(ctx))
        textboxes.sort(key=lambda p: p.y1)
        logger.debug(f"textboxes: {textboxes}")

        # 三个一组分组
        tacets_idx = 0
        cards_idx = 0
        cards = []

        for textbox in textboxes:
            if tacets_idx < len(tacets) and re.search(ctx.tr(tacets[tacets_idx]), textbox.text, re.I):
                cards.append([textbox, tacets_idx, None, None, None])
                cards_idx = tacets_idx
                tacets_idx += 1
                continue
            if re.search(ctx.tr(I18nText.Go), textbox.text, re.I):
                cards[cards_idx][2] = textbox
            match = re.search(progress_pattern, textbox.text, re.I)
            logger.debug(f"match: {match}")
            if match:
                cards[cards_idx][3] = textbox
                cards[cards_idx][4] = match

        # 分组
        cards = {}
        for i, textbox in enumerate(textboxes):
            found_tacet = next((x for x in tacets if re.search(ctx.tr(x), textbox.text, re.I)), None)
            logger.debug(f"found_tacet: {found_tacet}")
            if not found_tacet:
                continue
            cur_card = [textbox, tacets.index(found_tacet), None, None, None]
            cards[found_tacet] = cur_card
            if i + 2 >= len(textboxes):
                continue
            if re.search(ctx.tr(I18nText.Go), textboxes[i + 1].text, re.I):
                cur_card[2] = textboxes[i + 1]
            match = re.search(progress_pattern, textboxes[i + 2].text, re.I)
            logger.debug(f"match: {match}")
            if match:
                cur_card[3] = textbox
                cur_card[4] = match
        logger.debug(f"cards: {cards}")

        for cur_instance, card in cards.items():
            # 跳过无法处理的空值
            if any(t is None for t in card):
                continue

            logger.debug(f"card: {card}")
            tbox, _tacets_idx, go, _progress, match = card
            cur_fsm = tacets_fsm[_tacets_idx]

            # 任务状态检查
            if cur_fsm.status.is_terminal:
                continue
            try:
                if cur_fsm.status == TaskStatus.PENDING and int(match.group(1)) == int(match.group(2)):
                    cur_fsm.start()
                    logger.info(f"{cur_fsm.name}: ⏭️ skip because: {match.group(0)}")
                    cur_fsm.complete()
                    continue
            except Exception:
                pass
            # 已在执行中，说明是第二次来，已容错一次，为防止无限循环，这次必须转成终态
            in_progress = cur_fsm.status == TaskStatus.IN_PROGRESS
            if cur_fsm.status == TaskStatus.PENDING:
                cur_fsm.start()
            logger.info(f"{cur_fsm.name}: {match.group(0)}")

            # 点击前往
            for _ in range(2):
                # 有时ui反应太慢，点快了ui没跳转，再试一次
                ui.sleep(0.4).click_bbox(go, times=2, interval=0.2)
                if ui.sleep(1).wait(3, 0.3).until(
                        lambda: not ui.snapshot().search(ctx.tr(I18nText.TacetDiscordNest), bbox_guidebook_item(ctx))):
                    break

            # 点击快速旅行
            if not ui.search(ctx.tr([I18nText.FastTravel, I18nText.EnableNavigation, I18nText.Track])):
                if not ui.wait().until(
                        lambda: ui.snapshot().search(
                            ctx.tr([I18nText.FastTravel, I18nText.EnableNavigation, I18nText.Track]))):
                    if in_progress:
                        cur_fsm.fail()
                    return False
            # 检查副本未解锁
            if ui.search(ctx.tr([I18nText.EnableNavigation, I18nText.Track])):
                logger.warning(f"Unlock instance: {ctx.tr(cur_instance).raw}")
                cur_fsm.complete()
                return True
            # 点击快速旅行
            ui.click_text(ctx.tr(I18nText.FastTravel), delay=0.2, pk=PointKind.NEAR, times=2, interval=0.3)

            if ui.sleep(2).wait_back_home():
                ui.sleep(1.0)
            else:
                return False

            # 前往战斗区域
            combat_system = CombatSystem(ctx.control_service, ctx.img_service)
            combat_system.set_resonators(local.members, is_print=False)
            combat_system.exit_special_state(Morph.Forced)
            ui.move(tacets_route[_tacets_idx]).sleep(0.3)

            if cur_instance == I18nText.SimulacrumNexusTacetDiscordNest:
                # 梦枢天罗
                # 00 10
                # 01 11
                grid = TileGrid()
                grid.add_tile(0, 0, img_util.read_img(
                    Resource.Map.Huanglong.Mengzhou.SimulacrumNexusOfMengzhou / "912_0_1.png"))
                grid.add_tile(1, 0, img_util.read_img(
                    Resource.Map.Huanglong.Mengzhou.SimulacrumNexusOfMengzhou / "912_1_1.png"))
                composite = grid.composite_region(min_x=0, min_y=0, max_x=1, max_y=0)
                tmpl_name = str(int(time.monotonic()))
                tmpl_img = composite.image
                matcher = SIFTFeatureMatcher()
                feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
                point = Point(1024 + 7, 489)
            elif cur_instance == I18nText.SouthernYuanHillsTacetDiscordNest:
                # 落渊南丘
                tmpl_name = "8_-7_1.png"
                tmpl_img = img_util.read_img(Resource.Map.Huanglong.Mengzhou.ROOT / "8_-7_1.png")
                matcher = SIFTFeatureMatcher()
                feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
                point = Point(135, 900)
            elif cur_instance == I18nText.StarblindCrashsiteTacetDiscordNest:
                # 盲望之塌
                tmpl_name = "8_-2_8.png"
                tmpl_img = img_util.read_img(file_util.get_assets_map("Roya Frostlands/Frostlands Surface/8_-2_8.png"))
                matcher = SIFTFeatureMatcher()
                feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
                point = Point(301, 194)
            elif cur_instance == I18nText.RebirthUplandsTacetDiscordNest:
                # 复生丘原
                tmpl_name = "906_-1_7.png"
                tmpl_img = img_util.read_img(file_util.get_assets_map("Roya Frostlands/Lahai-Roi/906_-1_7.png"))
                matcher = SIFTFeatureMatcher()
                feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
                point = Point(38, 335)
            elif cur_instance == I18nText.StagnantRunTacetDiscordNest:
                # 陷足流川
                tmpl_name = "906_0_6.png"
                tmpl_img = img_util.read_img(file_util.get_assets_map("Roya Frostlands/Lahai-Roi/906_0_6.png"))
                matcher = SIFTFeatureMatcher()
                feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
                point = Point(240, 138)
            else:
                raise NotImplementedError()

            # TODO 封装
            def _map_fast_travel() -> bool:
                if not ui.is_on_homepage():
                    return False
                ctx.control_service.map()
                if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(ctx.tr(I18nText.SwitchMap))):
                    ui.esc().sleep(1)
                    return False
                scene_img = ui.sleep(0.3).grap()
                result = matcher.match(scene_img, feature_data)
                if result is None:
                    logger.warning("Feature match failed")
                    ui.esc().sleep(1)
                    return False

                scene_point = matcher.feature_to_scene(result, (float(point.x), float(point.y)))
                x = int(scene_point[0])
                y = int(scene_point[1])
                logger.debug(f"模板点 {point} 映射到场景坐标: ({scene_point[0]:.1f}, {scene_point[1]:.1f})")
                ui.click(x, y)
                if not ui.sleep(0.5).wait().until(
                        lambda: ui.snapshot().click_text(
                            ctx.tr(I18nText.FastTravel), delay=0.3, times=2, interval=0.2)):
                    scene_img = ui.sleep(0.3).grap()
                    result = matcher.match(scene_img, feature_data)
                    if result is None:
                        logger.warning("Feature match failed")
                        ui.esc().sleep(1)
                        return False
                    scene_point = matcher.feature_to_scene(result, (float(point.x), float(point.y)))
                    logger.debug(f"模板点 {point} 映射到场景坐标: ({scene_point[0]:.1f}, {scene_point[1]:.1f})")
                    ui.click(int(scene_point[0]), int(scene_point[1])).sleep(0.35)
                    ctx.control_service.scroll_mouse(100, x, y)
                    ui.sleep(0.3)

                    scene_img = ui.sleep(0.3).grap()
                    result = matcher.match(scene_img, feature_data)
                    if result is None:
                        logger.warning("Feature match failed")
                        ui.esc().sleep(1)
                        return False
                    scene_point = matcher.feature_to_scene(result, (float(point.x), float(point.y)))
                    logger.debug(f"模板点 {point} 映射到场景坐标: ({scene_point[0]:.1f}, {scene_point[1]:.1f})")
                    ui.click(int(scene_point[0]), int(scene_point[1]))
                    if not ui.sleep(0.5).wait().until(
                            lambda: ui.snapshot().click_text(
                                ctx.tr(I18nText.FastTravel), delay=0.3, times=2, interval=0.2)):
                        ui.esc().sleep(1)
                        return False

                if not ui.sleep(0.5).wait_back_home():
                    return False
                ui.sleep(0.7)
                return True

            cleared_keyword = ctx.tr([
                I18nText.TacetDiscordNestCleared, I18nText.TacetDiscordNestClearedMengzhou, I18nText.RefreshesTomorrow])
            is_combat = not ui.snapshot().search(cleared_keyword)
            # 可能打着打着出了战斗区域，标识文本消失，误判已经打完，循环重置位置接着打
            max_combat_range = 3
            for k in range(max_combat_range):
                if k > 0:
                    logger.debug(f"k: {k}")
                # 没刷就打
                if is_combat:
                    combat_system = CombatSystem(ctx.control_service, ctx.img_service)
                    combat_system.set_resonators(local.members, is_print=False)
                    combat_system.is_async = True
                    combat_system.check_boss_hp = False
                    combat_system.auto_pickup = False
                    # combat_system.exit_special_state(Morph.Forced)

                    timeout = 10 * 60
                    deadline = time.monotonic() + timeout
                    no_text_max = 3
                    no_text_count = no_text_max
                    hp_roi = bbox_hp_bar(ctx).as_tuple()

                    while ui.is_set() or time.monotonic() < deadline:
                        logger.debug(f"no_text_count: {no_text_count}")
                        if no_text_count < 0:
                            break
                        combat_system.start(3.5)
                        ui.sleep(1.5)
                        ui.snapshot()
                        img = ui.img
                        if ui.is_on_homepage():
                            # 残象聚落已清理
                            logger.debug(f"result: {ui.bbox_result}")
                            if ui.search(cleared_keyword):
                                break
                            # 清理聚落中的残象
                            if ui.search(ctx.tr(
                                    [I18nText.ClearTheTacetDiscordNest, I18nText.ClearTheTacetDiscordNestMengzhou])):
                                logger.debug("战斗中")
                                no_text_count = no_text_max
                                continue
                            else:
                                logger.debug(f"Text not found: {ctx.tr(I18nText.ClearTheTacetDiscordNest).raw}")
                            # boxes = img_util.detect_hp_bar(img, hp_roi)
                            # if boxes:
                            #     logger.debug("有血条，还在战斗中")
                            #     no_text_count = no_text_max
                            #     if logger.isEnabledFor(logging.DEBUG):
                            #         img_draw = img_util.draw_detect_hp_bar(img, boxes)
                            #         img_util.save_img_in_temp(img_draw)
                            #     continue
                            no_text_count -= 1

                        if page_key := GlobalPage(ctx).action(ui=ui):
                            if page_key == GlobalPage.InternetDisconnecting:
                                combat_system.stop(join=True)
                                return False

                    combat_system.stop(join=True)
                    # 检查复苏弹窗
                    if ui.sleep(0.5).snapshot().search(ctx.tr(I18nText.SelectARevivalItem)):
                        ui.esc().sleep(0.5)
                    combat_system.exit_special_state(Morph.Prefer)
                    ui.sleep(0.3)

                    ctx.control_service.camera_reset()
                    ui.sleep(0.5)

                    # # 声骸刚好掉在脚下，直接吸收结束，不用后续操作
                    # if ui.search(ctx.tr(I18nText.Absorb), bbox_dialogue(ctx)):
                    #     logger.info("Tacet Discord Nest Cleared")
                    #     ui.pick_up(2, 0.2)
                    #     cur_fsm.complete()
                    #     return True
                    ui.pick_up(2, 0.2).sleep(0.2)

                    # 重置位置
                    if not _map_fast_travel():
                        # 原地传送失败就结束
                        if in_progress:
                            # 没找到吸收，再次来不管怎样都结束掉
                            cur_fsm.complete()
                        return True
                    # 前往战斗区域
                    with AsyncPickup(ctx, delay=1.0):
                        ui.move(tacets_route[_tacets_idx])
                    ui.sleep(0.3)

                    is_combat = not ui.snapshot().search(cleared_keyword)
                    if k == max_combat_range - 1:
                        # 打了几回都没打完，重新来
                        if in_progress:
                            break
                        return True
                    continue
                # else:
                #     ctx.control_service.camera_reset()
                #     ui.sleep(0.5)
                #     logger.info("Tacet Discord Nest Cleared")
                #
                #     # 声骸刚好掉在脚下，直接吸收结束，不用后续操作
                #     if ui.search(ctx.tr(I18nText.Absorb), bbox_dialogue(ctx)):
                #         ui.pick_up(2, 0.2)
                #         cur_fsm.complete()
                #         return True
                #     break

            # 吸收
            absorb_around_variant_blind(ctx)
            # 不管怎样都结束掉
            cur_fsm.complete()
            return True

        # 标记剩余待完成的任务为失败
        pending = 0
        for fsm in tacets_fsm:
            if fsm.status != TaskStatus.PENDING:
                continue
            if pending == 0:
                logger.info("Marking remaining subtask as failed")
            pending += 1
            fsm.start()
            fsm.fail()

        return pending == 0
    except (KeyboardInterrupt, StopError) as e:
        raise e
    except Exception as e:
        logger.exception(e)

    for fsm in tacets_fsm:
        if fsm.status == TaskStatus.PENDING:
            fsm.start()
            fsm.fail()
        elif fsm.status in [TaskStatus.IN_PROGRESS, TaskStatus.WAITING]:
            fsm.fail()

    return False


@node(NodeName.doMail)
def doMail(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.mailFSM.is_terminal:
        return True
    if local.mailFSM.status == TaskStatus.PENDING:
        local.mailFSM.start()

    ui = UIOp(ctx)

    # 进入邮件
    if ui.is_on_homepage():
        ctx.control_service.mail()
    elif GlobalPage(ctx).isTerminal(ui=ui.snapshot()):
        ui.click_point(AnchorPoint(822, 691, Align.Right | Align.Bottom))
    else:
        ctx.control_service.mail()

    def _waitClaimAll():
        if ui.search(ctx.tr(I18nText.NoMailToClaim)):
            return True
        if not ui.snapshot().click_text(ctx.tr(I18nText.MailClaimAll), delay=0.3):
            return False

        def _waitItemsObtained():
            if ui.snapshot().click_text(ctx.tr(I18nText.ItemsObtained)):
                ui.sleep(0.3)
                return True
            return ui.search(ctx.tr(I18nText.MailClaimAll))

        ui.sleep(1).wait(2, 0.3).until(_waitItemsObtained)
        return True

    if not ui.sleep(0.5).wait().until(_waitClaimAll):
        logger.warning(f"Text not found: {ctx.tr(I18nText.MailClaimAll).raw}")
        local.mailFSM.fail()
        return False

    local.mailFSM.complete()
    ui.esc().sleep(1)
    return True


@node(NodeName.doPioneerPodcast)
def doPioneerPodcast(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.pioneerPodcastFSM.is_terminal:
        return True
    if local.pioneerPodcastFSM.status == TaskStatus.PENDING:
        local.pioneerPodcastFSM.start()

    ui = UIOp(ctx)
    pioneerPodcast = ctx.tr(I18nText.PioneerPodcast)
    podcastTasks = ctx.tr(I18nText.PodcastTasks)

    # 从终端进入先约电台，不用快捷键
    if ui.is_on_homepage():
        ui.esc().sleep(1.0)
        if not ui.wait().until(lambda: GlobalPage(ctx).isTerminal(ui=ui.snapshot())):
            return False
    elif not GlobalPage(ctx).isTerminal(ui=ui.snapshot()):
        return False
    if not ui.click_text(ctx.tr(I18nText.TerminalPioneerPodcast),
                         bbox_terminal_content(ctx), pk=PointKind.NEAR, times=2, interval=0.2):
        return False

    pioneerPodcastUnavailable = ctx.tr(I18nText.PioneerPodcastUnavailable)
    maxLevelReached = ctx.tr(I18nText.MaxLevelReached)
    if not ui.sleep(1.2).wait().until(
            lambda: ui.snapshot().search([pioneerPodcast, pioneerPodcastUnavailable, maxLevelReached])):
        return False
    if ui.search([pioneerPodcastUnavailable, maxLevelReached]):
        local.pioneerPodcastFSM.complete()
        ui.sleep(0.3).esc().sleep(1)
        return True

    sidebarsPioneerPodcast = ctx.scaler.as_point(AnchorPoint(50, 126, Align.Left | Align.Top))
    sidebarsPodcastTasks = ctx.scaler.as_point(AnchorPoint(50, 213, Align.Left | Align.Top))
    # 提示种类很多
    confirm = ctx.tr([
        I18nText.TapTheBlankAreaToClose,
        I18nText.TapTheBlankAreaToContinue,
        I18nText.PioneerPodcastConfirm,
        I18nText.Confirm,
    ])

    def _closePodcastTasksNotice():
        ui.snapshot()
        # 可能弹窗获得奖励，需要点确定才关闭
        if ui.click_text(confirm, times=2, interval=0.2):
            return False
        # 可能提示获得电台经验，切到电台任务页，能过去说明提示已消失
        if ui.search(pioneerPodcast):
            return True
        ui.click_point(sidebarsPioneerPodcast, times=2, interval=0.2)
        return False

    # 先点电台任务
    ui.sleep(0.3).click_point(sidebarsPodcastTasks, times=2, interval=0.2)
    if ui.sleep(0.3).wait().until(lambda: ui.snapshot().search(podcastTasks)):
        if ui.sleep(0.2).snapshot().click_text(
                ctx.tr(I18nText.PioneerPodcastClaimAll), delay=0.2, times=2, interval=0.2):
            ui.sleep(1.5).wait().until(_closePodcastTasksNotice)

    # 再点先约电台
    ui.sleep(0.3).click_point(sidebarsPioneerPodcast, times=2, interval=0.2)
    if ui.sleep(0.3).wait().until(lambda: ui.snapshot().search(pioneerPodcast)):
        if ui.sleep(0.2).snapshot().click_text(ctx.tr(I18nText.PioneerPodcastClaimAll), times=2, interval=0.2):
            ui.sleep(2).wait(3, 0.3).until(lambda: ui.snapshot().click_text(confirm, delay=0.2, times=2, interval=0.2))

    local.pioneerPodcastFSM.complete()
    ui.sleep(0.3).esc().sleep(1)
    return True


class DailyWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name="DailyWorkflow")
        self.local = TaskLocal()

        self.__init_task_local()
        self.__init_workflow()

    def execute(self, **kwargs):
        try:
            logger.debug(f"task: {self.__class__.__name__}")
            self.ctx.runtime.taskFSM = self.fsm
            self.fsm.start()
            self.ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
            self.ctx.control_service.activate()
            time.sleep(0.1)
            self.engine.run(self, local=self.local, **kwargs)
        except Exception as e:
            raise e

    def __init_task_local(self):
        """根据配置初始化任务状态"""
        cfg = self.ctx.runtime.cfg.daily
        logger.debug(f"cfg: {cfg}")

        # ------- Root -------
        self.local.rootFSM.set_enabled(True)

        self.local.teamFSM.set_enabled(True)
        self.local.guidebookFSM.set_enabled(True)
        self.local.mailFSM.set_enabled(cfg.mailOpen)
        self.local.pioneerPodcastFSM.set_enabled(cfg.pioneerPodcastOpen)

        # ------- Guidebook -------
        self.local.activityFSM.set_enabled(True)
        self.local.materialCollectionFSM.set_enabled(True)
        self.local.recurringChallengesFSM.set_enabled(False)
        self.local.pathOfGrowthFSM.set_enabled(False)
        self.local.enemyTracingFSM.set_enabled(False)
        self.local.milestonesFSM.set_enabled(False)

        ## ------- Guidebook Activity -------
        self.local.activityDailyFSM.set_enabled(cfg.activityOpen)
        self.local.activityWeeklyFSM.set_enabled(cfg.activityOpen and cfg.activityWeeklyOpen)

        ## ------- Guidebook MaterialCollection -------
        self.local.forgeryChallengeFSM.set_enabled(cfg.forgeryChallengeOpen and cfg.forgeryChallenge)
        self.local.simulationChallengeFSM.set_enabled(cfg.simulationChallengeOpen and cfg.simulationChallenge)
        self.local.bossChallengeFSM.set_enabled(cfg.bossChallengeOpen and cfg.bossChallenge)
        self.local.tacetSuppressionFSM.set_enabled(cfg.tacetSuppressionOpen and cfg.tacetSuppression)
        self.local.weeklyChallengeFSM.set_enabled(cfg.weeklyChallengeOpen and cfg.weeklyChallenge)
        self.local.nightmarePurificationFSM.set_enabled(cfg.nightmarePurificationOpen and cfg.nightmarePurification)
        self.local.tacetDiscordNestFSM.set_enabled(cfg.tacetDiscordNestOpen and cfg.tacetDiscordNest)

        ## ------- Guidebook RecurringChallenges -------

        ## ------- Guidebook PathOfGrowth -------

        ### ------- Guidebook MaterialCollection ForgeryChallenge -------
        self.local.wingfallChasmFSM.set_enabled(cfg.wingfallChasm)
        self.local.silentChasmFSM.set_enabled(cfg.silentChasm)
        self.local.splitChasmFSM.set_enabled(cfg.splitChasm)
        self.local.erodedChasmFSM.set_enabled(cfg.erodedChasm)
        self.local.ashenChasmFSM.set_enabled(cfg.ashenChasm)
        self.local.fallenSanctumFSM.set_enabled(cfg.fallenSanctum)
        self.local.lessonInSunsetFSM.set_enabled(cfg.lessonInSunset)
        self.local.strickenSanctumFSM.set_enabled(cfg.strickenSanctum)
        self.local.lessonInVoidFSM.set_enabled(cfg.lessonInVoid)
        self.local.lessonInEmbersFSM.set_enabled(cfg.lessonInEmbers)
        self.local.gardenOfSalvationFSM.set_enabled(cfg.gardenOfSalvation)
        self.local.abyssOfInitiationFSM.set_enabled(cfg.abyssOfInitiation)
        self.local.gardenOfAdorationFSM.set_enabled(cfg.gardenOfAdoration)
        self.local.abyssOfSacrificeFSM.set_enabled(cfg.abyssOfSacrifice)
        self.local.abyssOfConfessionFSM.set_enabled(cfg.abyssOfConfession)
        self.local.flamingRemnantsFSM.set_enabled(cfg.flamingRemnants)
        self.local.mistyForestFSM.set_enabled(cfg.mistyForest)
        self.local.erodedRuinsFSM.set_enabled(cfg.erodedRuins)
        self.local.moonlitGrovesFSM.set_enabled(cfg.moonlitGroves)
        self.local.marigoldWoodsFSM.set_enabled(cfg.marigoldWoods)

        ### ------- Guidebook MaterialCollection SimulationChallenge -------

        ### ------- Guidebook MaterialCollection BossChallenge -------
        self.local.enemyCalamityEffigyFSM.set_enabled(cfg.enemyCalamityEffigy)
        self.local.enemyMyriadSnareRustfireChassisFSM.set_enabled(cfg.enemyMyriadSnareRustfireChassis)
        self.local.enemyNightmareAdamSmasherFSM.set_enabled(cfg.enemyNightmareAdamSmasher)
        self.local.enemyNamelessExplorerFSM.set_enabled(cfg.enemyNamelessExplorer)
        self.local.enemyHyvatiaFSM.set_enabled(cfg.enemyHyvatia)
        self.local.enemyReactorHuskFSM.set_enabled(cfg.enemyReactorHusk)
        self.local.enemyLadyOfTheSeaFSM.set_enabled(cfg.enemyLadyOfTheSea)
        self.local.enemyTheFalseSovereignFSM.set_enabled(cfg.enemyTheFalseSovereign)
        self.local.enemyFenricoFSM.set_enabled(cfg.enemyFenrico)
        self.local.enemyLionessOfGloryFSM.set_enabled(cfg.enemyLionessOfGlory)
        self.local.enemyDragonOfDirgeFSM.set_enabled(cfg.enemyDragonOfDirge)
        self.local.enemyLoreleiFSM.set_enabled(cfg.enemyLorelei)
        self.local.enemySentryConstructFSM.set_enabled(cfg.enemySentryConstruct)
        self.local.enemyFallacyOfNoReturnFSM.set_enabled(cfg.enemyFallacyOfNoReturn)
        self.local.enemyCrownlessFSM.set_enabled(cfg.enemyCrownless)
        self.local.enemyFeilianBeringalFSM.set_enabled(cfg.enemyFeilianBeringal)
        self.local.enemyTempestMephisFSM.set_enabled(cfg.enemyTempestMephis)
        self.local.enemyThunderingMephisFSM.set_enabled(cfg.enemyThunderingMephis)
        self.local.enemyMourningAixFSM.set_enabled(cfg.enemyMourningAix)
        self.local.enemyMechAbominationFSM.set_enabled(cfg.enemyMechAbomination)
        self.local.enemyImpermanenceHeronFSM.set_enabled(cfg.enemyImpermanenceHeron)
        self.local.enemyInfernoRiderFSM.set_enabled(cfg.enemyInfernoRider)
        self.local.enemyLampylumenMyriadFSM.set_enabled(cfg.enemyLampylumenMyriad)

        ### ------- Guidebook MaterialCollection TacetSuppression -------
        self.local.tacetFieldHeartOfStillnessFSM.set_enabled(cfg.tacetFieldHeartOfStillness)
        self.local.tacetFieldHeartOfFlamesFSM.set_enabled(cfg.tacetFieldHeartOfFlames)
        self.local.westernFangPeaksTacetFieldFSM.set_enabled(cfg.westernFangPeaksTacetField)
        self.local.easternXuanPeaksTacetFieldFSM.set_enabled(cfg.easternXuanPeaksTacetField)
        self.local.tacetFieldSolisiaLandingFSM.set_enabled(cfg.tacetFieldSolisiaLanding)
        self.local.tacetFieldFrostlandsTransitPortFSM.set_enabled(cfg.tacetFieldFrostlandsTransitPort)
        self.local.tacetFieldMountGjallarFSM.set_enabled(cfg.tacetFieldMountGjallar)
        self.local.tacetFieldMawburrowDesertFSM.set_enabled(cfg.tacetFieldMawburrowDesert)
        self.local.tacetFieldStagnantRunFSM.set_enabled(cfg.tacetFieldStagnantRun)
        self.local.tacetFieldMournfellCanyonFSM.set_enabled(cfg.tacetFieldMournfellCanyon)
        self.local.tacetFieldBeohrWatersFSM.set_enabled(cfg.tacetFieldBeohrWaters)
        self.local.tacetFieldRiccioliIslandsFSM.set_enabled(cfg.tacetFieldRiccioliIslands)
        self.local.tacetFieldFagaceaePeninsulaFSM.set_enabled(cfg.tacetFieldFagaceaePeninsula)
        self.local.tacetFieldPenitentsEndFSM.set_enabled(cfg.tacetFieldPenitentsEnd)
        self.local.tacetFieldCentralPlainsFSM.set_enabled(cfg.tacetFieldCentralPlains)
        self.local.tacetFieldDesorockHighlandIFSM.set_enabled(cfg.tacetFieldDesorockHighlandI)
        self.local.tacetFieldTigersMawFSM.set_enabled(cfg.tacetFieldTigersMaw)
        self.local.tacetFieldWhiningAixsMireFSM.set_enabled(cfg.tacetFieldWhiningAixsMire)
        self.local.tacetFieldPortCityOfGuixuFSM.set_enabled(cfg.tacetFieldPortCityOfGuixu)
        self.local.tacetFieldDesorockHighlandIIFSM.set_enabled(cfg.tacetFieldDesorockHighlandII)
        self.local.tacetFieldDimForestFSM.set_enabled(cfg.tacetFieldDimForest)

        ### ------- Guidebook MaterialCollection WeeklyChallenge -------
        self.local.ordinanceOfTheInevitableFSM.set_enabled(cfg.ordinanceOfTheInevitable)
        self.local.courtOfShackledSoulsFSM.set_enabled(cfg.courtOfShackledSouls)
        self.local.seedOfIllusoryOriginFSM.set_enabled(cfg.seedOfIllusoryOrigin)
        self.local.gateOfTheLostStarFSM.set_enabled(cfg.gateOfTheLostStar)
        self.local.cinderniteApocalypseFSM.set_enabled(cfg.cinderniteApocalypse)
        self.local.theWheelOfBrokenFateFSM.set_enabled(cfg.theWheelOfBrokenFate)
        self.local.beyondTheCrimsonCurtainFSM.set_enabled(cfg.beyondTheCrimsonCurtain)
        self.local.theFatedConfrontationFSM.set_enabled(cfg.theFatedConfrontation)
        self.local.statueOfTheCrownlessFSM.set_enabled(cfg.statueOfTheCrownless)
        self.local.chaoticJunctureFSM.set_enabled(cfg.chaoticJuncture)
        self.local.bellOfArchaicChantsFSM.set_enabled(cfg.bellOfArchaicChants)

        ### ------- Guidebook MaterialCollection NightmarePurification -------

        ### ------- Guidebook MaterialCollection TacetDiscordNest -------

        ### ------- Guidebook MaterialCollection tacetDiscordNest -------
        self.local.simulacrumNexusTacetDiscordNestFSM.set_enabled(cfg.simulacrumNexusTacetDiscordNest)
        self.local.southernYuanHillsTacetDiscordNestFSM.set_enabled(cfg.southernYuanHillsTacetDiscordNest)
        self.local.starblindCrashsiteTacetDiscordNestFSM.set_enabled(cfg.starblindCrashsiteTacetDiscordNest)
        self.local.rebirthUplandsTacetDiscordNestFSM.set_enabled(cfg.rebirthUplandsTacetDiscordNest)
        self.local.stagnantRunTacetDiscordNestFSM.set_enabled(cfg.stagnantRunTacetDiscordNest)

        # ---------------------------------------------------------------

        # ------- DoubleDrop -------
        self.local.doubleDropForgeryChallengeFSM.set_enabled(True)
        self.local.doubleDropSimulationChallengeFSM.set_enabled(True)
        self.local.doubleDropTacetSuppressionFSM.set_enabled(True)

        if not self.local.rootFSM.is_active:
            logger.warning('Task is not active')

    def __init_workflow(self):
        # TODO 事件循环？
        # TODO 根据体力（180）动态策略？
        # TODO DAG自检、预览
        (
            self.engine.source(NodeName.globalDispatcher, is_start=True)
            .on(I18nText.Terminal).to(NodeName.rootDispatcher)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.rootDispatcher)
            .on(I18nText.Team).to(NodeName.doTeam)
            .on(I18nText.Guidebook).to(NodeName.doGuidebook)
            .on(I18nText.Mail).to(NodeName.doMail)
            .on(I18nText.TerminalPioneerPodcast).to(NodeName.doPioneerPodcast)
            .always().to(NodeName.endNode)
        )

        (
            self.engine.source(NodeName.doTeam)
            .on(False).to(NodeName.doTravelToResonanceNexus)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doTravelToResonanceNexus)
            .on(True).to(NodeName.globalDispatcher)
            .always().to(NodeName.endNode)
        )

        (
            self.engine.source(NodeName.doGuidebook)
            .on(I18nText.Activity).to(NodeName.doActivity)
            .on(I18nText.MaterialCollection).to(NodeName.doMaterialCollection)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doActivity)
            .on(I18nText.ActivityDaily).to(NodeName.doActivityDaily)
            .on(I18nText.ActivityWeekly).to(NodeName.doActivityWeekly)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.source(NodeName.doActivityDaily).always().to(NodeName.globalDispatcher)
        (
            self.engine.source(NodeName.doActivityWeekly)
            .on(False).to(NodeName.doPhantasmaDreamlandRhapsody)
            .always().to(NodeName.doActivity)
        )
        self.engine.source(NodeName.doPhantasmaDreamlandRhapsody).always().to(NodeName.globalDispatcher)

        (
            self.engine.source(NodeName.doMaterialCollection)
            .on(I18nText.ForgeryChallenge).to(NodeName.doForgeryChallenge)
            .on(I18nText.SimulationChallenge).to(NodeName.doSimulationChallenge)
            .on(I18nText.BossChallenge).to(NodeName.doBossChallenge)
            .on(I18nText.TacetSuppression).to(NodeName.doTacetSuppression)
            .on(I18nText.WeeklyChallenge).to(NodeName.doWeeklyChallenge)
            .on(I18nText.NightmarePurification).to(NodeName.doNightmarePurification)
            .on(I18nText.TacetDiscordNest).to(NodeName.doTacetDiscordNest)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.source(NodeName.doForgeryChallenge).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doSimulationChallenge).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doBossChallenge).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doTacetSuppression).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doWeeklyChallenge).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doNightmarePurification).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doTacetDiscordNest).always().to(NodeName.globalDispatcher)

        self.engine.source(NodeName.doMail).always().to(NodeName.globalDispatcher)
        self.engine.source(NodeName.doPioneerPodcast).always().to(NodeName.globalDispatcher)

        self.engine.exception(NodeName.endNode)
