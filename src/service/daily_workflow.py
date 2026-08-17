import logging
import random
import re
import time
from typing import Optional

from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import ResonatorNameEnum, Morph
from src.core.combat.combat_system import CombatSystem
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, Point
from src.core.i18n import I18nText, Language, I18nTr
from src.core.message import MsgType, MsgTaskStatus, MsgSource
from src.core.movement import Run, Walk
from src.core.pages import UIOp, GlobalPage
from src.core.resonator import Resonator
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import (
    absorb_around_variant_blind, bbox_terminal_content, bbox_guidebook_content, move_and_scan_dialogue,
    match_remaining_attempts, linear_spacing, query_waveplate_guidebook, query_waveplate_claim_rewards,
    object_detection, bbox_hp_bar, bbox_guidebook_item, search_icon_materials_spots, bbox_dialogue,
    bbox_guidebook_title, AsyncPickup,
)
from src.util import img_util, file_util
from src.util.img_sift_util import SIFTFeatureMatcher
from src.util.img_tile_util import TileGrid

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        ### ------- Guidebook MaterialsSpots ForgeryChallenge -------
        self.wingfallChasmFSM: TaskFSM = TaskFSM(name=I18nText.WingfallChasm)
        self.silentChasmFSM: TaskFSM = TaskFSM(name=I18nText.SilentChasm)
        self.splitChasmFSM: TaskFSM = TaskFSM(name=I18nText.SplitChasm)
        self.erodedChasmFSM: TaskFSM = TaskFSM(name=I18nText.ErodedChasm)
        self.ashenChasmFSM: TaskFSM = TaskFSM(name=I18nText.AshenChasm)
        self.fallenSanctumFSM: TaskFSM = TaskFSM(name=I18nText.FallenSanctum)
        self.lessonInSunsetFSM: TaskFSM = TaskFSM(name=I18nText.LessonInSunset)
        self.strickenSanctumFSM: TaskFSM = TaskFSM(name=I18nText.StrickenSanctum)
        self.lessonInVoidFSM: TaskFSM = TaskFSM(name=I18nText.LessonInVoid)
        self.lessonInEmbersFSM: TaskFSM = TaskFSM(name=I18nText.LessonInEmbers)
        self.gardenOfSalvationFSM: TaskFSM = TaskFSM(name=I18nText.GardenOfSalvation)
        self.abyssOfInitiationFSM: TaskFSM = TaskFSM(name=I18nText.AbyssOfInitiation)
        self.gardenOfAdorationFSM: TaskFSM = TaskFSM(name=I18nText.GardenOfAdoration)
        self.abyssOfSacrificeFSM: TaskFSM = TaskFSM(name=I18nText.AbyssOfSacrifice)
        self.abyssOfConfessionFSM: TaskFSM = TaskFSM(name=I18nText.AbyssOfConfession)
        self.flamingRemnantsFSM: TaskFSM = TaskFSM(name=I18nText.FlamingRemnants)
        self.mistyForestFSM: TaskFSM = TaskFSM(name=I18nText.MistyForest)
        self.erodedRuinsFSM: TaskFSM = TaskFSM(name=I18nText.ErodedRuins)
        self.moonlitGrovesFSM: TaskFSM = TaskFSM(name=I18nText.MoonlitGroves)
        self.marigoldWoodsFSM: TaskFSM = TaskFSM(name=I18nText.MarigoldWoods)

        ### ------- Guidebook MaterialsSpots SimulationChallenge -------

        ### ------- Guidebook MaterialsSpots BossChallenge -------

        ### ------- Guidebook MaterialsSpots TacetSuppression -------
        self.westernFangPeaksTacetFieldFSM: TaskFSM = TaskFSM(name=I18nText.WesternFangPeaksTacetField)
        self.easternXuanPeaksTacetFieldFSM: TaskFSM = TaskFSM(name=I18nText.EasternXuanPeaksTacetField)
        self.tacetFieldSolisiaLandingFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldSolisiaLanding)
        self.tacetFieldFrostlandsTransitPortFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldFrostlandsTransitPort)
        self.tacetFieldMountGjallarFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldMountGjallar)
        self.tacetFieldMawburrowDesertFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldMawburrowDesert)
        self.tacetFieldStagnantRunFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldStagnantRun)

        ### ------- Guidebook MaterialsSpots WeeklyChallenge -------
        self.courtOfShackledSoulsFSM: TaskFSM = TaskFSM(name=I18nText.CourtOfShackledSouls)
        self.seedOfIllusoryOriginFSM: TaskFSM = TaskFSM(name=I18nText.SeedOfIllusoryOrigin)
        self.gateOfTheLostStarFSM: TaskFSM = TaskFSM(name=I18nText.GateOfTheLostStar)
        self.cinderniteApocalypseFSM: TaskFSM = TaskFSM(name=I18nText.CinderniteApocalypse)
        self.theWheelOfBrokenFateFSM: TaskFSM = TaskFSM(name=I18nText.TheWheelOfBrokenFate)
        self.beyondTheCrimsonCurtainFSM: TaskFSM = TaskFSM(name=I18nText.BeyondTheCrimsonCurtain)
        self.theFatedConfrontationFSM: TaskFSM = TaskFSM(name=I18nText.TheFatedConfrontation)
        self.statueOfTheCrownlessFSM: TaskFSM = TaskFSM(name=I18nText.StatueOfTheCrownless)
        self.chaoticJunctureFSM: TaskFSM = TaskFSM(name=I18nText.ChaoticJuncture)
        self.bellOfArchaicChantsFSM: TaskFSM = TaskFSM(name=I18nText.BellOfArchaicChants)

        ### ------- Guidebook MaterialsSpots NightmarePurification -------

        ### ------- Guidebook MaterialsSpots TacetDiscordNest -------
        self.southernYuanHillsTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.SouthernYuanHillsTacetDiscordNest)
        self.starblindCrashsiteTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.StarblindCrashsiteTacetDiscordNest)
        self.rebirthUplandsTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.RebirthUplandsTacetDiscordNest)
        self.stagnantRunTacetDiscordNestFSM: TaskFSM = TaskFSM(name=I18nText.StagnantRunTacetDiscordNest)

        ## ------- Guidebook Activity -------
        self.activityDailyFSM: TaskFSM = TaskFSM(name=I18nText.ActivityDaily)
        self.activityWeeklyFSM: TaskFSM = TaskFSM(name=I18nText.ActivityWeekly)

        ## ------- Guidebook MaterialsSpots -------
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
        self.simulationChallengeFSM: TaskFSMGroup = TaskFSMGroup(name="SimulationChallenge")
        self.bossChallengeFSM: TaskFSMGroup = TaskFSMGroup(name=I18nText.BossChallenge)
        self.tacetSuppressionFSM: TaskFSMGroup = TaskFSMGroup(
            self.westernFangPeaksTacetFieldFSM,
            self.easternXuanPeaksTacetFieldFSM,
            self.tacetFieldSolisiaLandingFSM,
            self.tacetFieldFrostlandsTransitPortFSM,
            self.tacetFieldMountGjallarFSM,
            self.tacetFieldMawburrowDesertFSM,
            self.tacetFieldStagnantRunFSM,
            name=I18nText.TacetSuppression
        )
        self.weeklyChallengeFSM: TaskFSMGroup = TaskFSMGroup(
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
        self.materialsSpotsFSM: TaskFSMGroup = TaskFSMGroup(
            self.forgeryChallengeFSM,
            self.simulationChallengeFSM,
            self.bossChallengeFSM,
            self.tacetSuppressionFSM,
            self.weeklyChallengeFSM,
            self.nightmarePurificationFSM,
            self.tacetDiscordNestFSM,
            name=I18nText.MaterialsSpots
        )
        self.recurringChallengesFSM: TaskFSMGroup = TaskFSMGroup(name="RecurringChallenges")
        self.pathOfGrowthFSM: TaskFSMGroup = TaskFSMGroup(name="PathOfGrowth")
        self.enemyTracingFSM: TaskFSMGroup = TaskFSMGroup(name="EnemyTracing")
        self.milestonesFSM: TaskFSMGroup = TaskFSMGroup(name="Milestones")

        # ------- Root -------
        self.guidebookFSM: TaskFSMGroup = TaskFSMGroup(
            self.activityFSM,
            self.materialsSpotsFSM,
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
    doMaterialsSpots = "doMaterialsSpots"
    doRecurringChallenges = "doRecurringChallenges"
    doPathOfGrowth = "doPathOfGrowth"
    doEnemyTracing = "doEnemyTracing"
    doMilestones = "doMilestones"

    # doActivity
    doActivityDaily = "doActivityDaily"
    doActivityWeekly = "doActivityWeekly"
    doPhantasmaDreamlandRhapsody = "doPhantasmaDreamlandRhapsody"

    # doMaterialsSpots
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
        logger.debug(f"Found page: {page.Terminal}")
        return I18nText.Terminal

    # 在全局预设中找出离开函数，尝试回到主页
    if page_key := page.action(ui=ui):
        logger.debug(f"Found page: {page_key}")
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
        if not ui.click_text(ctx.tr(I18nText.Map), bbox_terminal_content(ctx), delay=0.2, times=2, interval=0.3):
            ui.click_point(AnchorPoint(1197, 350, Align.Right | Align.Middle))
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.Map), delay=0.3, times=2, interval=0.3)):
                ui.esc().sleep(1)
                return False
    else:
        # 大世界进入地图
        ctx.control_service.map()
    # 点击切换地图
    if not ui.sleep(0.5).wait(10, 0.4).until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.SwitchMap), delay=0.8)):
        return False

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
        if ui.search(ctx.tr(I18nText.Mengzhou)) or ui.search(ctx.tr(I18nText.Jinzhou)):
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
    tmpl_img = img_util.read_img(file_util.get_assets_map("Huanglong/Jinzhou/8_0_-1.png"))
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
        logger.warning(f"Text not found: {ctx.tr(I18nText.Terminal)}")
        ui.esc().sleep(1)
        return None

    # 点击进入编队
    if not ui.click_text(ctx.tr(I18nText.Team), bbox_terminal_content(ctx), pk=PointKind.NEAR, times=2, interval=0.2):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Team).raw}")
        return False

    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(700, 625, Align.Right | Align.Bottom),
        AnchorPoint(1280, 720, Align.Right | Align.Bottom)
    ))
    if ui.sleep(0.8).wait(5, 0.5).until(
            lambda: ui.snapshot().search(
                ctx.tr([I18nText.QuickSetup, I18nText.CannotPerformThisActionDuringBattle]))):
        if ui.search(ctx.tr(I18nText.CannotPerformThisActionDuringBattle)):
            logger.info(f"Team locked")
            return False
        if not ui.search(ctx.tr(I18nText.QuickSetup), roi):
            logger.info(f"Team locked")
            return False

    # 检查失去意识
    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top),
        AnchorPoint(1280, 450, Align.Right | Align.Middle)
    ))
    result = ui.search(ctx.tr(I18nText.ResonatorDowned), roi)
    if result:
        logger.info(f"resonator downed: {len(result)}")
        if ui.esc().sleep(0.5).wait_back_home():
            ui.sleep(0.3)
        return False

    # 匹配编队角色名
    img = ui.img

    # 识别编队
    members_info: list[list] = [
        # 三个元素分别是：name、text、is_exist
        [None, None, None], [None, None, None], [None, None, None]
    ]
    team_members = [ResonatorNameEnum.none.value for _ in range(3)]

    # 编队角色名右侧一点黑色背景上取点
    member_points = [
        AnchorPoint(433, 569, Align.Center | Align.Middle),
        AnchorPoint(810, 569, Align.Center | Align.Middle),
        AnchorPoint(1187, 569, Align.Center | Align.Middle),
    ]
    member_boxes = [
        AnchorBBox(
            AnchorPoint(200, 550, Align.Center | Align.Middle),
            AnchorPoint(510, 590, Align.Center | Align.Middle),
        ),
        AnchorBBox(
            AnchorPoint(576, 550, Align.Center | Align.Middle),
            AnchorPoint(888, 590, Align.Center | Align.Middle),
        ),
        AnchorBBox(
            AnchorPoint(954, 550, Align.Center | Align.Middle),
            AnchorPoint(1280, 590, Align.Center | Align.Middle),
        ),
    ]
    member_points = [ctx.scaler.as_point(p) for p in member_points]
    member_boxes = [ctx.scaler.as_bbox(box) for box in member_boxes]

    color_matches = []
    for p in member_points:
        rule = ColorRule().points(p).colors(Color.bgr(22, 18, 13), 30)
        color_matches.append(ColorMatch(ctx.scaler).rules(rule))

    for i, match in enumerate(color_matches):
        if match.match(img):
            members_info[i][2] = True

    keys = Resonator.i18n_keys()
    lang = ctx.window_service.get_lang()

    for text_box in ui.bbox_result:
        if text_box.x2 < member_boxes[0].x1:
            continue
        if text_box.y2 < member_boxes[0].y1 or text_box.y2 > member_boxes[0].y2:
            continue
        for i, member_bbox in enumerate(member_boxes):
            if not member_bbox.contains_bbox(text_box):
                continue
            if not members_info[i][2]:
                continue
            members_info[i][1] = text_box
            if lang == Language.ZH:
                # 通过名称匹配这个位置的角色名
                enum_obj = ResonatorNameEnum.get_enum_by_ocr_text(text_box.text)
                # 角色名都对不上，默认为主角
                members_info[i][0] = enum_obj.value if enum_obj else ResonatorNameEnum.rover.value
                team_members[i] = members_info[i][0]
            elif lang == Language.EN:
                key = next((k for k in keys if ui.match_key(k, text_box.text)), None)
                if not key:
                    key = I18nText.Rover
                members_info[i][0] = I18nTr(Language.ZH)(key).raw
                team_members[i] = members_info[i][0]

            else:
                raise NotImplementedError()
            # logger.debug(f"team_members[{i}]: {team_members[i]}")

    # logger.debug(f"members_info: {members_info}")
    logger.info(f"team members: {team_members}")

    ui.esc().sleep(1)
    if not any(team_members):  # 兜底，留一个角色，至少能动
        team_members = ["unknown", None, None]
        logger.info(f"reset team members: {team_members}")
    local.teamFSM.complete()
    ctx.shared.team_members = team_members
    # ctx.shared.team_members = ["今汐", "长离", "守岸人"]

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
    materialsSpotsSidebar = [
        AnchorPoint(50, 218, Align.Top | Align.Left),
        AnchorPoint(50, 308, Align.Top | Align.Left),
    ]
    recurringChallengesSidebar = AnchorPoint(50, 308, Align.Top | Align.Left)
    pathOfGrowthSidebar = AnchorPoint(50, 396, Align.Top | Align.Left)
    enemyTracingSidebar = [
        AnchorPoint(50, 487, Align.Top | Align.Left),
        AnchorPoint(50, 578, Align.Top | Align.Left),
        AnchorPoint(50, 396, Align.Top | Align.Left),
    ]
    milestonesSidebar = AnchorPoint(50, 578, Align.Top | Align.Left)

    # 进入索拉指南后，默认是 活跃度 或 素材获取页
    activity = ctx.tr(I18nText.Activity)
    materialsSpots = ctx.tr(I18nText.MaterialsSpots)
    recurringChallenges = ctx.tr(I18nText.RecurringChallenges)
    pathOfGrowth = ctx.tr(I18nText.PathOfGrowth)
    enemyTracing = ctx.tr(I18nText.EnemyTracing)
    milestones = ctx.tr(I18nText.Milestones)

    titles = [activity, materialsSpots, recurringChallenges, pathOfGrowth, enemyTracing, milestones]
    title_roi = bbox_guidebook_title(ctx)

    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(titles, title_roi)):
        logger.warning(f"Page not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    # 根据任务的开启状态分发任务
    if local.materialsSpotsFSM.is_active:
        # 素材获取
        if not ui.search(materialsSpots, title_roi):
            ui.sleep(0.2)
            for i in range(2):
                icon_point = search_icon_materials_spots(ctx)
                if not icon_point:
                    if i == 0:
                        continue
                    else:
                        logger.warning(f"materialsSpots icon not found")
                        return None
                ui.click_point(icon_point, times=2, interval=0.3)
                if ui.sleep(0.2).wait(2, 0.3).until(lambda: ui.snapshot().search(materialsSpots, title_roi)):
                    ui.sleep(0.3)
                    break

            # for i in materialsSpotsSidebar:
            #     ui.click_point(i, 2, 0.2).sleep(0.8)
            #     if ui.snapshot().search(materialsSpots, title_roi):
            #         break

        return I18nText.MaterialsSpots
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
        if ui.search(activity, title_roi) and ui.search(tab_text):
            pass
        else:
            ui.click_point(activitySidebar, times=2, interval=0.3)
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot() and ui.search(activity, title_roi) and ui.search(tab_text)):
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

    # 检查100活跃点是否为黄色待领取
    if ColorRule().points(pts_sp[num_points - 1]).colors(yellow).match(img):
        ui.click_point(pts_sp[num_points - 1], times=2, interval=0.2)
        if not ui.sleep(0.5).wait().until(
                lambda: ui.snapshot().click_text(ctx.tr(I18nText.TapTheBlankAreaToClose), delay=0.3)):
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
            ui.click_point(pts_sp[i], times=2, interval=0.2)
            if not ui.sleep(0.5).wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.TapTheBlankAreaToClose), delay=0.3)):
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


@node(NodeName.doMaterialsSpots)
def doMaterialsSpots(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
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
    ui.activate().sleep(0.1)

    tacets = [
        I18nText.WingfallChasm,
        I18nText.SilentChasm,
        I18nText.SplitChasm,
        I18nText.ErodedChasm,
        I18nText.AshenChasm,
        I18nText.FallenSanctum,
        I18nText.LessonInSunset,
        I18nText.StrickenSanctum,
        I18nText.LessonInVoid,
        I18nText.LessonInEmbers,
        I18nText.GardenOfSalvation,
        I18nText.AbyssOfInitiation,
        I18nText.GardenOfAdoration,
        I18nText.AbyssOfSacrifice,
        I18nText.AbyssOfConfession,
        I18nText.FlamingRemnants,
        I18nText.MistyForest,
        I18nText.ErodedRuins,
        I18nText.MoonlitGroves,
        I18nText.MarigoldWoods,
    ]
    tacets_fsm = [
        local.wingfallChasmFSM,
        local.silentChasmFSM,
        local.splitChasmFSM,
        local.erodedChasmFSM,
        local.ashenChasmFSM,
        local.fallenSanctumFSM,
        local.lessonInSunsetFSM,
        local.strickenSanctumFSM,
        local.lessonInVoidFSM,
        local.lessonInEmbersFSM,
        local.gardenOfSalvationFSM,
        local.abyssOfInitiationFSM,
        local.gardenOfAdorationFSM,
        local.abyssOfSacrificeFSM,
        local.abyssOfConfessionFSM,
        local.flamingRemnantsFSM,
        local.mistyForestFSM,
        local.erodedRuinsFSM,
        local.moonlitGrovesFSM,
        local.marigoldWoodsFSM,
    ]
    weapons = [
        I18nText.Sword,
        I18nText.Rectifier,
        I18nText.Broadblade,
        I18nText.Gauntlets,
        I18nText.Pistols,
    ]

    # 任务选中的副本
    index, cur_fsm = next(((i, x) for i, x in enumerate(tacets_fsm) if x.is_active), (None, None))
    cur_instance: str = tacets[index]
    logger.info(f"{ctx.tr(cur_instance).raw}")
    if not cur_fsm:
        return False

    # 任务状态检查
    if cur_fsm.status.is_terminal:
        return True
    in_progress = cur_fsm.status == TaskStatus.IN_PROGRESS
    if cur_fsm.status == TaskStatus.PENDING:
        cur_fsm.start()

    def _fail_return():
        ui.esc().sleep(1)
        if in_progress:
            cur_fsm.fail()
            return True
        return False

    # 点击凝素领域
    def _wait_content():
        if ui.snapshot().search(ctx.tr(weapons), bbox_guidebook_content(ctx)):
            return True
        ui.click_text(
            ctx.tr(I18nText.ForgeryChallenge), bbox_guidebook_item(ctx), pk=PointKind.RANDOM, times=2, interval=0.1)
        return False

    # 确认已进入凝素领域
    if not ui.wait().until(_wait_content):
        return _fail_return()

    # 检查体力
    cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
    if cur_waveplate is None or waveplate_crystal is None:
        return False
    cost = 40
    if cur_waveplate < cost:
        logger.info(f"⏭️ skip because: waveplate &lt; {cost}")
        cur_fsm.complete()
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

    keywords = ctx.tr([*tacets, I18nText.Go, I18nText.Challenge])

    # 滑动条最下方所在的位置
    scroll_p1 = ctx.scaler.as_point(AnchorPoint(1245, 250, Align.Top | Align.Right))
    # 滑动条移动后的位置
    scroll_p2 = ctx.scaler.as_point(AnchorPoint(1245, 325, Align.Top | Align.Right))
    # 滑动条移动滑到底的位置
    scroll_p3 = ctx.scaler.as_point(AnchorPoint(1245, 628, Align.Top | Align.Right))

    # 两个一组分组
    card = None
    next_point = scroll_p1
    while True:
        # 获取这页的副本
        # textboxes = ui.sleep(0.1).snapshot(resize=False).search(keywords, bbox_guidebook_content(ctx))
        textboxes = ui.sleep(0.1).snapshot().search(keywords, bbox_guidebook_content(ctx))
        if not textboxes:
            return _fail_return()
        textboxes.sort(key=lambda p: p.y1)
        logger.debug(f"textboxes: {textboxes}")

        # 找出指定副本
        for textbox in textboxes:
            if re.search(ctx.tr(tacets[index]), textbox.text, re.I):
                card = [textbox, None, False]
                continue
            if card is not None and re.search(ctx.tr(I18nText.Challenge), textbox.text, re.I):
                card[1] = textbox
                break
            elif card is not None and re.search(ctx.tr(I18nText.Go), textbox.text, re.I):
                card[1] = textbox
                card[2] = True
                break

        # 已找到
        if card and all(i is not None for i in card):
            break
        card = None

        # 点击下一页
        next_point = Point(next_point.x, next_point.y + scroll_p2.y - scroll_p1.y)
        if next_point.y >= scroll_p3.y:
            break
        logger.debug(f"next_point: {next_point}")
        ui.sleep(0.2).click_point(next_point, times=2, interval=0.2).sleep(0.3)

    logger.debug(f"card: {card}")
    if not card or any(i is None for i in card):
        logger.debug(f"result: {ui.bbox_result}")
        return _fail_return()

    tbox, challenge, unlock = card

    # 检查副本未解锁
    if unlock:
        logger.warning(f"Unlock instance: {ctx.tr(cur_instance).raw}")
        cur_fsm.complete()
        return True

    # 点击直接挑战
    for _ in range(2):
        # 有时ui反应太慢，点快了ui没跳转，再试一次
        ui.sleep(0.4).click_bbox(challenge, times=2, interval=0.2)
        if ui.sleep(1).wait(3, 0.3).until(lambda: not ui.snapshot().search(ctx.tr(weapons))):
            break

    # 进入副本
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.SoloChallenge), delay=0.35)):
        return _fail_return()
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.StartChallenge), delay=0.3, times=2, interval=0.3)):
        return _fail_return()

    quest_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top), AnchorPoint(400, 720, Align.Left | Align.Bottom)))

    # 循环刷
    max_challenge = 12
    for i in range(max_challenge):
        if i == max_challenge - 1:
            return _fail_return()

        # 确认已进入副本
        if not ui.sleep(3 if i > 0 else 0.1).wait(25, 0.5).until(
                lambda: ui.is_on_homepage() and ui.snapshot().search(ctx.tr(I18nText.StartChallenge), quest_roi)):
            return _fail_return()

        # 开始挑战
        if not move_and_scan_dialogue(ctx, ctx.tr(I18nText.StartChallenge), 15):
            return _fail_return()
        ui.pick_up(2, 0.2).sleep(0.3)

        # 打
        combat_system = CombatSystem(ctx.control_service, ctx.img_service)
        combat_system.set_resonators(ctx.shared.team_members)
        combat_system.is_async = True
        combat_system.check_boss_hp = False
        combat_system.auto_pickup = False

        timeout = 10 * 60
        no_text_count = 3
        no_text_max = no_text_count
        deadline = time.monotonic() + timeout
        hp_roi = bbox_hp_bar(ctx).as_tuple()

        while ctx.runtime.stop_event.is_set() or time.monotonic() < deadline:
            if no_text_count < 0:
                break
            combat_system.start(3.5)
            ui.sleep(1.5)
            ui.snapshot()
            img = ui.img
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
                # boxes = img_util.detect_hp_bar(img, hp_roi)
                # if boxes:
                #     logger.debug("有血条，还在战斗中")
                #     no_text_count = no_text_max
                #     if logger.isEnabledFor(logging.DEBUG):
                #         img_draw = img_util.draw_detect_hp_bar(img, boxes)
                #         img_util.save_img_in_temp(img_draw)
                #     continue
                no_text_count -= 1
            # 断开连接
            page = GlobalPage(ctx)
            if page.isInternetDisconnecting(ui=ui):
                combat_system.stop(join=True)
                return False
            if page_key := page.action(ui=ui):
                logger.debug(f"Found page: {page_key}")

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
                return _fail_return()

            # 领取奖励
            if not ui.pick_up(2, 0.2).sleep(0.3).wait().until(
                    lambda: ui.snapshot().search(ctx.tr(I18nText.ForgeryClaim))):
                return _fail_return()

        # 获取体力值
        cost = 40
        cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

        if cur_waveplate is None or waveplate_crystal is None:
            return _fail_return()
        if cur_waveplate < cost:
            cur_fsm.complete()
            return True
        # 根据体力选择双倍单倍
        if cur_waveplate >= cost * 2:
            claim = I18nText.ForgeryClaimX2
            cur_waveplate -= cost * 2
        else:
            claim = I18nText.ForgeryClaim
            cur_waveplate -= cost
        if not ui.click_text(ctx.tr(claim), delay=0.4):
            return _fail_return()

        # 此处仅打印日志用，打印剩余次数
        match_remaining_attempts(ui.search(ctx.tr(I18nText.DoubleDropChancesToday)))

        # 根据体力选择重新挑战还是离开
        if ui.sleep(0.3).wait().until(
                lambda: ui.snapshot().search(ctx.tr([I18nText.ForgeryExit, I18nText.ForgeryRestart]))):
            if cur_waveplate >= cost:
                if ui.click_text(ctx.tr(I18nText.ForgeryRestart), delay=0.3, times=2, interval=0.3):
                    continue
                else:
                    return _fail_return()
            else:
                ui.click_text(ctx.tr(I18nText.ForgeryExit), delay=0.3, times=2, interval=0.3)
        else:
            if cur_waveplate >= cost:
                return _fail_return()
        cur_fsm.complete()
        return True

    if not cur_fsm.is_terminal:
        cur_fsm.fail()
    return False


@node(NodeName.doSimulationChallenge)
def doSimulationChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


@node(NodeName.doBossChallenge)
def doBossChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


@node(NodeName.doTacetSuppression)
def doTacetSuppression(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.tacetSuppressionFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    tacets = [
        I18nText.WesternFangPeaksTacetField,
        I18nText.EasternXuanPeaksTacetField,
        I18nText.TacetFieldSolisiaLanding,
        I18nText.TacetFieldFrostlandsTransitPort,
        I18nText.TacetFieldMountGjallar,
        I18nText.TacetFieldMawburrowDesert,
        I18nText.TacetFieldStagnantRun,
    ]
    tacets_fsm = [
        local.westernFangPeaksTacetFieldFSM,
        local.easternXuanPeaksTacetFieldFSM,
        local.tacetFieldSolisiaLandingFSM,
        local.tacetFieldFrostlandsTransitPortFSM,
        local.tacetFieldMountGjallarFSM,
        local.tacetFieldMawburrowDesertFSM,
        local.tacetFieldStagnantRunFSM,
    ]

    # 任务选中的副本
    index, cur_fsm = next(((i, x) for i, x in enumerate(tacets_fsm) if x.is_active), (None, None))
    cur_instance: str = tacets[index]
    logger.info(f"{ctx.tr(cur_instance).raw}")
    if not cur_fsm:
        return False

    # 任务状态检查
    if cur_fsm.status.is_terminal:
        return True
    in_progress = cur_fsm.status == TaskStatus.IN_PROGRESS
    if cur_fsm.status == TaskStatus.PENDING:
        cur_fsm.start()

    def _fail_return():
        ui.esc().sleep(1)
        if in_progress:
            cur_fsm.fail()
            return True
        return False

    try:
        # 点击无音清剿
        def _wait_content():
            if ui.snapshot().search(ctx.tr(I18nText.EchoSet), bbox_guidebook_content(ctx)):
                return True
            ui.click_text(
                ctx.tr(I18nText.TacetSuppression), bbox_guidebook_item(ctx), pk=PointKind.RANDOM, times=2, interval=0.1)
            return False

        # 确认已进入无音清剿
        if not ui.wait().until(_wait_content):
            return _fail_return()

        # 检查体力
        cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
        if cur_waveplate is None or waveplate_crystal is None:
            return False
        cost = 60
        if cur_waveplate < cost:
            logger.info(f"⏭️ skip because: waveplate &lt; {cost}")
            cur_fsm.complete()
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

        keywords = ctx.tr([*tacets, I18nText.Go, I18nText.Challenge, I18nText.EchoSet])
        # 获取无音区
        # textboxes = ui.snapshot(resize=False).search(keywords, bbox_guidebook_content(ctx))
        textboxes = ui.snapshot().search(keywords, bbox_guidebook_content(ctx))
        if not textboxes:
            return _fail_return()
        textboxes.sort(key=lambda p: p.y1)
        logger.debug(f"textboxes: {textboxes}")

        # 分组
        cards = {}
        for i, textbox in enumerate(textboxes):
            found_tacet = next((x for x in tacets if re.search(ctx.tr(x), textbox.text, re.I)), None)
            if not found_tacet:
                continue
            cur_card = [textbox, None, False]
            cards[found_tacet] = cur_card
            if i + 1 >= len(textboxes):
                continue
            # 直接挑战表示可以打，前往表示没解锁不能打
            if re.search(ctx.tr(I18nText.Challenge), textboxes[i + 1].text, re.I):
                cur_card[1] = textboxes[i + 1]
            elif re.search(ctx.tr(I18nText.Go), textboxes[i + 1].text, re.I):
                cur_card[1] = textboxes[i + 1]
                cur_card[2] = True
        logger.debug(f"cards: {cards}")

        # 取出与选择同名的组
        cur_card = cards.get(cur_instance)
        logger.debug(f"cur_card: {cur_card}")
        if not cur_card or any(i is None for i in cur_card):
            return _fail_return()

        tbox, challenge, unlock = cur_card

        # 检查副本未解锁
        if unlock:
            logger.warning(f"Unlock instance: {ctx.tr(cur_instance).raw}")
            cur_fsm.complete()
            return True

        # 点击直接挑战
        ui.sleep(0.5).click_bbox(tbox)
        for _ in range(2):
            # 有时ui反应太慢，点快了ui没跳转，再试一次
            ui.sleep(0.2).click_bbox(challenge, times=2, interval=0.2)
            if ui.sleep(1).wait(3, 0.3).until(
                    lambda: not ui.snapshot().search(ctx.tr(I18nText.TacetSuppression), bbox_guidebook_item(ctx))):
                break

        # 点击开启挑战
        if not ui.sleep(0.3).wait().until(
                lambda: ui.snapshot().click_text(ctx.tr(I18nText.StartChallenge), delay=0.3, times=2, interval=0.3)):
            return _fail_return()

        # 循环刷
        max_challenge = 9
        for i in range(max_challenge):
            if i == max_challenge - 1:
                return _fail_return()

            # 进入副本
            if ui.sleep(0.5).wait_back_home():
                ui.sleep(1.0)
            else:
                return _fail_return()

            # 检查战斗文本
            keyword = ctx.tr([I18nText.DefeatTheTdsInTheTacetField, I18nText.TacetField])
            if not ui.snapshot().search(keyword):
                ui.esc()
                if ui.sleep(0.3).wait().until(
                        lambda: ui.snapshot().click_text(ctx.tr(I18nText.Restart), delay=0.3, times=2, interval=0.3)):
                    continue
                return _fail_return()

            # 直接打，打起来才会有文字提示
            combat_system = CombatSystem(ctx.control_service, ctx.img_service)
            combat_system.set_resonators(ctx.shared.team_members)
            combat_system.is_async = True
            combat_system.check_boss_hp = False
            combat_system.auto_pickup = False
            combat_system.exit_special_state(Morph.Forced)

            timeout = 10 * 60
            no_text_count = 3
            no_text_max = no_text_count
            deadline = time.monotonic() + timeout
            hp_roi = bbox_hp_bar(ctx).as_tuple()

            while ctx.runtime.stop_event.is_set() or time.monotonic() < deadline:
                if no_text_count < 0:
                    break
                combat_system.start(3.5)
                ui.sleep(1.5)
                ui.snapshot()
                img = ui.img
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
                    # boxes = img_util.detect_hp_bar(img, hp_roi)
                    # if boxes:
                    #     logger.debug("有血条，还在战斗中")
                    #     no_text_count = no_text_max
                    #     if logger.isEnabledFor(logging.DEBUG):
                    #         img_draw = img_util.draw_detect_hp_bar(img, boxes)
                    #         img_util.save_img_in_temp(img_draw)
                    #     continue
                    no_text_count -= 1
                # 断开连接
                page = GlobalPage(ctx)
                if page.isInternetDisconnecting(ui=ui):
                    combat_system.stop(join=True)
                    return False
                if page_key := page.action(ui=ui):
                    logger.debug(f"Found page: {page_key}")

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
                    return _fail_return()

                # 领取奖励
                if not ui.pick_up(2, 0.2).sleep(0.3).wait().until(
                        lambda: ui.snapshot().search(ctx.tr(I18nText.TacetFieldClaim))):
                    return _fail_return()

            # 获取体力值
            cost = 60
            cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

            if cur_waveplate is None or waveplate_crystal is None:
                return _fail_return()
            if cur_waveplate < cost:
                cur_fsm.complete()
                return True
            # 根据体力选择双倍单倍
            if cur_waveplate >= cost * 2:
                claim = I18nText.TacetFieldClaimX2
                cur_waveplate -= cost * 2
            else:
                claim = I18nText.TacetFieldClaim
                cur_waveplate -= cost
            if not ui.click_text(ctx.tr(claim), delay=0.4):
                return _fail_return()

            # 此处仅打印日志用，打印剩余次数
            match_remaining_attempts(ui.search(ctx.tr(I18nText.DoubleDropChancesToday)))

            # # 点击确认弹窗
            # if not ui.sleep(0.5).wait().until(
            #         lambda: ui.snapshot().click_text(ctx.tr(I18nText.TacetFieldConfirm), delay=0.3)):
            #     return _fail_return()

            ui.sleep(1)
            # 容错，判断是否有体力不足是否继续弹窗
            if ui.snapshot().search(ctx.tr([I18nText.WeeklyCancel, I18nText.DoNotShowAgain])):
                if ui.click_text(ctx.tr(I18nText.DoNotShowAgain), delay=0.2):
                    ui.sleep(0.1)
                if ui.click_text(ctx.tr(I18nText.WeeklyCancel), delay=0.2):
                    ui.sleep(0.4)
                    cur_fsm.complete()
                    return True

            # 根据体力选择重新挑战还是离开
            if ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().search(ctx.tr([I18nText.TacetFieldExit, I18nText.TacetFieldRestart]))):
                if cur_waveplate >= cost:
                    if ui.click_text(ctx.tr(I18nText.TacetFieldRestart), delay=0.3, times=2, interval=0.3):
                        continue
                    else:
                        return _fail_return()
                else:
                    ui.click_text(ctx.tr(I18nText.TacetFieldExit), delay=0.3, times=2, interval=0.3)
            else:
                if cur_waveplate >= cost:
                    return _fail_return()
            cur_fsm.complete()
            return True

        if not cur_fsm.is_terminal:
            cur_fsm.complete()
            return True
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


@node(NodeName.doWeeklyChallenge)
def doWeeklyChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.weeklyChallengeFSM.is_terminal:
        return True

    ui = UIOp(ctx)
    tacets = [
        I18nText.CourtOfShackledSouls,
        I18nText.SeedOfIllusoryOrigin,
        I18nText.GateOfTheLostStar,
        I18nText.CinderniteApocalypse,
        I18nText.TheWheelOfBrokenFate,
        I18nText.BeyondTheCrimsonCurtain,
        I18nText.TheFatedConfrontation,
        I18nText.StatueOfTheCrownless,
        I18nText.ChaoticJuncture,
        I18nText.BellOfArchaicChants,
    ]
    tacets_fsm = [
        local.courtOfShackledSoulsFSM,
        local.seedOfIllusoryOriginFSM,
        local.gateOfTheLostStarFSM,
        local.cinderniteApocalypseFSM,
        local.theWheelOfBrokenFateFSM,
        local.beyondTheCrimsonCurtainFSM,
        local.theFatedConfrontationFSM,
        local.statueOfTheCrownlessFSM,
        local.chaoticJunctureFSM,
        local.bellOfArchaicChantsFSM,
    ]

    # 任务选中的副本
    index, cur_fsm = next(((i, x) for i, x in enumerate(tacets_fsm) if x.is_active), (None, None))
    cur_instance: str = tacets[index]
    logger.info(f"{ctx.tr(cur_instance).raw}")
    if not cur_fsm:
        return False

    # 任务状态检查
    if cur_fsm.status.is_terminal:
        return True
    in_progress = cur_fsm.status == TaskStatus.IN_PROGRESS
    if cur_fsm.status == TaskStatus.PENDING:
        cur_fsm.start()

    def _fail_return():
        # ui.esc().sleep(0.5)
        if in_progress:
            cur_fsm.fail()
            return True
        return False

    # 点击战歌重奏
    def _wait_content():
        if ui.snapshot().search(ctx.tr(I18nText.WeeklyChallengeWeeklyChallenge), bbox_guidebook_content(ctx)):
            return True
        ui.click_text(
            ctx.tr(I18nText.WeeklyChallenge), bbox_guidebook_item(ctx), pk=PointKind.RANDOM, times=2, interval=0.1)
        return False

    # 确认已进入战歌重奏
    if not ui.wait().until(_wait_content):
        return _fail_return()

    # 检查体力
    cur_waveplate, waveplate_crystal = query_waveplate_guidebook(ctx)
    if cur_waveplate is None or waveplate_crystal is None:
        return False
    cost = 60
    if cur_waveplate < cost:
        logger.info(f"⏭️ skip because: waveplate &lt; {cost}")
        cur_fsm.complete()
        return True

    # 本周剩余可收取次数: 3/3
    result = ui.sleep(0.2).wait().until(
        lambda: ui.snapshot().search(ctx.tr(I18nText.RemainingWeeklyAttempts), bbox_guidebook_content(ctx)))
    # lambda: ui.snapshot(resize=False).search(ctx.tr(I18nText.RemainingWeeklyAttempts), bbox_guidebook_content(ctx)))
    remain, max_remain = match_remaining_attempts(result)
    if remain is None or not max_remain:
        return _fail_return()
    if remain == 0:
        logger.info(f"⏭️ skip because: remaining attempts {remain}/{max_remain}")
        cur_fsm.complete()
        return True

    # 获取这页的副本
    keywords = ctx.tr([*tacets, I18nText.Go, I18nText.Challenge])
    textboxes = ui.search(keywords, bbox_guidebook_content(ctx))
    if not textboxes:
        return _fail_return()
    textboxes.sort(key=lambda p: p.y1)
    logger.debug(f"textboxes: {textboxes}")

    # 分组
    cards = {}
    for i, textbox in enumerate(textboxes):
        found_tacet = next((x for x in tacets if re.search(ctx.tr(x), textbox.text, re.I)), None)
        logger.debug(f"found_tacet: {found_tacet}")
        if not found_tacet:
            continue
        cur_card = [textbox, None, False]
        cards[found_tacet] = cur_card
        if i + 1 >= len(textboxes):
            continue
        # 直接挑战表示可以打，前往表示没解锁不能打
        if re.search(ctx.tr(I18nText.Challenge), textboxes[i + 1].text, re.I):
            cur_card[1] = textboxes[i + 1]
        elif re.search(ctx.tr(I18nText.Go), textboxes[i + 1].text, re.I):
            cur_card[1] = textboxes[i + 1]
            cur_card[2] = True
    logger.debug(f"cards: {cards}")

    # 取出与选择同名的组
    cur_card = cards.get(cur_instance)
    logger.debug(f"cur_card: {cur_card}")
    if not cur_card or any(i is None for i in cur_card):
        return _fail_return()

    tbox, challenge, unlock = cur_card

    # 检查副本未解锁
    if unlock:
        logger.warning(f"Unlock instance: {ctx.tr(cur_instance).raw}")
        cur_fsm.complete()
        return True

    # 点击直接挑战
    ui.sleep(0.5).click_bbox(tbox)
    for _ in range(2):
        # 有时ui反应太慢，点快了ui没跳转，再试一次
        ui.sleep(0.2).click_bbox(challenge, times=2, interval=0.2)
        if ui.sleep(1).wait(3, 0.3).until(
                lambda: not ui.snapshot().search(ctx.tr(I18nText.WeeklyChallenge), bbox_guidebook_item(ctx))):
            break

    # 点击可能影响剧情体验弹窗，点击单人挑战
    for i in range(2):
        waiting = i == 0 and not ui.search(ctx.tr([I18nText.SoloChallenge, I18nText.ArrivingAtTheDestination]))
        if waiting or i > 0:
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().search(ctx.tr([I18nText.SoloChallenge, I18nText.ArrivingAtTheDestination]))):
                return _fail_return()
        if ui.search(ctx.tr(I18nText.ArrivingAtTheDestination)):
            if not ui.click_text(ctx.tr(I18nText.Confirm), delay=0.2, times=2, interval=0.2):
                return _fail_return()
            ui.sleep(0.2)
            continue
        if not ui.click_text(ctx.tr(I18nText.SoloChallenge), delay=0.35):
            return _fail_return()
        break

    # 点击开启挑战
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.StartChallenge), delay=0.2, times=2, interval=0.3)):
        return _fail_return()

    # 循环刷
    max_challenge = 9
    for i in range(max_challenge):
        if i == max_challenge - 1:
            return _fail_return()

        # 确认已进入副本
        if not ui.sleep(3 if i == 0 else 0.1).wait(15, 0.2).until(lambda: ui.is_on_homepage()):
            return _fail_return()
        logger.info("已进入副本")
        if cur_instance == I18nText.SeedOfIllusoryOrigin:
            for _ in range(3):
                ctx.control_service.dash_dodge()
                ui.sleep(0.2)
            ctx.control_service.attack()
            ui.sleep(0.6)

        combat_system = CombatSystem(ctx.control_service, ctx.img_service)
        combat_system.set_resonators(ctx.shared.team_members)
        combat_system.is_async = True
        combat_system.check_boss_hp = True
        combat_system.auto_pickup = False
        combat_system.exit_special_state(Morph.Forced)

        # 打
        timeout = 10 * 60
        no_text_count = 3
        no_text_max = no_text_count
        deadline = time.monotonic() + timeout
        hp_roi = bbox_hp_bar(ctx).as_tuple()

        while ctx.runtime.stop_event.is_set() or time.monotonic() < deadline:
            if no_text_count < 0:
                break
            combat_system.start(3.5)
            ui.sleep(1.5)
            ui.snapshot()
            img = ui.img
            if ui.is_on_homepage():
                # 领取奖励
                if ui.search(ctx.tr(I18nText.WeeklyClaimRewards)):
                    logger.debug("Weekly Claim Rewards")
                    break
                # 击败敌人
                if ui.search(ctx.tr(I18nText.WeeklyDefeatTheEnemy)):
                    logger.debug("Fight fight!")
                    no_text_count = no_text_max
                    continue
                else:
                    logger.debug(f"Text not found: {ctx.tr(I18nText.WeeklyDefeatTheEnemy).raw}")
                # boxes = img_util.detect_hp_bar(img, hp_roi)
                # if boxes:
                #     logger.debug("有血条，还在战斗中")
                #     no_text_count = no_text_max
                #     if logger.isEnabledFor(logging.DEBUG):
                #         img_draw = img_util.draw_detect_hp_bar(img, boxes)
                #         img_util.save_img_in_temp(img_draw)
                #     continue
                no_text_count -= 1
            # 断开连接
            page = GlobalPage(ctx)
            if page.isInternetDisconnecting(ui=ui):
                combat_system.stop(join=True)
                return False
            if page_key := page.action(ui=ui):
                logger.debug(f"Found page: {page_key}")

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
                return _fail_return()

            # 领取奖励
            if not ui.pick_up(2, 0.2).sleep(0.5).wait().until(
                    lambda: ui.snapshot().search(notice_keywords)):
                return _fail_return()

        # 此处仅打印日志用，打印剩余次数
        match_remaining_attempts(ui.search(ctx.tr(I18nText.DoubleDropChancesToday)))

        # 检查是否达到次数上限
        if ui.search(ctx.tr(I18nText.YouHaveReachedTheChallengeLimit)):
            logger.info(f"{ctx.tr(I18nText.YouHaveReachedTheChallengeLimit).raw}")
            cur_fsm.complete()
            if ui.click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4):
                if ui.sleep(2).wait_back_home():
                    ui.sleep(0.5)
                else:
                    return _fail_return()
            else:
                logger.warning(f"Text not found: {ctx.tr(I18nText.WeeklyExit).raw}")
            return True

        cost = 60
        cur_waveplate, waveplate_crystal = query_waveplate_claim_rewards(ctx)

        if cur_waveplate is None or waveplate_crystal is None:
            return _fail_return()
        if cur_waveplate < cost:
            cur_fsm.complete()
            return True

        cur_waveplate -= cost
        if not ui.click_text(ctx.tr(I18nText.WeeklyConfirm), delay=0.3):
            return _fail_return()

        ui.sleep(1)
        # 容错，判断是否有体力不足是否继续弹窗
        if ui.snapshot().search(ctx.tr([I18nText.WeeklyCancel, I18nText.DoNotShowAgain])):
            ui.click_text(ctx.tr(I18nText.DoNotShowAgain), delay=0.3)
            ui.click_text(ctx.tr(I18nText.WeeklyCancel), delay=0.2)
            cur_fsm.complete()
            return True

        if cur_waveplate >= cost:
            if ui.wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyRestart), delay=0.4, times=2, interval=0.2)):
                continue
            return _fail_return()

        ui.wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.WeeklyExit), delay=0.4, times=2, interval=0.2))
        cur_fsm.complete()
        if ui.sleep(2).wait_back_home():
            ui.sleep(0.5)
        return True

    if not cur_fsm.is_terminal:
        cur_fsm.fail()
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
        I18nText.SouthernYuanHillsTacetDiscordNest,
        I18nText.StarblindCrashsiteTacetDiscordNest,
        I18nText.RebirthUplandsTacetDiscordNest,
        I18nText.StagnantRunTacetDiscordNest,
    ]
    tacets_fsm = [
        local.southernYuanHillsTacetDiscordNestFSM,
        local.starblindCrashsiteTacetDiscordNestFSM,
        local.rebirthUplandsTacetDiscordNestFSM,
        local.stagnantRunTacetDiscordNestFSM,
    ]
    tacets_route = [
        [Run.forward(4.5)],
        [Run.right(0.25), Run.forward(3.3)],
        [Run.forward(2.5)],
        [Run.forward(5.5)],
    ]

    try:
        scrollbar = ctx.scaler.as_point(AnchorPoint(458, 636, Align.Top | Align.Left))
        logger.debug(f"scrollbar point: {scrollbar}")

        # 点击残像聚落
        def _wait_content():
            if ui.snapshot().search(
                    ctx.tr(I18nText.TacetDiscordNestTacetDiscordNest), bbox_guidebook_content(ctx)):
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
        # textboxes = ui.snapshot(resize=False).search(keywords, bbox_guidebook_content(ctx))
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
            if not ui.search(ctx.tr([I18nText.FastTravel, I18nText.EnableNavigation])):
                if not ui.wait().until(
                        lambda: ui.snapshot().search(ctx.tr([I18nText.FastTravel, I18nText.EnableNavigation]))):
                    if in_progress:
                        cur_fsm.fail()
                    return False
            # 检查副本未解锁
            if ui.search(ctx.tr(I18nText.EnableNavigation)):
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
            combat_system.set_resonators(ctx.shared.team_members, is_print=False)
            combat_system.exit_special_state(Morph.Forced)
            ui.move(tacets_route[_tacets_idx]).sleep(0.3)

            if cur_instance == I18nText.SouthernYuanHillsTacetDiscordNest:
                # 落渊南丘
                tmpl_name = "8_-7_1.png"
                tmpl_img = img_util.read_img(file_util.get_assets_map("Huanglong/Mengzhou/8_-7_1.png"))
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
                scene_img = ui.img
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
                    scene_img = ui.grap()
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

                    scene_img = ui.grap()
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

            is_combat = not ui.snapshot().search(
                ctx.tr([I18nText.TacetDiscordNestCleared, I18nText.TacetDiscordNestClearedMengzhou]))
            # 可能打着打着出了战斗区域，标识文本消失，误判已经打完，循环重置位置接着打
            max_combat_range = 3
            for k in range(max_combat_range):
                if k > 0:
                    logger.debug(f"k: {k}")
                # 没刷就打
                if is_combat:
                    combat_system = CombatSystem(ctx.control_service, ctx.img_service)
                    combat_system.set_resonators(ctx.shared.team_members)
                    combat_system.is_async = True
                    combat_system.check_boss_hp = False
                    combat_system.auto_pickup = False
                    # combat_system.exit_special_state(Morph.Forced)

                    timeout = 10 * 60
                    deadline = time.monotonic() + timeout
                    no_text_max = 3
                    no_text_count = no_text_max
                    hp_roi = bbox_hp_bar(ctx).as_tuple()

                    while ctx.runtime.stop_event.is_set() or time.monotonic() < deadline:
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
                            if ui.search(ctx.tr(
                                    [I18nText.TacetDiscordNestCleared, I18nText.TacetDiscordNestClearedMengzhou])):
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

                        # 断开连接
                        page = GlobalPage(ctx)
                        if page.isInternetDisconnecting(ui=ui):
                            combat_system.stop(join=True)
                            return False
                        if page_key := page.action(ui=ui):
                            logger.debug(f"Found page: {page_key}")

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

                    is_combat = not ui.snapshot().search(ctx.tr(
                        [I18nText.TacetDiscordNestCleared, I18nText.TacetDiscordNestClearedMengzhou]))
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

    claim_all = ctx.tr(I18nText.MailClaimAll)
    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().click_text(claim_all)):
        logger.warning(f"Text not found: {claim_all.raw}")
        local.mailFSM.fail()
        return False

    def isItemsObtained():
        if ui.snapshot().click_text(ctx.tr(I18nText.ItemsObtained)):
            ui.sleep(0.3)
            return True
        elif ui.search(ctx.tr(I18nText.MailClaimAll)):
            return True
        return False

    ui.sleep(1).wait(2, 0.3).until(isItemsObtained)
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

    # 从终端进入先约电台，不用快捷键F4容易被占用
    if ui.is_on_homepage():
        ui.esc().sleep(1.0)
        if not ui.wait().until(lambda: GlobalPage(ctx).isTerminal(ui=ui.snapshot())):
            return False
    elif not GlobalPage(ctx).isTerminal(ui=ui.snapshot()):
        return False
    if not ui.click_text(ctx.tr(I18nText.TerminalPioneerPodcast),
                         bbox_terminal_content(ctx), pk=PointKind.NEAR, times=2, interval=0.2):
        return False
    if not ui.sleep(1.2).wait().until(
            lambda: ui.snapshot().search([pioneerPodcast, ctx.tr(I18nText.PioneerPodcastUnavailable)])):
        return False
    if ui.search(ctx.tr(I18nText.PioneerPodcastUnavailable)):
        local.pioneerPodcastFSM.complete()
        ui.sleep(0.3).esc().sleep(1)
        return True

    sidebarsPioneerPodcast = ctx.scaler.as_point(AnchorPoint(50, 126, Align.Left | Align.Top))
    sidebarsPodcastTasks = ctx.scaler.as_point(AnchorPoint(50, 213, Align.Left | Align.Top))
    # 提示种类很多
    confirm = ctx.tr([I18nText.TapTheBlankAreaToClose, I18nText.PioneerPodcastConfirm, I18nText.Confirm])

    def closePodcastTasksNotice():
        ui.snapshot()
        # 可能弹窗获得奖励，需要点确定才关闭
        if ui.click_text(confirm, delay=0.2):
            return False
        # 可能提示获得电台经验，切到电台任务页，能过去说明提示已消失
        if ui.search(pioneerPodcast):
            return True
        ui.click_point(sidebarsPioneerPodcast, times=2, interval=0.2)
        return False

    # 先点电台任务
    ui.sleep(0.3).click_point(sidebarsPodcastTasks, times=2, interval=0.2).sleep(0.3)
    if ui.wait().until(lambda: ui.snapshot().search(podcastTasks)):
        if ui.click_text(ctx.tr(I18nText.PioneerPodcastClaimAll), pk=PointKind.NEAR):
            ui.sleep(1.5).wait(6, 0.4).until(closePodcastTasksNotice)

    # 再点先约电台
    ui.sleep(0.3).click_point(sidebarsPioneerPodcast, times=2, interval=0.2).sleep(0.3)
    if ui.wait().until(lambda: ui.snapshot().search(pioneerPodcast)):
        if ui.click_text(ctx.tr(I18nText.PioneerPodcastClaimAll), pk=PointKind.NEAR, times=2, interval=0.2):
            ui.sleep(2).wait(2, 0.4).until(lambda: ui.snapshot().click_text(confirm, delay=0.2, times=2, interval=0.2))

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
        self.local.materialsSpotsFSM.set_enabled(True)
        self.local.recurringChallengesFSM.set_enabled(False)
        self.local.pathOfGrowthFSM.set_enabled(False)
        self.local.enemyTracingFSM.set_enabled(False)
        self.local.milestonesFSM.set_enabled(False)

        ## ------- Guidebook Activity -------
        self.local.activityDailyFSM.set_enabled(cfg.activityOpen)
        self.local.activityWeeklyFSM.set_enabled(cfg.activityOpen and cfg.activityWeeklyOpen)

        ## ------- Guidebook MaterialsSpots -------
        self.local.forgeryChallengeFSM.set_enabled(cfg.forgeryChallengeOpen and cfg.forgeryChallenge)
        self.local.simulationChallengeFSM.set_enabled(cfg.simulationChallengeOpen and cfg.simulationChallenge)
        self.local.bossChallengeFSM.set_enabled(cfg.bossChallengeOpen and cfg.bossChallenge)
        self.local.tacetSuppressionFSM.set_enabled(cfg.tacetSuppressionOpen and cfg.tacetSuppression)
        self.local.weeklyChallengeFSM.set_enabled(cfg.weeklyChallengeOpen and cfg.weeklyChallenge)
        self.local.nightmarePurificationFSM.set_enabled(cfg.nightmarePurificationOpen and cfg.nightmarePurification)
        self.local.tacetDiscordNestFSM.set_enabled(cfg.tacetDiscordNestOpen and cfg.tacetDiscordNest)

        ## ------- Guidebook RecurringChallenges -------

        ## ------- Guidebook PathOfGrowth -------

        ### ------- Guidebook MaterialsSpots ForgeryChallenge -------
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

        ### ------- Guidebook MaterialsSpots SimulationChallenge -------

        ### ------- Guidebook MaterialsSpots BossChallenge -------

        ### ------- Guidebook MaterialsSpots TacetSuppression -------
        self.local.westernFangPeaksTacetFieldFSM.set_enabled(cfg.westernFangPeaksTacetField)
        self.local.easternXuanPeaksTacetFieldFSM.set_enabled(cfg.easternXuanPeaksTacetField)
        self.local.tacetFieldSolisiaLandingFSM.set_enabled(cfg.tacetFieldSolisiaLanding)
        self.local.tacetFieldFrostlandsTransitPortFSM.set_enabled(cfg.tacetFieldFrostlandsTransitPort)
        self.local.tacetFieldMountGjallarFSM.set_enabled(cfg.tacetFieldMountGjallar)
        self.local.tacetFieldMawburrowDesertFSM.set_enabled(cfg.tacetFieldMawburrowDesert)
        self.local.tacetFieldStagnantRunFSM.set_enabled(cfg.tacetFieldStagnantRun)

        ### ------- Guidebook MaterialsSpots WeeklyChallenge -------
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

        ### ------- Guidebook MaterialsSpots NightmarePurification -------

        ### ------- Guidebook MaterialsSpots TacetDiscordNest -------

        ### ------- Guidebook MaterialsSpots tacetDiscordNest -------
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
            .on(I18nText.MaterialsSpots).to(NodeName.doMaterialsSpots)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doActivity)
            .on(I18nText.ActivityDaily).to(NodeName.doActivityDaily)
            .on(I18nText.ActivityWeekly).to(NodeName.doActivityWeekly)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.source(NodeName.doActivityDaily).always().to(NodeName.doActivity)
        (
            self.engine.source(NodeName.doActivityWeekly)
            .on(False).to(NodeName.doPhantasmaDreamlandRhapsody)
            .always().to(NodeName.doActivity)
        )
        self.engine.source(NodeName.doPhantasmaDreamlandRhapsody).always().to(NodeName.globalDispatcher)

        (
            self.engine.source(NodeName.doMaterialsSpots)
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
