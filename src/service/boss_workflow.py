import logging
import random
import re
import time
from typing import Optional

from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import ResonatorNameEnum, ScenarioEnum
from src.core.combat.combat_system import CombatSystem
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, Point
from src.core.i18n import I18nText, Language, I18nTr
from src.core.message import MsgType, MsgTaskStatus
from src.core.movement import Run, Walk
from src.core.pages import I18nPage, UIOp
from src.core.resonator import Resonator
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import (
    absorb_around_variant_blind, bbox_terminal_content, bbox_guidebook_content, move_and_scan_dialogue,
    match_remaining_attempts, linear_spacing, query_waveplate_guidebook, query_waveplate_claim_rewards,
    object_detection, bbox_hp_bar, bbox_guidebook_item, search_icon_materials_spots, bbox_dialogue,
    bbox_guidebook_title,
)
from src.util import img_util, file_util
from src.util.img_sift_util import SIFTFeatureMatcher
from src.util.img_tile_util import TileGrid

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        ### ------- Guidebook MaterialsSpots ForgeryChallenge -------
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
        self.tacetFieldSolisiaLandingFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldSolisiaLanding)
        self.tacetFieldFrostlandsTransitPortFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldFrostlandsTransitPort)
        self.tacetFieldMountGjallarFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldMountGjallar)
        self.tacetFieldMawburrowDesertFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldMawburrowDesert)
        self.tacetFieldStagnantRunFSM: TaskFSM = TaskFSM(name=I18nText.TacetFieldStagnantRun)

        ### ------- Guidebook MaterialsSpots WeeklyChallenge -------
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
            self.tacetFieldSolisiaLandingFSM,
            self.tacetFieldFrostlandsTransitPortFSM,
            self.tacetFieldMountGjallarFSM,
            self.tacetFieldMawburrowDesertFSM,
            self.tacetFieldStagnantRunFSM,
            name=I18nText.TacetSuppression
        )
        self.weeklyChallengeFSM: TaskFSMGroup = TaskFSMGroup(
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
        self.activityFSM: TaskFSM = TaskFSM(name=I18nText.Activity)
        # self.activityFSM: TaskFSMGroup = TaskFSMGroup(
        #     self.activityDailyFSM,
        #     # self.activityWeeklyFSM,
        #     name=I18nText.Activity
        # )
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
    ui.activate().sleep(0.1)

    # 已在终端页
    if ui.snapshot().match_page(I18nPage.Terminal.PAGE):
        logger.debug("已在终端")
        return I18nText.Terminal

    # 在全局预设中找出离开函数，尝试回到主页
    if ctx.page_service.global_page_action(ui.ocr_result):
        logger.debug("找到全局页面")
        ui.sleep(1)
        return None

    # 兜底规则，esc
    logger.info("Transferring")

    # num = round(random.uniform(1.5, 2.0), 2)
    num = max(1, min(1.4, random.gauss(1.2, 0.08)))
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
    if ui.match_page(I18nPage.Terminal.PAGE):
        ui.click_point(AnchorPoint(1197, 350, Align.Right | Align.Middle))
        if not ui.sleep(0.3).wait().until(
                lambda: ui.snapshot().click_text(ctx.tr(I18nText.Map), delay=0.2, times=2, interval=0.3)):
            ui.esc().sleep(1)
            return False
    else:
        # 大世界进入地图
        ctx.control_service.map()
    # 点击切换地图
    if not ui.sleep(0.5).wait(10, 0.4).until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.SwitchMap), delay=0.8)):
        return False

    # 选择瑝珑
    regions_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(600, 0, Align.Right | Align.Top), AnchorPoint(925, 1280, Align.Right | Align.Bottom)))
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.Huanglong), regions_roi, delay=0.4)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Huanglong).raw}")
        return False

    # 选择今州城
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.Jinzhou), delay=0.4)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Jinzhou).raw}")
        return False

    # 点击今州城传送点
    tmpl_name = "8_0_-1.png"
    tmpl_img = img_util.read_img(file_util.get_assets_map_huanglong(tmpl_name))
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
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.FastTravel), delay=0.3, times=2, interval=0.2)):
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
    if not ui.match_page(I18nPage.Terminal.PAGE):
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
    if not ui.sleep(0.8).wait(5, 0.5).until(
        lambda: ui.snapshot().search(ctx.tr(I18nText.QuickSetup), roi)):
        # lambda: ui.snapshot(resize=False).search(ctx.tr(I18nText.QuickSetup), roi)):
        logger.info(f"编队已锁定，离开战斗区域")
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
    if ui.snapshot().match_page(I18nPage.Terminal.PAGE):
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
                    logger.warning(f"materialsSpots icon not found")
                    return None
                ui.click(*icon_point, times=2, interval=0.3)
                if ui.sleep(0.2).wait(2, 0.3).until(lambda: ui.snapshot().search(materialsSpots, title_roi)):
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
        if not ui.search(activity, title_roi):
            ui.click_point(activitySidebar, times=2, interval=0.2).sleep(0.5)
        return I18nText.Activity

    return None


@node(NodeName.doMaterialsSpots)
def doMaterialsSpots(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    # TODO 双倍流程， 双倍材料、无音区 > 周本 > 材料、无音区
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


@node(NodeName.doBossChallenge)
def doBossChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


class BossWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name="BossWorkflow")
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
        self.local.activityFSM.set_enabled(cfg.activityOpen)
        self.local.materialsSpotsFSM.set_enabled(True)
        self.local.recurringChallengesFSM.set_enabled(False)
        self.local.pathOfGrowthFSM.set_enabled(False)
        self.local.enemyTracingFSM.set_enabled(False)
        self.local.milestonesFSM.set_enabled(False)

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
        self.local.tacetFieldSolisiaLandingFSM.set_enabled(cfg.tacetFieldSolisiaLanding)
        self.local.tacetFieldFrostlandsTransitPortFSM.set_enabled(cfg.tacetFieldFrostlandsTransitPort)
        self.local.tacetFieldMountGjallarFSM.set_enabled(cfg.tacetFieldMountGjallar)
        self.local.tacetFieldMawburrowDesertFSM.set_enabled(cfg.tacetFieldMawburrowDesert)
        self.local.tacetFieldStagnantRunFSM.set_enabled(cfg.tacetFieldStagnantRun)

        ### ------- Guidebook MaterialsSpots WeeklyChallenge -------
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

        self.engine.source(NodeName.doActivity).always().to(NodeName.globalDispatcher)

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
