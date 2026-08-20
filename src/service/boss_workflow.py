import logging
import random
import re
import time
from typing import Optional

from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import ResonatorNameEnum, Morph, BaseResonator
from src.core.combat.combat_system import CombatSystem
from src.core.enemy import Enemy
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, Point
from src.core.i18n import I18nText, Language, I18nTr
from src.core.message import MsgType, MsgTaskStatus, MsgSource
from src.core.movement import Run, Walk, RouteExecutor
from src.core.pages import UIOp, GlobalPage
from src.core.resonator import Resonator
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import (
    absorb_around_variant_blind, bbox_terminal_content, bbox_guidebook_content, move_and_scan_dialogue,
    match_remaining_attempts, linear_spacing, query_waveplate_guidebook, query_waveplate_claim_rewards,
    object_detection, bbox_hp_bar, bbox_guidebook_item, search_icon_guidebook, bbox_dialogue,
    bbox_guidebook_title, AsyncPickup,
)
from src.util import img_util, file_util
from src.util.img_sift_util import SIFTFeatureMatcher
from src.util.img_tile_util import TileGrid

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        self.teamFSM: TaskFSM = TaskFSM(name=I18nText.Team)

        self.rootFSM: TaskFSMGroup = TaskFSMGroup(
            self.teamFSM,
            name="Root"
        )

        # runtime
        self.downed = False


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

    # doMaterialCollection
    doForgeryChallenge = "doForgeryChallenge"
    doSimulationChallenge = "doSimulationChallenge"
    doBossChallenge = "doBossChallenge"
    doTacetSuppression = "doTacetSuppression"
    doWeeklyChallenge = "doWeeklyChallenge"
    doNightmarePurification = "doNightmarePurification"
    doTacetDiscordNest = "doTacetDiscordNest"

    doCombat = "doCombat"


@node(NodeName.endNode)
def endNode(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.rootFSM.is_finished:
        ctx.runtime.taskFSM.complete()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
        ctx.ipc.event_queue.put({
            "task": {"AutoBossProcessTask": "finished"}
        }, block=True)
    else:
        ctx.runtime.taskFSM.fail()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.FAILED)
        ctx.ipc.event_queue.put({
            "task": {"AutoBossProcessTask": "failed"}
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
    if local.downed:
        return I18nText.ResonatorDowned
    return I18nText.Guidebook


@node(NodeName.doTravelToResonanceNexus)
def doTravelToResonanceNexus(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    """去往信标，用于复活队友、脱战等"""
    ui = UIOp(ctx)
    ui.snapshot()

    # 防止失败卡流程，重置状态，少人也能打
    local.downed = False

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
    ui = UIOp(ctx)

    # 终端
    if not GlobalPage(ctx).isTerminal(ui=ui.snapshot()):
        return None
    # 点击进入索拉指南
    if not ui.click_text(ctx.tr(I18nText.Guidebook), bbox_terminal_content(ctx),
                         pk=PointKind.NEAR, delay=0.2, times=2, interval=0.2):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    # 进入索拉指南后，默认是 活跃度 或 素材获取页
    activity = ctx.tr(I18nText.Activity)
    materialCollection = ctx.tr(I18nText.MaterialCollection)
    recurringChallenges = ctx.tr(I18nText.RecurringChallenges)
    pathOfGrowth = ctx.tr(I18nText.PathOfGrowth)
    enemyTracing = ctx.tr(I18nText.EnemyTracing)
    milestones = ctx.tr(I18nText.Milestones)

    titles = [activity, materialCollection, recurringChallenges, pathOfGrowth, enemyTracing, milestones]
    title_roi = bbox_guidebook_title(ctx)

    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(titles, title_roi)):
        logger.warning(f"Page not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    enemy_key = ctx.runtime.cfg.bossRush.bossName[0]
    enemy_name = ctx.tr(enemy_key)
    enemy = Enemy.NightmareMourningAix

    # 根据敌人属性选择刷取入口
    ui.sleep(0.2)
    if enemy.prefer_quick:
        # 素材获取
        if not ui.search(materialCollection, title_roi):
            for i in range(2):
                icon_point = search_icon_guidebook(ctx, material_collection=True)
                if not icon_point:
                    if i == 0:
                        continue
                    else:
                        logger.warning(f"materialCollection icon not found")
                        return None
                ui.click_point(icon_point, times=2, interval=0.3)
                if ui.sleep(0.2).wait(2, 0.3).until(lambda: ui.snapshot().search(materialCollection, title_roi)):
                    ui.sleep(0.3)
                    break

        return I18nText.MaterialCollection

    for i in range(2):
        icon_point = search_icon_guidebook(ctx, enemy_tracing=True)
        if not icon_point:
            if i == 0:
                continue
            else:
                logger.warning(f"enemyTracing icon not found")
                return None
        ui.click_point(icon_point, times=2, interval=0.3)
        roi_item = bbox_guidebook_item(ctx)
        if ui.sleep(0.2).wait(2, 0.3).until(
                lambda: ui.snapshot()
                        and ui.search(enemyTracing, title_roi)
                        and ui.search(ctx.tr(I18nText.EnemyTracingSearch), roi_item)):
            ui.sleep(0.3)
            break

    return I18nText.EnemyTracing


@node(NodeName.doEnemyTracing)
def doEnemyTracing(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    # 检查是否在敌迹探寻，双击搜索
    if not ui.search(ctx.tr(I18nText.EnemyTracing)) and not ui.click_text(
            ctx.tr(I18nText.EnemyTracingSearch), bbox_guidebook_item(ctx), delay=0.3, times=2, interval=0.2):
        return False

    enemy_key = ctx.runtime.cfg.bossRush.bossName[0]
    enemy_name = ctx.tr(enemy_key)
    enemy = Enemy.NightmareMourningAix
    # TODO 提示抗性
    logger.info(f"Enemy: {enemy_name}")

    # 输入敌人名称
    ui.sleep(0.3)
    ctx.control_service.input_text(enemy_name)
    ui.sleep(0.5)
    ctx.control_service.enter()
    ui.sleep(0.8)

    # 点击敌人，点击探测
    if ui.snapshot().search(ctx.tr(I18nText.NoDetectableResult)):
        logger.warning(f"{ctx.tr(I18nText.DetectionTargetNotFound).raw}")
        return False
    roi_enemy = AnchorBBox(
        AnchorPoint(0, 115, Align.Left | Align.Top),
        AnchorPoint(454, 720, Align.Left | Align.Bottom)
    )
    if not ui.click_text(enemy_name, roi_enemy, times=2, interval=0.2) and not ui.click_text(
            ctx.tr(I18nText.Detect), delay=0.35, times=2, interval=0.3):
        logger.warning(f"Text not found: {enemy_name.raw}")
        return False

    def _wait_fast_travel():
        ui.snapshot()
        if ui.search(ctx.tr(I18nText.DetectionTargetNotFound)):
            return True
        if ui.click_text(ctx.tr(I18nText.FastTravel), pk=PointKind.RANDOM, delay=0.3, times=2, interval=0.3):
            return True
        return False

    # 点击快速旅行
    if not ui.sleep(0.8).wait().until(_wait_fast_travel):
        logger.warning(f"Text not found: {ctx.tr(I18nText.FastTravel).raw}")
        return False
    if ui.search(ctx.tr(I18nText.DetectionTargetNotFound)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.DetectionTargetNotFound).raw}")
        return False

    ui.wait_back_home(close_window=True)
    ui.sleep(0.5)
    return True


@node(NodeName.doCombat)
def doCombat(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    if not ui.is_on_homepage():
        return False

    enemy_key = ctx.runtime.cfg.bossRush.bossName[0]
    enemy_name = ctx.tr(enemy_key)
    enemy = Enemy.NightmareMourningAix
    # TODO 提示抗性
    logger.info(f"Enemy: {enemy_name}")
    downed = False

    while ui.is_set():
        combat_system = CombatSystem(ctx.control_service, ctx.img_service)
        combat_system.set_resonators(ctx.shared.team_members, is_print=False)
        combat_system.is_async = True
        combat_system.check_boss_hp = True
        combat_system.auto_pickup = True
        combat_system.exit_special_state(Morph.Forced)

        # 跑向boss或副本
        executor = RouteExecutor(ctx)
        executor.execute(enemy.boss_meta.routes)

        timeout = 10 * 60
        no_text_count = 3
        no_text_max = no_text_count
        deadline = time.monotonic() + timeout
        hp_roi = bbox_hp_bar(ctx).as_tuple()

        index = 1
        logger.info(f"[Round{index}] - Combat engaged!")

        while ui.is_set():
            if time.monotonic() < deadline or no_text_count < 0:
                logger.info(f"[Round{index}] - Out of combat")
                break

            combat_system.start(3.5)
            ui.sleep(1.5).snapshot()

            if ui.is_on_homepage():
                # 挑战成功
                if ui.search(ctx.tr([I18nText.ForgeryChallengeComplete, I18nText.TacetFieldChallengeComplete])):
                    logger.info(f"[Round{index}] - Combat ended!")
                    break
                # 击败
                battle_text = ctx.tr(enemy.battle_text)
                if ui.search(battle_text):
                    logger.info(f"[Round{index}] - In combat")
                    no_text_count = no_text_max
                    continue
                no_text_count -= 1
                logger.debug(f"[Round{index}] - Text not found: {battle_text.raw}")

            if page_key := GlobalPage(ctx).action(ui=ui):
                if page_key == GlobalPage.InternetDisconnecting:
                    combat_system.stop(join=True)
                    return False

        combat_system.stop(join=True)
        ui.sleep(0.5)

        # 等待回到主页
        back_homepage = False
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            img = ui.grap()
            if ui.is_on_homepage(img=img):
                back_homepage = True
                break
            GlobalPage(ctx).action(ui=ui.snapshot(img=img))
            ui.sleep(0.3)
        if not back_homepage:
            return False

        # 检查阵亡情况
        downed = False
        if downed:
            logger.info(f"[Round{index}] - Resonator downed")
            local.downed = downed

        # 退出特殊状态
        combat_system.exit_special_state(Morph.Prefer)

        # 搜索声骸
        if object_detection(ctx, search_echo=True, timeout=20):
            logger.info(f"[Round{index}] - Absorbed")
        else:
            logger.info(f"[Round{index}] - Not absorbed")

        # 准备进入下一轮，副本内
        if enemy.is_dungeon:
            page = GlobalPage(ctx)
            if not ui.sleep(0.2).esc().sleep(0.3).wait().until(
                    lambda: ui.snapshot()
                            and (ui.search(ctx.tr(I18nText.WeeklyRestart)) and ui.search(ctx.tr(I18nText.WeeklyExit)))
                            or page.isTerminal(ui=ui)):
                return False

            # 兼容大世界
            if page.isTerminal(ui=ui):
                break

            # 退出副本，复活
            if downed:
                logger.info(f"[Round{index}] - Exit to Nexus")
                ui.click_text(ctx.tr(I18nText.WeeklyExit), delay=0.3, times=2, interval=0.3)
                ui.sleep(1).wait_back_home()
                ui.sleep(0.5)
                return False

            logger.info(f"[Round{index}] - {ctx.tr(I18nText.WeeklyRestart).raw}")
            ui.click_text(ctx.tr(I18nText.WeeklyRestart), delay=0.3, times=2, interval=0.3)
            ui.sleep(1).wait_back_home()
            ui.sleep(0.5)

            index += 1
            continue

        # 大世界
        break

    return False


@node(NodeName.doMaterialCollection)
def doMaterialCollection(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
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


@node(NodeName.doSimulationChallenge)
def doSimulationChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


@node(NodeName.doBossChallenge)
def doBossChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    raise NotImplementedError


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


class BossWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name=self.__class__.__name__)
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
        cfg = self.ctx.runtime.cfg.bossRush
        logger.debug(f"cfg: {cfg}")

        self.local.rootFSM.set_enabled(True)
        self.local.teamFSM.set_enabled(True)

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
            .on(I18nText.ResonatorDowned).to(NodeName.doTravelToResonanceNexus)
            .on(I18nText.Guidebook).to(NodeName.doGuidebook)
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
            .on(I18nText.MaterialCollection).to(NodeName.doMaterialCollection)
            .on(I18nText.EnemyTracing).to(NodeName.doEnemyTracing)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doEnemyTracing)
            .on(True).to(NodeName.doCombat)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.source(NodeName.doCombat).always().to(NodeName.globalDispatcher)

        # self.engine.source(NodeName.doBossChallenge).always().to(NodeName.globalDispatcher)
        # self.engine.source(NodeName.doWeeklyChallenge).always().to(NodeName.globalDispatcher)

        self.engine.exception(NodeName.endNode)
